# SeederBot Troubleshooting Guide 🔧

This guide covers common issues and their solutions when running SeederBot.

## 🚨 Common Error Messages

### "getaddrinfo failed" Error

**Full Error:**
```
{"status":"error","message":"Failed to add movie to Radarr","details":{"mode":"radarr","title":"Inception","error":"[Errno 11001] getaddrinfo failed"}}
```

**Cause:** Cannot resolve hostname (e.g., `radarr`, `jackett`) in the configuration.

**Solutions:**
1. **Docker Compose Issue**: Ensure services are on the same network
   ```bash
   docker network ls
   docker-compose ps
   ```

2. **Update .env with IP addresses** instead of hostnames:
   ```bash
   # Instead of:
   RADARR_URL=http://radarr:7878

   # Use:
   RADARR_URL=http://192.168.1.100:7878
   ```

3. **Check service availability**:
   ```bash
   curl http://localhost:7878/api/v3/system/status
   ```

### "No suitable torrents found"

**Full Error:**
```
{"status":"error","message":"No suitable torrents found for 'Movie Title'","details":{"mode":"blackhole","title":"Movie Title","year":2023}}
```

**Cause:** Quality filters too restrictive or no indexers configured.

**Solutions:**
1. **Check Jackett indexers**:
   - Visit http://localhost:9117
   - Ensure indexers are configured and working
   - Test search manually in Jackett UI

2. **Adjust quality filters** in `.env`:
   ```bash
   # More permissive settings
   MIN_SEEDERS=5
   QUALITY_REGEX=1080p.*|720p.*WEB-DL|BluRay
   MIN_SIZE_GB=1.0
   MAX_SIZE_GB=10.0
   ```

3. **Test Jackett API directly**:
   ```bash
   curl "http://localhost:9117/api/v2.0/indexers/all/results/torznab?apikey=YOUR_KEY&t=search&q=popular+movie"
   ```

### "Authentication failed" / "Invalid authentication token"

**Full Error:**
```
{"detail":"Invalid authentication token"}
```

**Cause:** Wrong or missing Bearer token.

**Solutions:**
1. **Check token in .env**:
   ```bash
   cat .env | grep APP_TOKEN
   ```

2. **Test with correct token**:
   ```bash
   curl -X POST http://localhost:8000/grab \
     -H "Authorization: Bearer $(grep APP_TOKEN .env | cut -d= -f2)" \
     -H "Content-Type: application/json" \
     -d '{"title": "Test Movie"}'
   ```

3. **Generate new token** if needed:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

### "Radarr API error" / "Invalid API key"

**Cause:** Incorrect Radarr API key or URL.

**Solutions:**
1. **Get correct API key**:
   - Open Radarr web interface (http://localhost:7878)
   - Go to Settings → General → Security
   - Copy the API Key

2. **Test API key**:
   ```bash
   curl -H "X-Api-Key: YOUR_RADARR_KEY" \
     http://localhost:7878/api/v3/system/status
   ```

3. **Check Radarr URL format**:
   ```bash
   # Correct format
   RADARR_URL=http://localhost:7878

   # Common mistakes
   RADARR_URL=http://localhost:7878/  # Extra slash
   RADARR_URL=https://localhost:7878  # Wrong protocol
   ```

## 🐳 Docker Issues

### Container Health Check Failures

**Symptom:** Container shows as "unhealthy" in `docker ps`

**Diagnosis:**
```bash
# Check container logs
docker-compose logs seederbot

# Check health check status
docker inspect seederbot | grep -A 10 Health
```

**Solutions:**
1. **Service not ready**: Wait longer for startup
2. **Port conflict**: Change port mapping in docker-compose.yml
3. **Configuration error**: Check .env file
4. **Resource limits**: Increase memory/CPU limits

### Port Already in Use

**Error:**
```
ERROR: for seederbot  Cannot start service seederbot: driver failed programming external connectivity on endpoint seederbot: Bind for 0.0.0.0:8000 failed: port is already allocated
```

**Solutions:**
1. **Find process using port**:
   ```bash
   # Windows
   netstat -ano | findstr :8000

   # Linux/Mac
   lsof -i :8000
   ```

2. **Change port** in docker-compose.yml:
   ```yaml
   ports:
     - "8001:8000"  # Use different external port
   ```

3. **Stop conflicting service**:
   ```bash
   # Stop all SeederBot containers
   docker stop $(docker ps -q --filter ancestor=seederbot)
   ```

### Volume Mount Issues

**Error:**
```
docker: Error response from daemon: invalid mount config for type "bind": bind source path does not exist
```

**Solutions:**
1. **Create directories**:
   ```bash
   mkdir -p ./data/torrents ./data/movies ./data/downloads
   mkdir -p ./config/radarr ./config/jackett ./config/deluge
   ```

2. **Check permissions**:
   ```bash
   # Linux/Mac
   sudo chown -R 1000:1000 ./data ./config

   # Windows - run as Administrator
   icacls ./data /grant Everyone:F /T
   ```

## 🔧 Configuration Issues

### Environment Variables Not Loading

**Symptom:** Settings show default values instead of .env values

**Solutions:**
1. **Check .env file location** (must be in project root):
   ```bash
   ls -la .env
   cat .env
   ```

2. **Verify .env format** (no spaces around =):
   ```bash
   # Correct
   APP_TOKEN=abc123

   # Incorrect
   APP_TOKEN = abc123
   ```

3. **Check for special characters**:
   ```bash
   # Escape special characters in values
   APP_TOKEN="abc123!@#$%"
   ```

### Quality Profile ID Issues

**Error:** Radarr returns "Quality profile not found"

**Solutions:**
1. **Get correct profile ID**:
   ```bash
   curl -H "X-Api-Key: YOUR_KEY" \
     http://localhost:7878/api/v3/qualityprofile
   ```

2. **Update .env** with correct ID:
   ```bash
   QUALITY_PROFILE_ID=6  # Use actual ID from API response
   ```

### Root Folder Path Issues

**Error:** Radarr returns "Root folder not found"

**Solutions:**
1. **Check root folders** in Radarr:
   ```bash
   curl -H "X-Api-Key: YOUR_KEY" \
     http://localhost:7878/api/v3/rootfolder
   ```

2. **Update .env** with correct path:
   ```bash
   ROOT_FOLDER=/data/movies  # Use actual path
   ```

3. **Create folder** if it doesn't exist:
   ```bash
   mkdir -p /data/movies
   chown -R 1000:1000 /data/movies
   ```

## 🌐 Network Issues

### Services Can't Communicate

**Symptom:** Services timeout when trying to reach each other

**Diagnosis:**
```bash
# Check Docker networks
docker network ls
docker network inspect seederbot_media-stack

# Test connectivity between containers
docker exec seederbot ping radarr
docker exec seederbot curl http://jackett:9117/api/v2.0/indexers
```

**Solutions:**
1. **Ensure same network**:
   ```yaml
   # In docker-compose.yml
   services:
     seederbot:
       networks:
         - media-stack
     radarr:
       networks:
         - media-stack
   ```

2. **Use service names** as hostnames in .env:
   ```bash
   RADARR_URL=http://radarr:7878
   JACKETT_URL=http://jackett:9117
   ```

3. **Check firewall rules** on host system

### External Access Issues

**Symptom:** Can't access SeederBot from outside host

**Solutions:**
1. **Check port mapping**:
   ```yaml
   ports:
     - "8000:8000"  # External:Internal
   ```

2. **Test local access first**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Check host firewall**:
   ```bash
   # Linux
   sudo ufw allow 8000

   # Windows
   netsh advfirewall firewall add rule name="SeederBot" dir=in action=allow protocol=TCP localport=8000
   ```

## 📊 Performance Issues

### Slow Response Times

**Symptoms:** API requests take >30 seconds

**Diagnosis:**
```bash
# Check container resources
docker stats seederbot

# Test individual components
time curl http://localhost:7878/api/v3/system/status
time curl http://localhost:9117/api/v2.0/indexers
```

**Solutions:**
1. **Increase timeout values** in config:
   ```python
   # In radarr.py and jackett.py
   async with httpx.AsyncClient(timeout=60.0) as client:
   ```

2. **Optimize Docker resources**:
   ```yaml
   services:
     seederbot:
       deploy:
         resources:
           limits:
             memory: 512M
             cpus: "0.5"
   ```

3. **Check indexer performance** in Jackett UI

### High Memory Usage

**Diagnosis:**
```bash
docker stats seederbot
```

**Solutions:**
1. **Reduce concurrent operations**
2. **Increase container memory limit**
3. **Monitor for memory leaks** in logs

## 🔍 Debugging Tools

### Enable Debug Logging

1. **FastAPI debug mode**:
   ```bash
   uvicorn src.app.main:app --reload --log-level debug
   ```

2. **Python logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### Useful Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f seederbot

# View last 100 lines
docker-compose logs --tail=100 seederbot

# Follow logs in real-time
docker logs -f seederbot

# Execute commands inside container
docker exec -it seederbot /bin/bash

# Check container status
docker inspect seederbot

# Test API endpoints
curl -v http://localhost:8000/health
```

### Health Check Commands

```bash
# Test SeederBot health
curl http://localhost:8000/health

# Test Radarr connectivity
curl -H "X-Api-Key: YOUR_KEY" http://localhost:7878/api/v3/system/status

# Test Jackett connectivity
curl http://localhost:9117/api/v2.0/indexers/all/results/torznab?apikey=YOUR_KEY&t=search&q=test

# Test Deluge AutoAdd
ls -la /data/torrents/watch/
```

## 🛡️ Security Issues

### Token Security

**Best Practices:**
1. **Generate strong tokens**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Rotate tokens regularly**

3. **Use environment variables**, never hardcode tokens

4. **Restrict network access** with firewall rules

### SSL/TLS Issues

**For production deployment:**
1. **Use reverse proxy** (nginx) with SSL
2. **Get valid certificates** (Let's Encrypt)
3. **Force HTTPS** redirects
4. **Update .env** for production URLs

## 📝 Logging and Monitoring

### Important Log Locations

```bash
# Container logs
docker logs seederbot

# Application logs (if mounted)
tail -f ./logs/seederbot.log

# Radarr logs
docker exec radarr cat /config/logs/radarr.txt

# Jackett logs
docker exec jackett cat /config/Jackett/log.txt
```

### Log Analysis

**Look for these patterns:**

1. **Authentication errors**:
   ```
   INFO:src.app.main:Grab request: Movie Title (movie)
   ERROR:src.app.radarr:Error adding movie to Radarr: 401
   ```

2. **Network timeouts**:
   ```
   ERROR:src.app.jackett:Error searching Jackett: timeout
   ```

3. **Configuration issues**:
   ```
   ERROR:src.app.main:Invalid configuration for mode: radarr
   ```

## 🚀 Deployment & Git Issues

### Git Merge Conflicts During Deployment

**Symptom:** Error when pulling updates on remote server
```bash
error: Your local changes to the following files would be overwritten by merge:
	.claude/settings.local.json
```

**Solutions:**
1. **Stash local changes** before pulling:
   ```bash
   git stash save "Local config changes before update"
   git pull origin main
   git stash pop  # Restore changes if needed
   ```

2. **Use backup strategy** for important config:
   ```bash
   cp .env .env.backup
   cp .claude/settings.local.json .claude/settings.local.json.backup
   git reset --hard HEAD
   git pull origin main
   # Restore configs manually
   ```

3. **Configure .gitignore** properly:
   ```bash
   echo ".env" >> .gitignore
   echo ".claude/settings.local.json" >> .gitignore
   git rm --cached .claude/settings.local.json
   git commit -m "Remove local config from tracking"
   ```

### Service Management on Remote Servers

**Starting SeederBot in Background:**
```bash
# Method 1: Screen session (recommended)
screen -S seederbot
cd /path/to/SeederBot
poetry run uvicorn src.app.main:app --host 0.0.0.0 --port 8000
# Detach: Ctrl+A then D

# Method 2: Systemd service
sudo tee /etc/systemd/system/seederbot.service << EOF
[Unit]
Description=SeederBot API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/SeederBot
Environment=PATH=/home/ubuntu/.local/bin
ExecStart=/home/ubuntu/.local/bin/poetry run uvicorn src.app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable seederbot
sudo systemctl start seederbot
```

**Checking Service Status:**
```bash
# Screen sessions
screen -ls
screen -r seederbot  # Reattach to session

# Process management
pgrep -laf uvicorn
ps aux | grep seederbot

# Port usage
netstat -tulpn | grep :8000
lsof -i :8000
```

## 🤖 ChatGPT Action Configuration Issues

### "Invalid Action" Error in ChatGPT

**Symptom:** ChatGPT shows "invalid action" when trying to use the custom GPT

**Common Causes & Solutions:**

1. **OpenAPI Schema Format Issue:**
   ```json
   // ❌ Wrong: Using OpenAPI 3.0.0 format
   {
     "openapi": "3.0.0",
     "definitions": {
       "WatchlistRequest": {...}
     }
   }

   // ✅ Correct: Using OpenAPI 3.1.0 format
   {
     "openapi": "3.1.0",
     "components": {
       "schemas": {
         "WatchlistRequest": {...}
       }
     }
   }
   ```

2. **Server URL Not Accessible:**
   - Ensure your PUBLIC_BASE_URL is accessible from ChatGPT
   - Test with curl from a different network:
     ```bash
     curl https://your-domain.com/openapi.json
     curl https://your-domain.com/health
     ```

3. **Authentication Configuration:**
   - Use "API Key" authentication type in ChatGPT
   - Set header name to "Authorization"
   - Set API key value to "Bearer your-actual-token"

### ChatGPT Not Using the Action

**Symptom:** ChatGPT responds normally but doesn't trigger the API call

**Solutions:**

1. **Use Explicit Action Language:**
   ```bash
   # ✅ More likely to trigger action:
   "Add Inception (2010) to my watchlist using the action"
   "Use the watchlist tool to add Dune 2021"

   # ❌ May not trigger action:
   "Add Inception to my list"
   "I want to watch Dune"
   ```

2. **Check Action Privacy Setting:**
   - Ensure the custom GPT action is set to "Everyone" or shared appropriately
   - Test with a fresh conversation

3. **Mobile App Limitations:**
   - Custom actions are disabled in ChatGPT mobile apps
   - Use web browser interface at chat.openai.com

### OpenAPI Specification Issues

**Dynamic vs Static OpenAPI:**

1. **Dynamic (Recommended):**
   ```bash
   # Set in .env
   PUBLIC_BASE_URL=https://your-domain.com

   # ChatGPT will fetch from:
   https://your-domain.com/openapi.json
   ```

2. **Static Fallback:**
   ```bash
   # Edit chatgpt-action-spec.json manually
   "servers": [{"url": "https://your-actual-domain.com"}]
   ```

## 🌐 Ngrok & Tunneling Issues

### Ngrok URL Changes

**Symptom:** ChatGPT action stops working after ngrok restart

**Solutions:**

1. **Use Ngrok with Fixed Domain (Pro):**
   ```bash
   ngrok http 8000 --domain=your-reserved-domain.ngrok.app
   ```

2. **Update .env and Restart Services:**
   ```bash
   # Get new ngrok URL
   curl -s http://localhost:4040/api/tunnels | jq '.tunnels[0].public_url'

   # Update .env
   PUBLIC_BASE_URL=https://abc123.ngrok.app

   # Restart SeederBot
   screen -S seederbot -X quit
   screen -S seederbot
   poetry run uvicorn src.app.main:app --host 0.0.0.0 --port 8000
   ```

3. **Auto-Update Script:**
   ```bash
   #!/bin/bash
   # auto-update-ngrok.sh
   NEW_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')
   if [ "$NEW_URL" != "null" ]; then
       sed -i "s|PUBLIC_BASE_URL=.*|PUBLIC_BASE_URL=$NEW_URL|" .env
       echo "Updated PUBLIC_BASE_URL to $NEW_URL"
       # Restart your service here if needed
   fi
   ```

### Port Conflicts with Ngrok

**Error:** Port 8000 already in use

**Solutions:**
```bash
# Find process using port
lsof -i :8000
netstat -tulpn | grep :8000

# Use different port
poetry run uvicorn src.app.main:app --host 0.0.0.0 --port 8011
ngrok http 8011

# Update .env if needed
PORT=8011
```

## 📱 Mobile App Limitations

### ChatGPT Mobile Apps

**Issue:** Custom GPT actions don't work on mobile

**Workaround:**
1. **Use Web Browser:** Access chat.openai.com on mobile browser
2. **Desktop Only:** Custom actions only work in web interface
3. **Alternative:** Create IFTTT/Zapier webhook integration

### Browser Compatibility

**Tested Browsers:**
- ✅ Chrome/Chromium (recommended)
- ✅ Firefox
- ✅ Safari
- ❌ Internet Explorer (not supported)

## 🔄 Service Update & Maintenance

### Updating SeederBot

**Safe Update Procedure:**
```bash
# 1. Backup current state
cp .env .env.backup
git stash save "Local changes before update $(date)"

# 2. Pull updates
git pull origin main

# 3. Update dependencies
poetry install

# 4. Check for config changes
diff .env.example .env.backup

# 5. Test locally first
poetry run pytest

# 6. Restart service
screen -S seederbot -X quit
screen -S seederbot
poetry run uvicorn src.app.main:app --host 0.0.0.0 --port 8000
```

### Environment Variable Issues

**New Required Variables:**
When updating, check for new required environment variables:

```bash
# Compare with example
diff .env .env.example

# Common new variables to add:
PUBLIC_BASE_URL=https://your-domain.com
STRUCTURED_LOGGING=true
LOG_LEVEL=INFO
```

### Database/State Migration

**Watchlist Data:**
- Watchlist is stored in memory (resets on restart)
- For persistent storage, implement database backend
- Export/import functionality available via API

## 🆘 Getting Help

If you're still experiencing issues:

1. **Check the logs** thoroughly
2. **Search existing issues** on GitHub
3. **Create a detailed issue** with:
   - Error messages
   - Configuration (redact secrets)
   - Steps to reproduce
   - Environment details
   - Log snippets

### Issue Template

```
**Environment:**
- OS:
- Docker version:
- Docker Compose version:
- SeederBot version:

**Configuration:**
- Mode: radarr/blackhole
- External services: Radarr/Jackett versions

**Problem:**
Describe the issue...

**Steps to Reproduce:**
1. ...
2. ...

**Expected Behavior:**
What should happen...

**Actual Behavior:**
What actually happens...

**Logs:**
```
Relevant log snippets...
```
```

---

**Remember:** Most issues are configuration-related. Double-check your `.env` file and ensure all services are properly configured and accessible.