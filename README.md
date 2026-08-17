# telechan-watcher

Watch Telegram channels using your own account — no bot required — and browse
the collected messages in a small web UI.

Built on [Telethon](https://docs.telethon.dev) (MTProto client library), so it
logs in as your Telegram user account and listens for new messages on any
broadcast channel you're a member of.

## How it works

- **`watch.py`** — connects with your Telegram account and listens for new
  messages on every broadcast channel you belong to. Each message is stored
  in a local SQLite database (`telechan.db`).
- **`app.py`** — a small Flask app that reads the same database and serves a
  web UI: a channel list and a per-channel message view.
- Each channel gets a **label** (defaults to its Telegram title, editable in
  the UI) and can be **paused** — while paused, new messages from that
  channel are received but not recorded.

## Setup

1. Get API credentials from https://my.telegram.org/apps
2. Copy the env template and fill in your credentials:
   ```
   cp .env.example .env
   ```
3. Install dependencies:
   ```
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. Run the watcher once locally to complete the interactive login (phone
   number + login code):
   ```
   python watch.py
   ```
   This creates `telechan.session`, which lets future runs (including in
   Docker) reconnect without logging in again.

## Running

### Locally

```
source venv/bin/activate
python watch.py    # collector — leave running
python app.py       # web viewer, http://localhost:5000
```

### With Docker Compose

Once `telechan.session` exists (see Setup step 4), both processes can run in
containers, sharing the same SQLite database and session file via a bind
mount:

```
docker compose up -d
```

- `watcher` — runs `watch.py`
- `web` — runs `app.py`, published on `http://localhost:5000`

## Backfilling old data

Earlier versions of this project wrote messages to per-channel Markdown files
under `messages/`. `backfill.py` is a one-off script that imports those files
into the SQLite database, resolving each channel to its real Telegram chat ID
via your existing session:

```
python backfill.py
```

## Notes

- This uses your personal Telegram account, not a bot — it can only see
  channels you're already a member of, and is subject to Telegram's normal
  rate limits for user accounts.
- `telechan.session` is equivalent to being logged into your account; keep it
  private (it's gitignored).
- Timestamps are stored in UTC and displayed in UTC+7 (WIB).
