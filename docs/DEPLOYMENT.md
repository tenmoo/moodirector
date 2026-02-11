# Moo Director - Deployment Guide

This guide covers deploying the Moo Director to production.

## Overview

| Component | Recommended Platform | Alternative |
|-----------|---------------------|-------------|
| Backend | Fly.io | AWS, GCP, Railway |
| Frontend | Vercel | Netlify, Cloudflare Pages |

## Prerequisites

- Git repository with your code
- Accounts on deployment platforms:
  - [Fly.io](https://fly.io) for backend
  - [Vercel](https://vercel.com) for frontend
- Groq API key for production

---

## Backend Deployment (Fly.io)

### Step 1: Install Fly CLI

**macOS:**
```bash
brew install flyctl
```

**Linux:**
```bash
curl -L https://fly.io/install.sh | sh
```

**Windows:**
```powershell
pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### Step 2: Login to Fly.io

```bash
fly auth login
```

### Step 3: Create fly.toml

Create `backend/fly.toml`:

```toml
app = "moo-director-api"
primary_region = "sjc"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8000"
  HOST = "0.0.0.0"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512
```

### Step 4: Set Secrets

```bash
cd backend

# Set your Groq API key
fly secrets set GROQ_API_KEY=your_groq_api_key

# Set JWT secret (generate a secure key)
fly secrets set SECRET_KEY=$(openssl rand -hex 32)

# Optional: Enable LangSmith tracing in production
fly secrets set LANGCHAIN_API_KEY=your_langsmith_api_key
fly secrets set LANGCHAIN_TRACING_V2=true
fly secrets set LANGCHAIN_PROJECT=moo-director-prod
```

### Step 5: Deploy

```bash
fly launch --no-deploy  # First time: configure app
fly deploy              # Deploy the app
```

### Step 6: Verify Deployment

```bash
# Check status
fly status

# View logs
fly logs

# Test the API
curl https://moo-director-api.fly.dev/api/v1/health
```

### Scaling (Optional)

```bash
# Scale to multiple regions
fly regions add iad  # Add US East

# Scale memory
fly scale memory 1024  # 1GB RAM

# Scale VM
fly scale vm shared-cpu-2x
```

---

## Frontend Deployment (Vercel)

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2: Login to Vercel

```bash
vercel login
```

### Step 3: Create vercel.json

Create `frontend/vercel.json`:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://moo-director-api.fly.dev/api/:path*"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

### Step 4: Update API Client

Update `frontend/src/api/client.ts` for production:

```typescript
const API_BASE_URL = import.meta.env.PROD 
  ? '/api/v1'  // Uses Vercel rewrite
  : '/api/v1'; // Uses Vite proxy
```

### Step 5: Deploy

```bash
cd frontend

# First deployment
vercel

# Production deployment
vercel --prod
```

### Step 6: Configure Environment Variables

In Vercel Dashboard:
1. Go to your project settings
2. Navigate to "Environment Variables"
3. Add any necessary variables

---

## Alternative: Docker Compose (Self-Hosted)

For self-hosted deployments:

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - HOST=0.0.0.0
      - PORT=8000
      # Optional: LangSmith
      - LANGCHAIN_TRACING_V2=${LANGCHAIN_TRACING_V2:-false}
      - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY:-}
      - LANGCHAIN_PROJECT=${LANGCHAIN_PROJECT:-moo-director}
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
```

### Frontend Dockerfile

Create `frontend/Dockerfile`:

```dockerfile
# Build stage
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Deploy

```bash
# Set environment variables
export GROQ_API_KEY=your_key
export SECRET_KEY=$(openssl rand -hex 32)

# Build and run
docker-compose up -d --build
```

---

## Environment Configuration

### Production Environment Variables

**Backend:**
| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key |
| `SECRET_KEY` | Yes | JWT signing key (32+ chars) |
| `HOST` | No | Server host (default: 0.0.0.0) |
| `PORT` | No | Server port (default: 8000) |
| `DEBUG` | No | Debug mode (default: false) |
| `DEFAULT_MODEL` | No | LLM model (default: llama-3.3-70b-versatile) |
| `LANGCHAIN_TRACING_V2` | No | Enable LangSmith tracing (default: false) |
| `LANGCHAIN_API_KEY` | No | LangSmith API key |
| `LANGCHAIN_PROJECT` | No | LangSmith project name (default: moo-director) |

**Frontend:**
| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | No | API URL (uses rewrite in prod) |

---

## SSL/HTTPS

### Fly.io
SSL is automatically provided via Fly.io's edge network.

### Vercel
SSL is automatically provided via Vercel's edge network.

### Self-Hosted
Use Let's Encrypt with Certbot:

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com
```

---

## Monitoring & Logging

### Fly.io Logging

```bash
# Real-time logs
fly logs

# Historical logs
fly logs --since 1h
```

### Vercel Logging
View logs in Vercel Dashboard → Project → Logs

### Health Checks

Set up monitoring for:
```
GET https://your-api.fly.dev/api/v1/health
```

Expected response:
```json
{"status": "healthy", "service": "moo-director"}
```

### Recommended Monitoring Tools
- **Uptime**: UptimeRobot, Pingdom
- **APM**: Sentry, DataDog
- **Logs**: LogDNA, Papertrail
- **LLM Observability**: LangSmith (included - configure with `LANGCHAIN_API_KEY`)

---

## Security Checklist

- [ ] Strong `SECRET_KEY` (32+ random characters)
- [ ] `GROQ_API_KEY` stored as secret (not in code)
- [ ] HTTPS enabled (automatic on Fly.io/Vercel)
- [ ] CORS configured for production domain only
- [ ] Rate limiting configured (optional)
- [ ] Debug mode disabled in production

---

## Rollback

### Fly.io

```bash
# List releases
fly releases

# Rollback to previous version
fly releases rollback
```

### Vercel

1. Go to Vercel Dashboard
2. Navigate to Deployments
3. Click on a previous deployment
4. Click "Promote to Production"

---

## Cost Estimates

### Fly.io (Backend)
- **Free tier**: 3 shared-cpu-1x VMs, 160GB bandwidth
- **Production**: ~$5-10/month for 1 always-on VM

### Vercel (Frontend)
- **Free tier**: 100GB bandwidth, unlimited deployments
- **Pro tier**: $20/month for team features

### Groq API
- **Free tier**: Rate limited
- **Production**: Pay-as-you-go based on token usage

### LangSmith (Optional)
- **Free tier**: 5,000 traces/month, 14-day retention
- **Plus tier**: $39/month for more traces and features

---

## Troubleshooting

### Backend not starting

```bash
# Check logs
fly logs

# SSH into VM
fly ssh console

# Check environment
fly secrets list
```

### Frontend API calls failing

1. Check Vercel rewrites configuration
2. Verify backend URL in vercel.json
3. Check browser console for CORS errors
4. Verify backend is running: `curl your-api.fly.dev/api/v1/health`

### Slow cold starts

On Fly.io, increase `min_machines_running` in fly.toml:
```toml
[http_service]
  min_machines_running = 1
```

---

## Updating Deployments

### Backend

```bash
cd backend
fly deploy
```

### Frontend

```bash
cd frontend
vercel --prod
```

Or push to Git if you've connected Vercel to your repository.
