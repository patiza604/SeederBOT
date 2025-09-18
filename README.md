# SeederBot 🤖

[![Build Status](https://github.com/your-username/seederbot/workflows/CI/badge.svg)](https://github.com/your-username/seederbot/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a393.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg)](https://www.docker.com/)

A secure FastAPI service that triggers media searches from ChatGPT via webhook, using **Jackett → Radarr/Sonarr → Deluge** as the primary path, with torrent blackhole fallback.

## 🎯 Features

- **🔐 Secure Authentication**: Bearer token protection for all endpoints
- **🎬 Dual Operation Modes**:
  - **Radarr Mode**: Integrates with Radarr for movie management and automated downloading
  - **Blackhole Mode**: Direct Jackett search with .torrent file blackhole for manual import
- **🤖 ChatGPT Integration**: Ready-to-use OpenAPI specification for ChatGPT Actions
- **🐳 Docker Ready**: Multi-stage builds with full media stack orchestration
- **🔍 Smart Filtering**: Quality-based torrent selection with configurable criteria
- **📊 Health Monitoring**: Built-in health checks and structured logging
- **⚡ High Performance**: Async FastAPI with optimized request handling

## 🏗️ Architecture

```
ChatGPT Action → SeederBot API → [Radarr Mode OR Blackhole Mode] → Deluge

Mode A (Primary):  POST /grab → Radarr API → Jackett (via Radarr) → Deluge
Mode B (Fallback): POST /grab → Jackett API → Download .torrent → Watch Folder → Deluge AutoAdd
```

### Components

- **SeederBot**: FastAPI application with authentication and media search logic
- **Radarr**: Movie collection manager with automatic quality upgrading
- **Jackett**: Torrent indexer proxy supporting 100+ trackers
- **Deluge**: BitTorrent client with AutoAdd plugin for blackhole support
- **Nginx**: Optional reverse proxy with SSL termination and rate limiting

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.11+** (for local development)
- **Poetry** (for dependency management)

### Option 1: Docker Compose (Recommended)

1. **Clone and configure**:
   ```bash
   git clone https://github.com/your-username/seederbot.git
   cd seederbot
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start the full media stack**:
   ```bash
   docker-compose up -d
   ```

3. **Configure services**:
   - **Radarr**: http://localhost:7878 → Settings → General → Copy API Key to `.env`
   - **Jackett**: http://localhost:9117 → Add indexers → Copy API Key to `.env`
   - **Deluge**: http://localhost:8112 → Enable AutoAdd plugin → Set watch folder to `/data/torrents/watch`

4. **Test the API**:
   ```bash
   curl -X POST http://localhost:8000/grab \
     -H "Authorization: Bearer your-token-here" \
     -H "Content-Type: application/json" \
     -d '{"title": "Inception", "year": 2010}'
   ```

### Option 2: Standalone Deployment

For existing media infrastructure:

```bash
# Use standalone compose file
docker-compose -f docker-compose.standalone.yml up -d

# Or run single container
docker run -d -p 8000:8000 --env-file .env seederbot:latest
```

### Option 3: Local Development

```bash
# Install dependencies
poetry install

# Copy environment file
cp .env.example .env

# Start development server
poetry run uvicorn src.app.main:app --reload

# Run tests
poetry run pytest -v
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with your configuration:

```bash
# App Configuration
APP_TOKEN=your-super-secure-random-token-here
MODE=radarr  # or 'blackhole'
HOST=0.0.0.0
PORT=8000

# Radarr Configuration (for primary path)
RADARR_URL=http://radarr:7878
RADARR_API_KEY=your-radarr-api-key-here
ROOT_FOLDER=/movies
QUALITY_PROFILE_ID=4

# Jackett Configuration (for both paths)
JACKETT_URL=http://jackett:9117
JACKETT_API_KEY=your-jackett-api-key-here

# Blackhole Configuration
CATEGORIES=2000,2010  # IPTorrents movie categories
MIN_SEEDERS=20
QUALITY_REGEX=1080p.*WEB-DL|1080p.*BluRay
EXCLUDE_REGEX=CAM|TS|TC|WORKPRINT
MIN_SIZE_GB=2.5
MAX_SIZE_GB=6.0
AUTOADD_WATCH_DIR=/data/torrents/watch
```

### Operation Modes

#### Radarr Mode (Recommended)
- Integrates with Radarr for movie discovery and management
- Automatic quality profile selection and monitoring
- Leverages Radarr's indexer configuration
- Provides rich metadata and organization

#### Blackhole Mode (Fallback)
- Direct Jackett integration for torrent search
- Downloads .torrent files to watch directory
- Requires manual Deluge AutoAdd configuration
- Useful when Radarr integration isn't available

### Quality Filtering

SeederBot applies intelligent filtering to ensure high-quality downloads:

- **Seeders**: Minimum 20 seeders (configurable)
- **Quality**: Prefers 1080p WEB-DL and BluRay releases
- **Size**: 2.5-6GB range to balance quality and storage
- **Exclusions**: Filters out CAM, TS, TC, and workprint releases
- **Scoring**: Advanced algorithm considering seeders, quality, size, and freeleech status

## 🤖 ChatGPT Integration

### Setting up ChatGPT Action

1. **Create a new GPT** in ChatGPT with the following configuration:

2. **Import the OpenAPI specification**:
   ```
   Use the schema from: https://your-domain.com/openapi.json
   ```

3. **Configure authentication**:
   - Type: `Bearer Token`
   - Token: `your-app-token-from-env`

4. **Test the integration**:
   ```
   "Please download Inception from 2010"
   ```

### Example ChatGPT Prompts

- `"Download the movie Blade Runner 2049"`
- `"Get Dune 2021 in the best quality available"`
- `"Add The Matrix trilogy to my collection"`

## 🔧 API Reference

### Authentication

All endpoints require Bearer token authentication:

```bash
Authorization: Bearer your-app-token
```

### Endpoints

#### `GET /health`
Returns service health status and configuration.

**Response:**
```json
{
  "status": "healthy",
  "mode": "radarr",
  "version": "0.1.0"
}
```

#### `POST /grab`
Triggers media search and download.

**Request:**
```json
{
  "title": "Inception",
  "year": 2010,
  "type": "movie"
}
```

**Success Response:**
```json
{
  "status": "success",
  "message": "Successfully added 'Inception' to Radarr with auto-search",
  "details": {
    "mode": "radarr",
    "title": "Inception",
    "year": 2010,
    "movie_id": 123,
    "tmdb_id": 27205,
    "search_triggered": true
  }
}
```

## 🐳 Docker Deployment

### Available Compose Files

- **`docker-compose.yml`**: Full media stack with all services
- **`docker-compose.standalone.yml`**: SeederBot only for existing infrastructure
- **`docker-compose.development.yml`**: Development environment with hot reload
- **Profiles**: `proxy` (nginx), `full-stack` (including Sonarr)

### Makefile Commands

```bash
# Docker operations
make docker-build              # Build SeederBot image
make docker-run                # Run standalone container
make docker-up                 # Start full media stack
make docker-up-standalone      # Start SeederBot only
make docker-up-dev            # Start development environment
make docker-down              # Stop all services

# Development
make dev                      # Start development server
make test                     # Run test suite
make lint                     # Check code quality
make format                   # Format code
```

## 🛡️ Security Considerations

- **Authentication**: Always use strong, randomly generated tokens
- **Network**: Deploy behind reverse proxy with HTTPS in production
- **Secrets**: Never commit API keys or tokens to version control
- **Access Control**: Limit API access to trusted clients only
- **Compliance**: Ensure all content downloads comply with local laws and tracker rules

## 🐛 Troubleshooting

### Common Issues

#### "getaddrinfo failed" Error
- **Cause**: Cannot resolve hostname (e.g., `radarr`, `jackett`)
- **Solution**: Update `.env` with actual IP addresses or ensure Docker networking

#### "No suitable torrents found"
- **Cause**: Quality filters too restrictive or no indexers configured
- **Solution**: Check Jackett indexers, adjust quality regex, or lower seeder requirements

#### "Authentication failed"
- **Cause**: Invalid API keys or incorrect URLs
- **Solution**: Verify API keys in Radarr/Jackett web interfaces

#### Container health check failures
- **Cause**: Service not ready or misconfiguration
- **Solution**: Check logs with `docker-compose logs seederbot`

### Debugging

```bash
# View service logs
docker-compose logs -f seederbot

# Check service health
curl http://localhost:8000/health

# Test Radarr connectivity
curl -H "X-Api-Key: your-key" http://localhost:7878/api/v3/system/status

# Test Jackett connectivity
curl http://localhost:9117/api/v2.0/indexers/all/results/torznab?apikey=your-key&t=search&q=test
```

### Performance Tuning

- **Indexers**: Configure multiple indexers in Jackett for better results
- **Quality Profiles**: Set up appropriate quality profiles in Radarr
- **Resource Limits**: Adjust Docker memory/CPU limits for your hardware
- **Rate Limiting**: Configure nginx rate limiting to prevent abuse

## 🧪 Development

### Project Structure

```
seederbot/
├── src/app/           # FastAPI application
│   ├── main.py        # Application entry point
│   ├── models.py      # Pydantic models
│   ├── config.py      # Configuration management
│   ├── radarr.py      # Radarr integration
│   ├── jackett.py     # Jackett API client
│   └── blackhole.py   # Blackhole functionality
├── tests/             # Test suite
├── ops/               # Operations and deployment
├── docker-compose.yml # Full stack deployment
└── Dockerfile         # Multi-stage container build
```

### Running Tests

```bash
# Run all tests
poetry run pytest -v

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/test_radarr.py -v
```

### Code Quality

```bash
# Lint code
poetry run ruff check src tests

# Format code
poetry run black src tests
poetry run isort src tests

# Type checking
poetry run mypy src
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-username/seederbot.git
cd seederbot

# Install dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install

# Run development server
poetry run uvicorn src.app.main:app --reload
```

## 📊 Project Status

- ✅ **Stage 1**: Repo scaffolding, FastAPI skeleton, CI/CD setup
- ✅ **Stage 2**: Radarr integration implemented and tested
- ✅ **Stage 3**: Jackett blackhole implementation completed
- ✅ **Stage 4**: Docker and compose setup finished
- ⏳ **Stage 5**: Documentation and OpenAPI (in progress)
- ⏳ **Stage 6**: GitHub repo and CI/CD
- ⏳ **Stage 7**: Polishing and production ready

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [Radarr](https://radarr.video/) for movie collection management
- [Jackett](https://github.com/Jackett/Jackett) for indexer proxy functionality
- [LinuxServer.io](https://www.linuxserver.io/) for high-quality Docker images

## ⚠️ Disclaimer

This software is for educational and personal use only. Users are responsible for:
- Complying with all applicable laws and regulations
- Respecting copyright and intellectual property rights
- Following private tracker rules and maintaining proper ratios
- Using legal content sources and torrents

The authors are not responsible for any misuse of this software.

---

**Made with ❤️ for the self-hosted media community**