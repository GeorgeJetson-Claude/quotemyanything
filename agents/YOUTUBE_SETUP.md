# 5LUV YouTube Publisher — Setup

Auto-publishes **original** 5LUV content (music, remixes, late-night long-form, Shorts)
to YouTube on a schedule. You make the content; this drips it out so the channel stays
active without you manually uploading.

## ⚠️ Use only for content you own

This tool uploads files **you** provide. Do **not** feed it other creators' YouTube
Shorts or unlicensed music. Reposting/remixing copyrighted content gets caught by
Content ID, sends the ad money to the rights holder (not you), and stacks copyright
strikes — 3 strikes terminates the channel. The whole point of this script is to grow
5LUV *safely* with your own catalog.

## 1. Install dependencies

```bash
cd agents
pip install -r requirements.txt
```

## 2. Get YouTube API credentials (one time, ~5 min)

1. Go to https://console.cloud.google.com/ and create a project (e.g. "5LUV").
2. APIs & Services → Library → enable **YouTube Data API v3**.
3. APIs & Services → OAuth consent screen → External → add your Google account as a
   **Test user** (the account that owns the 5LUV channel).
4. APIs & Services → Credentials → Create Credentials → **OAuth client ID** →
   Application type **Desktop app**.
5. Download the JSON, save it as `agents/yt_client_secret.json`.

## 3. Configure

```bash
cp .env.example .env
# edit .env: set GROQ_API_KEY (optional, for auto titles/tags) and YT_* paths if needed
```

Copy the example queue and fill in your real video files:

```bash
cp youtube_queue.example.json youtube_queue.json
```

Each queue item:

| field         | required | notes |
|---------------|----------|-------|
| `file`        | yes      | absolute path to your video file |
| `kind`        | no       | "Short", "late-night long-form mix", "music video" — helps auto-metadata |
| `title`       | no       | leave blank to auto-generate (needs GROQ_API_KEY) |
| `description` | no       | leave blank to auto-generate |
| `tags`        | no       | leave blank to auto-generate |
| `category_id` | no       | defaults to `10` (Music) |
| `privacy`     | no       | `public` / `unlisted` / `private` (for immediate publish) |
| `schedule`    | no       | `true` drips releases `YT_DRIP_HOURS` apart |
| `publish_at`  | no       | exact RFC3339 UTC time, e.g. `2026-06-20T04:00:00Z` |

## 4. Run

```bash
# Dry run — shows exactly what would publish, uploads nothing
python youtube_publisher.py

# Go live — first run opens a browser once for OAuth, then runs unattended
python youtube_publisher.py --live
```

Published items are marked `"published": true` in the queue with their video URL, so
re-running never double-uploads.

## 5. Make it automatic (cron)

Drip a few videos a day, every day:

```cron
# every day at 2pm UTC, release up to YT_MAX_PER_RUN videos from the queue
0 14 * * * cd /path/to/quotemyanything/agents && /usr/bin/python youtube_publisher.py --live >> yt_publisher.log 2>&1
```

Keep the queue topped up with new 5LUV videos and the channel posts itself.

## Quota note

The YouTube Data API gives ~6 uploads/day on the default quota (uploads cost ~1600
units of a 10k/day budget). For more, request a quota increase in the Cloud Console.
`YT_MAX_PER_RUN=3` keeps you safely under the default.
