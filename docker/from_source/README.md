# TelQbot — Docker deployment

**Always run Docker commands from this folder:**

```
/root/TelQbot/docker/from_source/
```

Do **not** run from other `docker/` subfolders — those use different layouts.

## First-time setup

### 1. Go to the correct folder

From the project root:

```bash
cd docker/from_source
```

Or with a full path:

```bash
cd /path/to/TelQbot/docker/from_source
```

### 2. Create your config file

The bot loads config from **`qbittorrent-bot-data/config.yml`** only. That folder is mounted into the container as `/app/data`.

A template is included:

```bash
cp qbittorrent-bot-data/config.example.yml qbittorrent-bot-data/config.yml
```

Edit `qbittorrent-bot-data/config.yml` and set at minimum:

- `telegram.bot_token` — from [@BotFather](https://t.me/BotFather)
- `client.host`, `client.user`, `client.password` — qBittorrent Web UI (use `https://172.17.0.1:443/` if qBittorrent runs on the host and the bot is in Docker)
- `redis.url` — must be `redis://cache:6379/0` (service name from `docker-compose.yml`, **not** `localhost`)
- `users` — your Telegram numeric user ID and role
- `content_categories` / `stremio` — optional but needed for Stremio folder routing and library refresh

> **Only one config location:** `qbittorrent-bot-data/config.yml`. There are no other `config.yml` files in this project.

### 3. Build and start

Still inside `docker/from_source/`:

```bash
docker compose up -d --build
```

This starts:

| Container       | Role                          |
|----------------|-------------------------------|
| `qbittorrent-bot` | TelQbot (Telegram bot)     |
| `redis-cache`     | Redis for bot state        |

### 4. Check that it is running

```bash
docker compose ps
docker compose logs -f bot
```

In Telegram, send `/start` to your bot (only users listed in `config.yml` get a reply).

## Day-to-day commands

Run these from `docker/from_source/`:

```bash
# Restart after config change (hot reload also works, but restart is safest)
docker compose restart bot

# Rebuild after code changes
docker compose up -d --build

# Stop everything
docker compose down

# View logs
docker compose logs -f bot
```

## Folder layout (this directory)

```
docker/from_source/
├── docker-compose.yml              ← run docker compose here
├── README.md                       ← this file
└── qbittorrent-bot-data/
    ├── config.example.yml          ← template (copy to config.yml)
    ├── config.yml                  ← your live config (edit this)
    └── logs/                       ← bot log files
```

## qBittorrent on the host

If qBittorrent runs on the same machine (not in this compose stack), the bot container reaches it via the Docker bridge IP `172.17.0.1`. The compose file already sets:

- `QBITTORRENTAPI_DO_NOT_VERIFY_WEBUI_CERTIFICATE=1` — for self-signed HTTPS certs
- `extra_hosts: host.docker.internal:host-gateway` — optional host access

Adjust `client.host` in `config.yml` if your Web UI uses a different port or URL.
