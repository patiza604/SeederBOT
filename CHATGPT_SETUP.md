# ChatGPT Action Setup Guide 🤖

This guide explains how to integrate SeederBot with ChatGPT Actions for automated movie downloads through natural language requests.

## 📋 Prerequisites

1. **ChatGPT Plus subscription** (required for custom GPTs and Actions)
2. **SeederBot deployed** and accessible via HTTPS
3. **Valid SSL certificate** (Let's Encrypt recommended)
4. **API token** configured in SeederBot

## 🚀 Step-by-Step Setup

### Step 1: Deploy SeederBot with HTTPS

First ensure SeederBot is accessible via HTTPS:

```bash
# Update docker-compose.yml to use nginx proxy
docker-compose --profile proxy up -d

# Or deploy to a cloud provider with HTTPS
# Examples: Railway, Heroku, DigitalOcean, AWS, etc.
```

**Important**: ChatGPT Actions require HTTPS. HTTP endpoints will not work.

### Step 2: Create a New GPT

1. Go to [ChatGPT](https://chat.openai.com/)
2. Click on your profile → "My GPTs"
3. Click "Create a GPT"
4. Choose "Configure" tab

### Step 3: Configure Basic GPT Settings

Fill in the GPT configuration:

**Name:**
```
SeederBot - Movie Downloads
```

**Description:**
```
Automatically download movies through your personal media server. Searches for high-quality torrents and manages downloads through Radarr and Jackett.
```

**Instructions:**
```
You are SeederBot, a helpful assistant that manages movie downloads for a personal media server.

When users request movies:
1. Extract the movie title and year (if provided)
2. Use the /grab endpoint to initiate downloads
3. Confirm successful additions or explain any errors
4. Be helpful and conversational

Example interactions:
- "Download Inception from 2010" → Call grab with {"title": "Inception", "year": 2010}
- "Get the latest Dune movie" → Call grab with {"title": "Dune", "year": 2021}
- "Add The Matrix to my collection" → Call grab with {"title": "The Matrix"}

Always:
- Confirm what movie you're downloading
- Explain the download process briefly
- Handle errors gracefully
- Remind users about legal compliance

Never:
- Download copyrighted content without permission
- Bypass geographic restrictions
- Ignore rate limits or abuse the service
```

**Conversation starters:**
```
Download Inception (2010)
Get Dune: Part Two
Add The Matrix trilogy
What movies can you download?
```

### Step 4: Configure the Action

1. Scroll down to "Actions" section
2. Click "Create new action"
3. Set up the action schema:

#### Import OpenAPI Schema

**Option A: Direct Import**
```
https://your-domain.com/openapi.json
```

**Option B: Copy-Paste Schema**
Copy the contents from `ops/openapi/seederbot.json` and paste into the schema editor.

#### Authentication Setup

1. Select "Authentication Type": **API Key**
2. Set "Auth Type": **Bearer**
3. Enter your SeederBot API token in the "API Key" field
4. Set "Custom Header Name": `Authorization`
5. Set "Custom Header Value": `Bearer YOUR_TOKEN_HERE`

### Step 5: Test the Integration

1. Click "Test" in the Actions section
2. Try a sample request:
   ```json
   {
     "title": "Inception",
     "year": 2010
   }
   ```
3. Verify the response is successful

### Step 6: Save and Test with Natural Language

1. Save your GPT configuration
2. Start a conversation with your GPT
3. Test with natural language:
   - "Download Blade Runner 2049"
   - "Add Interstellar to my collection"
   - "Get the movie Dune from 2021"

## 🎯 Usage Examples

### Basic Movie Requests

**User:** "Download Inception"
**GPT Response:** "I'll download Inception for you! Let me search for the best quality version..."
*[Calls API with {"title": "Inception"}]*
**GPT Response:** "✅ Successfully added 'Inception (2010)' to your download queue! The system will automatically find and download the best quality version."

### Year-Specific Requests

**User:** "Get the 2021 Dune movie"
**GPT Response:** "Downloading Dune (2021)..."
*[Calls API with {"title": "Dune", "year": 2021}]*
**GPT Response:** "✅ Added 'Dune (2021)' to downloads! Found a high-quality 1080p version with good seeders."

### Error Handling

**User:** "Download a movie that doesn't exist"
**GPT Response:** "I tried to find that movie but couldn't locate any suitable torrents. This could mean:
- The movie title might be misspelled
- It might not be available on configured indexers
- Quality filters might be too restrictive

Would you like to try a different title or check the spelling?"

## 🔧 Advanced Configuration

### Custom Instructions

You can enhance the GPT with more specific instructions:

```
Additional Context:
- Your media server runs Radarr and uses Jackett for torrent indexing
- Quality preferences: 1080p WEB-DL or BluRay, 2.5-6GB file size
- Minimum 20 seeders required for downloads
- AutoAdd configured for blackhole mode fallback

User Preferences:
- Prefer recent releases and good quality
- Avoid CAM/TS/Workprint versions
- Freeleech torrents are preferred when available

Error Handling:
- If no torrents found, suggest checking indexer configuration
- For authentication errors, mention checking API token
- For network errors, suggest checking service status
```

### Privacy and Safety

Add safety guidelines:

```
Safety Guidelines:
- Only process requests for movies the user legally owns or is authorized to download
- Respect copyright laws and user's local regulations
- Don't provide assistance with bypassing geo-restrictions
- Remind users about maintaining proper torrent ratios
- Suggest using VPNs where appropriate for privacy
```

## 🛡️ Security Best Practices

### API Token Security

1. **Generate strong tokens**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Use environment variables**:
   ```bash
   APP_TOKEN=your-super-secure-token-here
   ```

3. **Rotate tokens regularly** (monthly recommended)

4. **Monitor API usage** in SeederBot logs

### Network Security

1. **Use HTTPS only** - ChatGPT requires SSL
2. **Configure rate limiting** in nginx:
   ```nginx
   limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
   limit_req zone=api burst=20 nodelay;
   ```

3. **Restrict access** by IP if possible:
   ```nginx
   allow 52.230.152.0/24;  # ChatGPT IP ranges
   allow 13.66.11.0/24;
   deny all;
   ```

### Monitoring

Monitor your SeederBot logs for:
- Authentication failures
- Unusual request patterns
- Error rates
- Response times

```bash
# Monitor API usage
docker-compose logs -f seederbot | grep "Grab request"

# Check for auth failures
docker-compose logs seederbot | grep "401"
```

## 🐛 Troubleshooting

### Common Issues

#### "Action not working" / No response
- **Check HTTPS**: Ensure SeederBot uses valid SSL certificate
- **Verify API token**: Test manually with curl
- **Check logs**: Look for errors in SeederBot logs

#### "Authentication failed"
- **Token mismatch**: Verify token in ChatGPT matches .env
- **Header format**: Ensure "Bearer TOKEN" format is used
- **Token expiry**: Generate new token if needed

#### "Service unavailable"
- **Check deployment**: Ensure SeederBot is running
- **Network access**: Verify ChatGPT can reach your server
- **Firewall rules**: Check if ports are accessible

### Testing Commands

```bash
# Test health endpoint
curl https://your-domain.com/health

# Test grab endpoint
curl -X POST https://your-domain.com/grab \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Movie", "year": 2020}'

# Check SSL certificate
curl -I https://your-domain.com/health
```

### Debug Mode

Enable debug logging in SeederBot:

```yaml
# docker-compose.yml
environment:
  - LOG_LEVEL=DEBUG
```

## 📊 Usage Analytics

Track your ChatGPT Action usage:

1. **Monitor request logs**:
   ```bash
   docker-compose logs seederbot | grep "ChatGPT"
   ```

2. **Set up metrics** (optional):
   - Prometheus + Grafana
   - Simple log analysis
   - Request counting

3. **Performance monitoring**:
   - Response times
   - Success rates
   - Error patterns

## 🔄 Updates and Maintenance

### Updating the Action

When you update SeederBot:

1. **Update OpenAPI schema** if API changes
2. **Test with ChatGPT** after updates
3. **Monitor for new errors** post-deployment
4. **Update GPT instructions** if needed

### Schema Versioning

Consider versioning your API:

```yaml
# In OpenAPI spec
info:
  version: "1.0.0"
```

This helps track compatibility with ChatGPT Actions.

## 🎉 Success!

Once configured, you can now:

- Ask ChatGPT to download movies naturally
- Get automatic quality selection and filtering
- Receive status updates and error handling
- Enjoy seamless integration with your media server

**Example conversation:**
```
You: "Add Interstellar to my Plex library"
ChatGPT: "I'll download Interstellar for you! 🎬"
[Downloads high-quality version automatically]
ChatGPT: "✅ Successfully added Interstellar (2014) to your download queue!
The system found a 1080p BluRay version with 45 seeders.
It should appear in your Plex library once the download completes."
```

---

**Legal Reminder**: Ensure all downloads comply with your local laws and you have appropriate rights to the content. SeederBot is for personal use with legally owned media only.