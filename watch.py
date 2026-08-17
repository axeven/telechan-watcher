import os
from datetime import datetime, timedelta, timezone

DISPLAY_TZ = timezone(timedelta(hours=7))

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.types import Channel

import db

load_dotenv()

API_ID = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]

client = TelegramClient("telechan", API_ID, API_HASH)


@client.on(events.NewMessage)
async def handler(event):
    chat = await event.get_chat()

    # only broadcast channels, skip groups/DMs (megagroups have broadcast=False)
    if not (isinstance(chat, Channel) and chat.broadcast):
        return

    sender = await event.get_sender()
    sender_name = getattr(sender, "username", None) or getattr(sender, "title", None) or "unknown"

    now = datetime.now(timezone.utc)

    conn = db.get_connection()
    db.upsert_channel(conn, chat.id, getattr(chat, "username", None), chat.title)

    if db.is_paused(conn, chat.id):
        conn.close()
        return

    db.insert_message(conn, chat.id, sender_name, event.raw_text, now.isoformat())
    conn.close()

    local = now.astimezone(DISPLAY_TZ)
    print(f"[{chat.title}] {local:%H:%M:%S} WIB {sender_name}: {event.raw_text}")


def main():
    db.init_db()
    print("Watching all channels... (Ctrl+C to stop)")
    client.start()
    client.run_until_disconnected()


if __name__ == "__main__":
    main()
