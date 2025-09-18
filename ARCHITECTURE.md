# SeederBot Architecture Documentation 🏗️

This document provides detailed architecture diagrams and flow explanations for SeederBot.

## 🌐 System Overview

```
┌─────────────────┐    HTTPS    ┌─────────────────┐    Docker Network    ┌──────────────────────┐
│                 │ ────────────▶│                 │ ───────────────────▶│                      │
│   ChatGPT       │              │   Reverse       │                     │   SeederBot          │
│   Action        │              │   Proxy         │                     │   (FastAPI)          │
│                 │◀────────────│   (nginx)       │◀─────────────────── │                      │
└─────────────────┘              └─────────────────┘                     └──────────────────────┘
                                                                                      │
                                                                                      │ Mode Selection
                                                                                      ▼
                                            ┌─────────────────────────────────────────────────────────┐
                                            │                                                         │
                                            │                   Operation Modes                      │
                                            │                                                         │
                                            └─────────────────────────────────────────────────────────┘
                                                                      │
                                                  ┌───────────────────┼───────────────────┐
                                                  │                   │                   │
                                                  ▼                   ▼                   ▼
                                        ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
                                        │                 │ │                 │ │                 │
                                        │  Radarr Mode    │ │ Blackhole Mode  │ │   Health Mode   │
                                        │   (Primary)     │ │   (Fallback)    │ │  (Monitoring)   │
                                        │                 │ │                 │ │                 │
                                        └─────────────────┘ └─────────────────┘ └─────────────────┘
```

## 🎬 Radarr Mode Flow (Primary Path)

```
┌─────────────┐    POST /grab     ┌─────────────┐    Search Movie    ┌─────────────┐
│             │ ─────────────────▶│             │ ──────────────────▶│             │
│  ChatGPT    │  {"title": ".."}  │ SeederBot   │   Radarr Lookup    │   Radarr    │
│  Action     │                   │   API       │      API           │   Service   │
│             │◀─────────────────│             │◀────────────────── │             │
└─────────────┘    JSON Response  └─────────────┘   Movie Metadata   └─────────────┘
                                                                             │
                                                                             │ Add Movie
                                                                             │ + Auto Search
                                                                             ▼
┌─────────────┐    .torrent       ┌─────────────┐    Search Request   ┌─────────────┐
│             │◀─────────────────│             │◀────────────────── │             │
│   Deluge    │     Download      │   Jackett   │   Configured        │   Radarr    │
│  BitTorrent │                   │   Indexer   │   Indexers          │   Indexer   │
│   Client    │                   │   Proxy     │                     │ Integration │
└─────────────┘                   └─────────────┘                     └─────────────┘
       │
       │ Download Complete
       ▼
┌─────────────┐
│             │
│ Media File  │
│ in /movies  │
│ Directory   │
└─────────────┘
```

### Radarr Mode Sequence

1. **ChatGPT Action** sends POST request to `/grab` endpoint
2. **SeederBot** validates request and authentication
3. **SeederBot** queries **Radarr API** for movie lookup
4. **Radarr** returns movie metadata (TMDB ID, title, year, etc.)
5. **SeederBot** adds movie to **Radarr** with auto-search enabled
6. **Radarr** triggers search across configured indexers
7. **Radarr** evaluates results based on quality profiles
8. **Radarr** sends best result to **Deluge** for download
9. **Deluge** downloads torrent and moves to media directory
10. **SeederBot** returns success response to **ChatGPT**

## 🕳️ Blackhole Mode Flow (Fallback Path)

```
┌─────────────┐    POST /grab     ┌─────────────┐   Direct Search    ┌─────────────┐
│             │ ─────────────────▶│             │ ──────────────────▶│             │
│  ChatGPT    │  {"title": ".."}  │ SeederBot   │   Jackett API      │   Jackett   │
│  Action     │                   │   API       │   Torznab Query    │   Service   │
│             │◀─────────────────│             │◀────────────────── │             │
└─────────────┘    JSON Response  └─────────────┘   Torrent Results   └─────────────┘
                                           │                                  │
                                           │ Smart Filtering                  │ Queries
                                           │ & Selection                      │ Indexers
                                           ▼                                  ▼
                                 ┌─────────────┐                    ┌─────────────┐
                                 │             │                    │             │
                                 │ Quality     │                    │ Configured  │
                                 │ Filter      │                    │ Torrent     │
                                 │ Algorithm   │                    │ Indexers    │
                                 │             │                    │             │
                                 └─────────────┘                    └─────────────┘
                                           │
                                           │ Best Result
                                           ▼
┌─────────────┐    AutoAdd        ┌─────────────┐   .torrent File   ┌─────────────┐
│             │◀─────────────────│             │◀────────────────── │             │
│   Deluge    │   Detection       │   Watch     │     Download       │ SeederBot   │
│  BitTorrent │                   │ Directory   │                    │ Blackhole   │
│   Client    │                   │             │                    │  Handler    │
└─────────────┘                   └─────────────┘                    └─────────────┘
       │
       │ Download Complete
       ▼
┌─────────────┐
│             │
│ Media File  │
│ in Download │
│ Directory   │
└─────────────┘
```

### Blackhole Mode Sequence

1. **ChatGPT Action** sends POST request to `/grab` endpoint
2. **SeederBot** validates request and authentication
3. **SeederBot** queries **Jackett API** directly for torrents
4. **Jackett** searches across all configured indexers
5. **SeederBot** applies quality filtering algorithm:
   - Minimum seeders check
   - Quality regex matching (1080p WEB-DL/BluRay)
   - Size limits (2.5-6GB)
   - Exclusion patterns (CAM, TS, etc.)
   - Scoring algorithm for best selection
6. **SeederBot** downloads `.torrent` file for best result
7. **SeederBot** saves `.torrent` to watch directory
8. **Deluge AutoAdd** detects new `.torrent` file
9. **Deluge** begins download automatically
10. **SeederBot** returns success response to **ChatGPT**

## 🔧 Quality Filtering Algorithm

```
┌─────────────────┐
│                 │
│ Raw Torrent     │
│ Search Results  │
│ from Jackett    │
│                 │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│                 │    ❌ Fail: < 20 seeders
│ Seeder Count    │ ─────────────────────────┐
│ Filter          │                          │
│ (MIN_SEEDERS)   │                          │
│                 │    ✅ Pass               │
└─────────┬───────┘                          │
          │                                  │
          ▼                                  │
┌─────────────────┐                          │
│                 │    ❌ Fail: Not 1080p    │
│ Quality Regex   │ ─────────────────────────┤
│ Filter          │                          │
│ (QUALITY_REGEX) │                          │
│                 │    ✅ Pass               │
└─────────┬───────┘                          │
          │                                  │
          ▼                                  │
┌─────────────────┐                          │
│                 │    ❌ Fail: CAM/TS/TC    │
│ Exclusion       │ ─────────────────────────┤
│ Pattern Filter  │                          │
│ (EXCLUDE_REGEX) │                          │
│                 │    ✅ Pass               │
└─────────┬───────┘                          │
          │                                  │
          ▼                                  │
┌─────────────────┐                          │
│                 │    ❌ Fail: Wrong size   │
│ Size Range      │ ─────────────────────────┤
│ Filter          │                          │
│ (MIN/MAX_SIZE)  │                          │
│                 │    ✅ Pass               │
└─────────┬───────┘                          │
          │                                  │
          ▼                                  │
┌─────────────────┐                          │
│                 │                          │
│ Scoring         │                          │
│ Algorithm       │                          │
│                 │                          │
└─────────┬───────┘                          │
          │                                  │
          ▼                                  │
┌─────────────────┐                          │
│                 │                          │
│ Sort by Score   │                          │
│ (Highest First) │                          │
│                 │                          │
└─────────┬───────┘                          │
          │                                  │
          ▼                                  │
┌─────────────────┐                          │
│                 │                          │
│ Best Result     │                          │
│ Selected        │                          │
│                 │                          │
└─────────────────┘                          │
                                             │
                              ┌──────────────▼──────────────┐
                              │                             │
                              │        Rejected             │
                              │      (Not Downloaded)       │
                              │                             │
                              └─────────────────────────────┘
```

### Scoring Algorithm Details

Each passing torrent gets a score based on:

```python
score = 0.0

# Seeder bonus (logarithmic, max 10 points)
score += min(seeders / 10.0, 10.0)

# Quality preference
if "web-dl" in title.lower():
    score += 10          # Highest preference
elif "bluray" in title.lower():
    score += 8           # Second preference
elif "webrip" in title.lower():
    score += 6           # Third preference

# Size preference (closer to 4GB is better)
size_gb = size / (1024 * 1024 * 1024)
size_diff = abs(size_gb - 4.0)
score += max(0, 5 - size_diff)

# Freeleech bonus
if download_volume_factor == 0.0:
    score += 15          # Major bonus for freeleech

return score
```

## 🐳 Docker Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Docker Host System                                    │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                         media-stack Network                                │    │
│  │                                                                             │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │    │
│  │  │             │  │             │  │             │  │             │        │    │
│  │  │ SeederBot   │  │   Radarr    │  │  Jackett    │  │   Deluge    │        │    │
│  │  │   :8000     │  │   :7878     │  │   :9117     │  │   :8112     │        │    │
│  │  │             │  │             │  │             │  │   :6881     │        │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │    │
│  │         │                 │                 │                 │            │    │
│  │         └─────────────────┼─────────────────┼─────────────────┘            │    │
│  │                           │                 │                              │    │
│  │  ┌─────────────┐          │                 │          ┌─────────────┐     │    │
│  │  │             │          │                 │          │             │     │    │
│  │  │   Nginx     │          │                 │          │   Sonarr    │     │    │
│  │  │   :80/443   │          │                 │          │   :8989     │     │    │
│  │  │ (Optional)  │          │                 │          │ (Optional)  │     │    │
│  │  │             │          │                 │          │             │     │    │
│  │  └─────────────┘          │                 │          └─────────────┘     │    │
│  │                           │                 │                              │    │
│  └───────────────────────────┼─────────────────┼──────────────────────────────┘    │
│                              │                 │                                   │
│  ┌───────────────────────────┼─────────────────┼──────────────────────────────┐    │
│  │                    Volume Mounts            │                              │    │
│  │                                             │                              │    │
│  │  ./config/radarr   ────────┘                 │                              │    │
│  │  ./config/jackett  ──────────────────────────┘                              │    │
│  │  ./config/deluge                                                            │    │
│  │  ./data/movies                                                              │    │
│  │  ./data/downloads                                                           │    │
│  │  ./data/torrents                                                            │    │
│  │  ./logs                                                                     │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────┘

External Access:
┌─────────────┐    Port 8000     ┌─────────────────────────────────────┐
│             │ ─────────────────▶│ SeederBot API                      │
│ Internet/   │                   │ (ChatGPT Actions)                  │
│ ChatGPT     │                   │                                     │
│             │◀─────────────────│                                     │
└─────────────┘                   └─────────────────────────────────────┘

┌─────────────┐    Port 7878     ┌─────────────────────────────────────┐
│             │ ─────────────────▶│ Radarr Web UI                      │
│ Local       │                   │ (Configuration)                    │
│ Network     │                   │                                     │
│             │◀─────────────────│                                     │
└─────────────┘                   └─────────────────────────────────────┘
```

## 🔄 Data Flow Patterns

### Configuration Data Flow

```
┌─────────────┐    Environment     ┌─────────────┐    Pydantic        ┌─────────────┐
│             │    Variables       │             │    Settings        │             │
│ .env File   │ ──────────────────▶│ Config      │ ──────────────────▶│ Application │
│             │    (.env)          │ Loader      │    Validation      │ Runtime     │
│             │                    │             │                    │             │
└─────────────┘                    └─────────────┘                    └─────────────┘
                                           │
                                           │ Default Values
                                           ▼
                                 ┌─────────────┐
                                 │             │
                                 │ pyproject   │
                                 │ .toml       │
                                 │ Defaults    │
                                 │             │
                                 └─────────────┘
```

### API Request Flow

```
┌─────────────┐    HTTPS          ┌─────────────┐    Bearer Token    ┌─────────────┐
│             │    Request        │             │    Validation      │             │
│ ChatGPT     │ ──────────────────▶│ FastAPI     │ ──────────────────▶│ Auth        │
│ Action      │    JSON Body      │ Router      │                    │ Middleware  │
│             │                   │             │                    │             │
└─────────────┘                   └─────────────┘                    └─────────────┘
                                           │                                  │
                                           │ Pydantic Model                   │ Success
                                           │ Validation                       ▼
                                           ▼                          ┌─────────────┐
                                 ┌─────────────┐                     │             │
                                 │             │ ◀──────────────────│ Business    │
                                 │ Request     │    Validated Data   │ Logic       │
                                 │ Models      │                     │ Handler     │
                                 │             │                     │             │
                                 └─────────────┘                     └─────────────┘
```

### Error Handling Flow

```
┌─────────────┐    Exception      ┌─────────────┐    Error Response  ┌─────────────┐
│             │    Occurs         │             │    Generation      │             │
│ Business    │ ──────────────────▶│ Exception   │ ──────────────────▶│ HTTP        │
│ Logic       │                   │ Handler     │                    │ Response    │
│             │                   │             │                    │             │
└─────────────┘                   └─────────────┘                    └─────────────┘
                                           │
                                           │ Structured Logging
                                           ▼
                                 ┌─────────────┐
                                 │             │
                                 │ Logger      │
                                 │ (with       │
                                 │ context)    │
                                 │             │
                                 └─────────────┘
```

## 🔐 Security Architecture

### Authentication Flow

```
┌─────────────┐    API Request    ┌─────────────┐    Extract Token   ┌─────────────┐
│             │    with Bearer    │             │    from Header     │             │
│ Client      │    Token          │ FastAPI     │                    │ Security    │
│ (ChatGPT)   │ ──────────────────▶│ Security    │ ──────────────────▶│ Dependency  │
│             │                   │ Middleware  │                    │             │
└─────────────┘                   └─────────────┘                    └─────────────┘
                                                                              │
                                                                              │ Compare with
                                                                              │ APP_TOKEN
                                                                              ▼
┌─────────────┐    Access Denied  ┌─────────────┐    Token Valid     ┌─────────────┐
│             │ ◀─────────────────│             │ ◀─────────────────│             │
│ HTTP 401    │                   │ Route       │                   │ Token       │
│ Response    │                   │ Handler     │                   │ Validator   │
│             │                   │             │                   │             │
└─────────────┘                   └─────────────┘                   └─────────────┘
                                           │
                                           │ Token Valid
                                           ▼
                                 ┌─────────────┐
                                 │             │
                                 │ Business    │
                                 │ Logic       │
                                 │ Execution   │
                                 │             │
                                 └─────────────┘
```

### Network Security

```
┌─────────────┐    HTTPS Only     ┌─────────────┐    Internal        ┌─────────────┐
│             │    (Port 443)     │             │    Network         │             │
│ Internet    │ ──────────────────▶│ Nginx       │ ──────────────────▶│ SeederBot   │
│ (ChatGPT)   │                   │ Reverse     │    (Docker)        │ Container   │
│             │                   │ Proxy       │                    │             │
└─────────────┘                   └─────────────┘                    └─────────────┘
                                           │
                                           │ Rate Limiting
                                           │ SSL Termination
                                           │ Header Security
                                           ▼
                                 ┌─────────────┐
                                 │             │
                                 │ Security    │
                                 │ Headers &   │
                                 │ Monitoring  │
                                 │             │
                                 └─────────────┘
```

## 📊 Monitoring & Health Checks

### Health Check Architecture

```
┌─────────────┐    /health        ┌─────────────┐    Service Checks  ┌─────────────┐
│             │    Endpoint       │             │                    │             │
│ Monitoring  │ ──────────────────▶│ SeederBot   │ ──────────────────▶│ Radarr      │
│ System      │                   │ Health      │                    │ Status API  │
│             │                   │ Handler     │                    │             │
└─────────────┘                   └─────────────┘                    └─────────────┘
                                           │                                  │
                                           │ Aggregate Status                 │ Health
                                           ▼                                  ▼
                                 ┌─────────────┐                    ┌─────────────┐
                                 │             │ ◀──────────────────│             │
                                 │ Health      │    Status Response │ Jackett     │
                                 │ Response    │                    │ API Check   │
                                 │ JSON        │                    │             │
                                 └─────────────┘                    └─────────────┘
```

This architecture documentation provides a comprehensive view of how SeederBot operates at different levels, from high-level system interactions down to detailed data flows and security considerations.