#!/usr/bin/env python3
"""
5LUV YouTube Publisher
Auto-publishes ORIGINAL 5LUV content (music, remixes, late-night long-form, Shorts)
to YouTube on a schedule via the official YouTube Data API v3.

This is the legitimate version of "auto-posting": you make the content, drop the
finished files in a queue, and this drip-publishes them so the channel stays active
24/7 without you babysitting uploads.

IMPORTANT — only use this for content you OWN or are licensed to publish.
Reposting other creators' videos = copyright strikes + channel termination + you
don't get the money anyway (Content ID routes revenue to the rights holder).

Setup: see agents/YOUTUBE_SETUP.md
"""

import os
import sys
import json
import time
import random
import logging
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("5luv-publisher")

# --- CONFIG ---
HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE_PATH = os.environ.get("YT_QUEUE_PATH", os.path.join(HERE, "youtube_queue.json"))
CLIENT_SECRETS = os.environ.get("YT_CLIENT_SECRETS", os.path.join(HERE, "yt_client_secret.json"))
TOKEN_PATH = os.environ.get("YT_TOKEN_PATH", os.path.join(HERE, "yt_token.json"))
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# How many videos to release per run, and how far apart to space scheduled drops.
MAX_PUBLISH_PER_RUN = int(os.environ.get("YT_MAX_PER_RUN", "3"))
DRIP_HOURS = float(os.environ.get("YT_DRIP_HOURS", "8"))  # space scheduled releases

YOUTUBE_UPLOAD_SCOPE = ["https://www.googleapis.com/auth/youtube.upload"]
CHANNEL_NAME = "5LUV"


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------
def get_service():
    """Authenticate and return a YouTube Data API v3 client.

    First run opens a browser for OAuth consent and caches the token to
    YT_TOKEN_PATH so subsequent runs are fully unattended.
    """
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, YOUTUBE_UPLOAD_SCOPE)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS):
                raise FileNotFoundError(
                    f"Missing OAuth client secrets at {CLIENT_SECRETS}. "
                    "See agents/YOUTUBE_SETUP.md to create one."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, YOUTUBE_UPLOAD_SCOPE)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
        log.info("Saved OAuth token to %s", TOKEN_PATH)

    return build("youtube", "v3", credentials=creds)


# --------------------------------------------------------------------------
# Metadata generation (optional, for YOUR content)
# --------------------------------------------------------------------------
def generate_metadata(item: dict) -> dict:
    """Auto-write title/description/tags for an original 5LUV track using Groq.

    Falls back to whatever is already in the queue item if Groq isn't configured.
    """
    title = item.get("title")
    description = item.get("description")
    tags = item.get("tags")

    if title and description and tags:
        return {"title": title, "description": description, "tags": tags}

    if not GROQ_API_KEY:
        return {
            "title": title or os.path.splitext(os.path.basename(item["file"]))[0],
            "description": description or "New from 5LUV.",
            "tags": tags or ["5LUV", "music", "remix"],
        }

    from groq import Groq

    client = Groq(api_key=GROQ_API_KEY)
    hint = item.get("hint", "")
    kind = item.get("kind", "music video")
    prompt = f"""You write YouTube metadata for the music channel "{CHANNEL_NAME}".
This is an ORIGINAL {kind} the channel produced.
Creator notes: {hint}
Working title (if any): {title or 'none'}

Return STRICT JSON with keys: title, description, tags.
- title: catchy, <=70 chars, no clickbait lies, include "5LUV" naturally if it fits
- description: 2-3 short paragraphs, include a line "Original content by 5LUV." and a spot for links
- tags: array of 10-15 relevant search tags (lowercase strings)
Return ONLY the JSON object."""

    resp = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.8,
    )
    raw = resp.choices[0].message.content.strip()
    # be tolerant of code fences
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("Groq returned non-JSON metadata; using fallbacks.")
        return {
            "title": title or os.path.splitext(os.path.basename(item["file"]))[0],
            "description": description or "Original content by 5LUV.",
            "tags": tags or ["5luv", "music", "remix"],
        }
    return {
        "title": title or data.get("title"),
        "description": description or data.get("description"),
        "tags": tags or data.get("tags", []),
    }


# --------------------------------------------------------------------------
# Queue
# --------------------------------------------------------------------------
def load_queue() -> list:
    if not os.path.exists(QUEUE_PATH):
        log.error("No queue at %s. Create one (see youtube_queue.example.json).", QUEUE_PATH)
        return []
    with open(QUEUE_PATH) as f:
        return json.load(f)


def save_queue(items: list):
    with open(QUEUE_PATH, "w") as f:
        json.dump(items, f, indent=2)


# --------------------------------------------------------------------------
# Upload
# --------------------------------------------------------------------------
def upload(service, item: dict, meta: dict, publish_at: str | None):
    from googleapiclient.http import MediaFileUpload

    status = {
        "privacyStatus": "private" if publish_at else item.get("privacy", "public"),
        "selfDeclaredMadeForKids": False,
    }
    if publish_at:
        # Scheduled: must be private + publishAt (RFC3339 UTC "Z")
        status["publishAt"] = publish_at

    body = {
        "snippet": {
            "title": meta["title"][:100],
            "description": meta["description"][:5000],
            "tags": meta["tags"][:30],
            "categoryId": item.get("category_id", "10"),  # 10 = Music
        },
        "status": status,
    }

    media = MediaFileUpload(item["file"], chunksize=-1, resumable=True)
    request = service.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        progress, response = request.next_chunk()
        if progress:
            log.info("  uploading... %d%%", int(progress.progress() * 100))
    return response["id"]


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def run(dry_run: bool = True):
    items = load_queue()
    pending = [it for it in items if not it.get("published") and it.get("file")]
    if not pending:
        log.info("Queue empty — nothing pending. Add original 5LUV videos to %s", QUEUE_PATH)
        return

    log.info("%d pending. Releasing up to %d this run (dry_run=%s).",
             len(pending), MAX_PUBLISH_PER_RUN, dry_run)

    service = None if dry_run else get_service()
    slot = datetime.now(timezone.utc)
    released = 0

    for item in pending:
        if released >= MAX_PUBLISH_PER_RUN:
            break

        if not os.path.exists(item["file"]) and not dry_run:
            log.warning("Skipping — file not found: %s", item["file"])
            continue

        meta = generate_metadata(item)

        # Schedule drops if requested; otherwise publish immediately.
        publish_at = None
        if item.get("schedule", True) and DRIP_HOURS > 0 and released > 0:
            slot = slot + timedelta(hours=DRIP_HOURS)
            publish_at = slot.strftime("%Y-%m-%dT%H:%M:%SZ")
        elif item.get("publish_at"):
            publish_at = item["publish_at"]

        log.info("[%s] %s", "SCHEDULED " + publish_at if publish_at else "PUBLISH NOW", meta["title"])
        log.info("  tags: %s", ", ".join(meta["tags"][:8]))

        if dry_run:
            log.info("  🔵 DRY RUN — not uploading")
            released += 1
            continue

        try:
            vid = upload(service, item, meta, publish_at)
            url = f"https://youtu.be/{vid}"
            log.info("  ✅ uploaded: %s", url)
            item["published"] = True
            item["video_id"] = vid
            item["url"] = url
            item["published_meta"] = meta
            save_queue(items)
            released += 1
            time.sleep(random.uniform(5, 15))  # be gentle on quota
        except Exception as e:
            log.warning("  upload failed: %s", e)
            time.sleep(10)

    log.info("Run complete. %d video(s) %s.", released, "drafted" if dry_run else "released")


if __name__ == "__main__":
    dry = "--live" not in sys.argv
    if dry:
        log.info("DRY RUN mode. Pass --live to actually upload to YouTube.")
    run(dry_run=dry)
