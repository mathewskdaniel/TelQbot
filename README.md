# TelQbot

TelQbot is a private Telegram bot for controlling **qBittorrent** from your phone. It is built for a Stremio + debrid workflow: add torrents into the right library folders, manage downloads, and refresh the Stremio catalog without opening the Web UI.

Unauthorized Telegram users get **no response at all** — the bot silently ignores them.

## Run with Docker (recommended)

**Full step-by-step instructions:** [`docker/from_source/README.md`](docker/from_source/README.md)

Short version — use **this exact folder** and **this exact config path**:

```bash
cd docker/from_source

# First time only: copy the template and edit it
cp qbittorrent-bot-data/config.example.yml qbittorrent-bot-data/config.yml
# edit qbittorrent-bot-data/config.yml

docker compose up -d --build
```

| What | Where |
|------|--------|
| Run `docker compose` from | `docker/from_source/` |
| Config file the bot actually uses | `docker/from_source/qbittorrent-bot-data/config.yml` |
| Config template (example) | `docker/from_source/qbittorrent-bot-data/config.example.yml` |

Each deployment mode has its **own** config path — see the non-Docker section below if you are not using Docker.

## Run without Docker

Run everything from the **project root** (the folder that contains `src/`, `pyproject.toml`, and `data/`):

```bash
cd /path/to/TelQbot
```

### 1. Prerequisites

- Python **3.13+**
- [uv](https://docs.astral.sh/uv/) (recommended) or another way to install from `pyproject.toml`
- **Redis** running locally (required)
- **qBittorrent** with Web UI enabled

Start Redis if it is not already running:

```bash
# example: Redis via Docker while the bot runs on the host
docker run -d --name redis -p 6379:6379 redis:8
```

### 2. Install dependencies

From the project root:

```bash
uv sync
uv run pybabel compile -d src/locales -D messages
```

### 3. Create your config

| What | Where |
|------|--------|
| Run the bot from | project root (`TelQbot/`) |
| Config file the bot uses | `data/config.yml` |
| Config template | `data/config.example.yml` |

```bash
cp data/config.example.yml data/config.yml
# edit data/config.yml
```

Use `redis://localhost:6379/0` for Redis (not `redis://cache:...` — that name is Docker-only).

### 4. Start the bot

Still from the project root:

```bash
uv run python -m src.main
```

For qBittorrent with a self-signed HTTPS certificate:

```bash
QBITTORRENTAPI_DO_NOT_VERIFY_WEBUI_CERTIFICATE=1 uv run python -m src.main
```

The bot watches `data/config.yml` for changes and reloads automatically.

## Features

### Torrent management
- **Stats** — server CPU, RAM, disk, and uptime (`/stats` or menu button)
- **Lists** — Downloading, Completed, Paused, and All torrents from the main menu
- **Add torrents** — magnet links or `.torrent` files with a category picker
- **Pause / resume** — single torrents or all at once
- **Delete** — with or without removing files
- **Torrent details** — progress, category, export `.torrent`, refresh

### Stremio content folders
- **Movie torrent** → `StremioMovies` → `.../media/movies`
- **TV series torrent** → `StremioSeries` → `.../media/series`
- Paste a magnet or send a `.torrent` file directly — the bot asks where it should go
- **Settings → Content Folders** — view and change save paths (synced to qBittorrent)
- Downloads use both the qBittorrent category **and** the configured save path

### Stremio library admin (administrator only)
- **Scan Library** — incremental scan of movies and series
- **Full Rebuild** — clears the Stremio DB and rescans (with confirmation)
- **Update Admin Token** — change the Stremio admin API token from Telegram

### Access control
- **Administrator** — full access including settings, delete, Stremio admin, categories
- **Manager** — add torrents, pause/resume, content categories
- **Reader** — view lists and stats only
- Users not listed in `config.yml` receive zero replies

### Other
- Redis-backed session state and completion notifications (no duplicate “torrent finished” spam)
- Hot reload when `config.yml` changes
- HTTPS qBittorrent Web UI support (self-signed certs via env var)
- Multi-language UI (English source strings; legacy translations may still show older labels)

## Bot commands

| Command   | Description        |
|-----------|--------------------|
| `/start`  | Open the main menu |
| `/stats`  | Server statistics  |

## Project layout

```
TelQbot/
├── src/                              # Bot source code
├── data/                             # Non-Docker config (run bot from project root)
│   ├── config.example.yml            # Template to copy → config.yml
│   └── config.yml                    # Your live config (local only, not in git)
├── docker/from_source/               # Docker deployment — run compose from here
│   ├── README.md                     # Detailed Docker guide
│   ├── docker-compose.yml
│   └── qbittorrent-bot-data/
│       ├── config.example.yml        # Template to copy → config.yml
│       └── config.yml                # Your live config (local only, not in git)
└── README.md
```

### Which config goes where?

| How you run TelQbot | Folder you run commands from | Config file |
|---------------------|------------------------------|-------------|
| **Docker** (recommended) | `docker/from_source/` | `qbittorrent-bot-data/config.yml` |
| **Direct / non-Docker** | project root (`TelQbot/`) | `data/config.yml` |

## Credits

Based on the work of [ch3p4ll3/QBittorrentBot](https://github.com/ch3p4ll3/QBittorrentBot).
