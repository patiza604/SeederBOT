# SeederBot 🤖

Secure FastAPI service for triggering media searches from ChatGPT via webhook, using Jackett → Radarr/Sonarr → Deluge as the primary path, with a robust torrent blackhole fallback.

## ⚠️ Legal Notice

**This software is intended for personal use only with content you are legally permitted to download. Users are responsible for following all applicable laws and tracker rules, including maintaining proper ratios. The authors are not responsible for any misuse of this software.**

## 🏗️ Architecture

```
ChatGPT Action → SeederBot API → [Radarr Mode OR Blackhole Mode] → Deluge
```

### Mode A: Radarr (Primary Path)
```
POST /grab → Radarr API → Jackett (via Radarr) → Deluge
```

### Mode B: Blackhole (Fallback)
```
POST /grab → Jackett API → Download .torrent → Watch Folder → Deluge AutoAdd
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Poetry
- Docker (optional)
- Deluge configured with AutoAdd plugin (for blackhole mode)

### Installation

1. **Clone and setup:**
```bash
git clone https://github.com/patiza604/seederbot.git
cd seederbot
make install
```

2. **Configure environment:**
```bash
make env-example
# Edit .env with your configuration
```

3. **Start development server:**
```bash
make dev
```

## 📋 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_TOKEN` | ✅ | *generated* | Bearer token for API authentication |
| `MODE` | ✅ | `blackhole` | Operation mode: `radarr` or `blackhole` |

#### Radarr Mode (Primary Path)
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RADARR_URL` | ✅ | - | Radarr base URL |
| `RADARR_API_KEY` | ✅ | - | Radarr API key |
| `ROOT_FOLDER` | ✅ | `/movies` | Movies root folder |
| `QUALITY_PROFILE_ID` | ✅ | `4` | Quality profile ID |

#### Blackhole Mode (Fallback)
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JACKETT_URL` | ✅ | - | Jackett base URL |
| `JACKETT_API_KEY` | ✅ | - | Jackett API key |
| `CATEGORIES` | ✅ | `2000,2010` | IPTorrents movie categories |
| `MIN_SEEDERS` | ✅ | `20` | Minimum seeders required |
| `QUALITY_REGEX` | ✅ | `1080p.*WEB-DL\|1080p.*BluRay` | Quality filter regex |
| `EXCLUDE_REGEX` | ✅ | `CAM\|TS\|TC\|WORKPRINT` | Quality exclusions |
| `MIN_SIZE_GB` | ✅ | `2.5` | Minimum file size (GB) |
| `MAX_SIZE_GB` | ✅ | `6.0` | Maximum file size (GB) |
| `AUTOADD_WATCH_DIR` | ✅ | `/data/torrents/watch` | Deluge watch folder |

## 🔧 Setup Guide

### Step 1: Install Jackett on Seedbox
*TODO: Add detailed instructions after Stage 3*

### Step 2: Install Radarr on Seedbox
*TODO: Add detailed instructions after Stage 4*

### Step 3: Configure ChatGPT Action
*TODO: Add detailed instructions after Stage 5*

## 🧪 Testing

```bash
# Run tests
make test

# Run with coverage
poetry run pytest --cov=src

# Lint and format
make lint
make format
```

### Manual API Testing

```bash
# Health check
curl http://localhost:8000/health

# Test grab endpoint
curl -X POST http://localhost:8000/grab \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{"title": "Inception 2010"}'
```

## 🐳 Docker

```bash
# Build and run
make docker-build
make docker-up

# View logs
make docker-logs
```

## 🔒 Security

- Bearer token authentication required
- HTTPS recommended (configure at reverse proxy)
- IP allowlisting recommended at reverse proxy level
- No secrets logged or exposed in responses

## 🛠️ Development

```bash
# Install pre-commit hooks
make pre-commit-install

# Run pre-commit manually
make pre-commit-run

# Development server with auto-reload
make dev
```

## 📊 Status

- ✅ Stage 1: Repo scaffolding and FastAPI skeleton
- ⏳ Stage 2: Radarr/Sonarr implementation
- ⏳ Stage 3: Jackett blackhole implementation
- ⏳ Stage 4: Docker and compose setup
- ⏳ Stage 5: Documentation and OpenAPI
- ⏳ Stage 6: GitHub repo and CI/CD
- ⏳ Stage 7: Polishing and health endpoints

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.