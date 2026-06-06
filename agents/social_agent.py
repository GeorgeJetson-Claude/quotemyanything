#!/usr/bin/env python3
"""
QMA Social Agent
Monitors Reddit for high-intent posts and replies with QuoteMyAnything.com
Covers: home services, collectibles, vehicles, antiques, valuables
"""

import praw
import time
import random
import logging
import os
from groq import Groq

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("qma-agent")

# --- CONFIG ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USERNAME = os.environ.get("REDDIT_USERNAME", "")
REDDIT_PASSWORD = os.environ.get("REDDIT_PASSWORD", "")

QMA_URL = "quotemyanything.com"

# Subreddits + intent keywords per vertical
TARGETS = {
    "home_services": {
        "subs": ["Austin", "HomeImprovement", "homeowners", "HVAC", "Roofing", "Plumbing", "lawncare", "electricians", "pestcontrol", "moving"],
        "keywords": ["need a quote", "looking for a contractor", "how much does", "recommend a", "anyone know a good", "HVAC quote", "roof quote", "plumber quote", "lawn care quote", "moving company", "need someone to", "get quotes", "cheapest", "best price"],
    },
    "collectibles": {
        "subs": ["whatsthisworth", "Antiques", "Coins", "Flipping", "vintage", "Funko", "Ebay", "ThriftStoreHauls", "Whatisit"],
        "keywords": ["what is this worth", "how much is this", "where can i sell", "best offer", "anyone want to buy", "appraisal", "value of", "sell my collection", "how do i sell"],
    },
    "vehicles": {
        "subs": ["carbuyingadvice", "UsedCars", "askcarsales", "AutoDetailing", "motorcycles"],
        "keywords": ["get quotes", "best price on", "how much should i pay", "dealer quotes", "looking to sell my car", "what is my car worth"],
    },
}

# Groq content generation
def generate_reply(post_title: str, post_body: str, vertical: str) -> str:
    client = Groq(api_key=GROQ_API_KEY)

    context = {
        "home_services": "home services (roofing, HVAC, plumbing, lawn care, moving, cleaning, electrical, pest control)",
        "collectibles": "collectibles, antiques, and valuables (get competing offers from dealers and buyers)",
        "vehicles": "vehicles (get competing quotes from dealers and private buyers)",
    }

    prompt = f"""You are a helpful Reddit user. Someone posted asking about {context[vertical]}.

Post title: {post_title}
Post body: {post_body[:300]}

Write a SHORT, natural, helpful Reddit reply (2-3 sentences max) that:
- Actually helps them with their question first
- Mentions quotemyanything.com as a free tool to get competing quotes/offers
- Sounds human, not spammy
- Does NOT start with "I" or sound like an ad
- Uses casual Reddit tone

Reply only with the comment text, nothing else."""

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.8,
    )
    return response.choices[0].message.content.strip()


def is_relevant(post, keywords: list) -> bool:
    text = (post.title + " " + (post.selftext or "")).lower()
    return any(kw.lower() in text for kw in keywords)


def run_agent(dry_run: bool = True):
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        username=REDDIT_USERNAME,
        password=REDDIT_PASSWORD,
        user_agent="QMAAgent/1.0 by " + REDDIT_USERNAME,
    )

    replied = set()
    total_replies = 0
    MAX_REPLIES_PER_RUN = 5  # stay under Reddit rate limits

    for vertical, config in TARGETS.items():
        if total_replies >= MAX_REPLIES_PER_RUN:
            break

        sub_name = "+".join(config["subs"])
        log.info(f"Scanning r/{sub_name} for {vertical}...")

        try:
            subreddit = reddit.subreddit(sub_name)
            for post in subreddit.new(limit=50):
                if total_replies >= MAX_REPLIES_PER_RUN:
                    break
                if post.id in replied:
                    continue
                if post.score < -5:  # skip heavily downvoted
                    continue
                if not is_relevant(post, config["keywords"]):
                    continue
                # Skip if post is too old (>48 hours)
                if (time.time() - post.created_utc) > 172800:
                    continue

                try:
                    reply_text = generate_reply(post.title, post.selftext or "", vertical)
                    log.info(f"[{vertical}] r/{post.subreddit} | {post.title[:60]}")
                    log.info(f"Reply: {reply_text[:120]}...")

                    if not dry_run:
                        post.reply(reply_text)
                        log.info("✅ Posted reply")
                        time.sleep(random.uniform(30, 60))  # rate limit safety
                    else:
                        log.info("🔵 DRY RUN — not posting")

                    replied.add(post.id)
                    total_replies += 1

                except Exception as e:
                    log.warning(f"Reply failed: {e}")
                    time.sleep(10)

        except Exception as e:
            log.warning(f"Subreddit scan failed for {vertical}: {e}")

    log.info(f"Agent run complete. {total_replies} replies {'drafted' if dry_run else 'posted'}.")


if __name__ == "__main__":
    import sys
    dry = "--live" not in sys.argv
    if dry:
        log.info("Running in DRY RUN mode. Pass --live to actually post.")
    run_agent(dry_run=dry)
