import os
import re
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient

import db

load_dotenv()

API_ID = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]

MESSAGES_DIR = Path(__file__).parent / "messages"

BULLET_RE = re.compile(
    r"^- `(?P<time>\d{2}:\d{2}:\d{2})Z` \*\*(?P<sender>.*?)\*\*: (?P<text>.*)$",
    re.MULTILINE,
)


def parse_file(path: Path):
    content = path.read_text(encoding="utf-8")
    matches = list(BULLET_RE.finditer(content))
    entries = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        rest = content[start:end]
        text = (m.group("text") + rest).rstrip("\n")
        entries.append((m.group("time"), m.group("sender"), text))
    return entries


async def resolve_channel(client, channel_key: str, fallback_title: str):
    """Resolve a folder name (username or numeric id) to the real Telegram chat id/title."""
    entity_ref = int(channel_key) if channel_key.lstrip("-").isdigit() else channel_key
    entity = await client.get_entity(entity_ref)
    username = getattr(entity, "username", None)
    title = getattr(entity, "title", None) or fallback_title
    return entity.id, username, title


async def main():
    conn = db.get_connection()
    total = 0

    async with TelegramClient("telechan", API_ID, API_HASH) as client:
        for channel_dir in sorted(MESSAGES_DIR.iterdir()):
            if not channel_dir.is_dir():
                continue

            channel_key = channel_dir.name
            files = sorted(channel_dir.glob("*.md"))
            if not files:
                continue

            fallback_title = channel_key
            for f in files:
                entries = parse_file(f)
                if entries:
                    fallback_title = entries[0][1]
                    break

            try:
                channel_id, username, title = await resolve_channel(client, channel_key, fallback_title)
            except Exception as e:
                print(f"SKIP {channel_key}: could not resolve via Telegram ({e})")
                continue

            db.upsert_channel(conn, channel_id, username, title)

            file_count = 0
            for f in files:
                date_str = f.stem  # YYYY-MM-DD
                for time_str, sender, text in parse_file(f):
                    sent_at = f"{date_str}T{time_str}+00:00"
                    db.insert_message(conn, channel_id, sender, text, sent_at)
                    file_count += 1
                    total += 1

            print(f"{channel_key} -> channel_id={channel_id} title={title!r}: {file_count} messages")

    conn.close()
    print(f"Backfilled {total} messages total.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
