# Deployment Guide - Task Management API

This guide covers various deployment options for the Task Management API.

## 🚀 Quick Deployment Options

### 1. **Local Development**
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python migrate.py migrate

# Start server
python -m app.main
```

### 2. **Docker Deployment**
```bash
# Quick start
docker-compose up --build

# Production with nginx
docker-compose --profile production up -d
```

### 3. **Production Server**
```bash
# Install with gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🐳 Docker Deployment (Recommended)

### Development Environment

```bash
# Build and start
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f taskapi

# Stop
docker-compose down
```

### Production Environment

```bash
# Start with nginx proxy
docker-compose --profile production up -d

# Scale API service
docker-compose up --scale taskapi=3 -d

# Check health
curl http://localhost/health
```

### Environment Variables

Create a `.env` file:

```env
# Database
DATABASE_URL=sqlite:///./data/tasks.db

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false
RELOAD=false

# Pagination
DEFAULT_PAGE_SIZE=100
MAX_PAGE_SIZE=1000
```

## ☁️ Cloud Deployment

### AWS Elastic Container Service (ECS)

1. **Build and push to ECR:**
```bash
# Build image
docker build -t task-management-api .

# Tag for ECR
docker tag task-management-api:latest <account>.dkr.ecr.<region>.amazonaws.com/task-api:latest

# Push to ECR
docker push <account>.dkr.ecr.<region>.amazonaws.com/task-api:latest
```

2. **Create ECS service with the image**

### Google Cloud Run

```bash
# Build and deploy
gcloud run deploy task-management-api \
  --source . \
  --port 8000 \
  --allow-unauthenticated \
  --region us-central1
```

### Azure Container Instances

```bash
# Create resource group
az group create --name task-api-rg --location eastus

# Deploy container
az container create \
  --resource-group task-api-rg \
  --name task-management-api \
  --image <your-registry>/task-management-api:latest \
  --ports 8000 \
  --environment-variables DATABASE_URL=sqlite:///./data/tasks.db
```

## 🔧 Production Configuration

### Nginx Configuration

For production, use nginx as a reverse proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Systemd Service

Create `/etc/systemd/system/task-api.service`:

```ini
[Unit]
Description=Task Management API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/task-api
ExecStart=/opt/task-api/venv/bin/gunicorn app.main:app --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable task-api
sudo systemctl start task-api
```

## 📊 Monitoring & Health Checks

### Health Check Endpoint

The API provides a health check at `/health`:

```bash
curl http://localhost:8000/health
```

### Docker Health Check

The Dockerfile includes health checks:

```dockerfile
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

### Application Metrics

Monitor these endpoints:
- `GET /health` - Basic health status
- `GET /tasks/statistics` - Application metrics
- `GET /admin/migrations/status` - Database status

## 🔒 Security Considerations

### Production Security

1. **Use HTTPS in production**
2. **Set proper CORS origins**
3. **Use environment variables for secrets**
4. **Regular security updates**
5. **Database backups**

### Example Secure Configuration

```python
# app/core/config.py
class Settings(BaseSettings):
    # Security
    allowed_hosts: List[str] = ["localhost", "your-domain.com"]
    cors_origins: List[str] = ["https://your-frontend.com"]
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    
    class Config:
        env_file = ".env"
```

## 🚨 Troubleshooting

### Common Issues

1. **Port conflicts:**
   ```bash
   # Check what's using port 8000
   netstat -an | grep 8000
   
   # Use different port
   uvicorn app.main:app --port 8001
   ```

2. **Database issues:**
   ```bash
   # Check migration status
   python migrate.py status
   
   # Reset database
   rm tasks.db
   python migrate.py migrate
   ```

3. **Docker issues:**
   ```bash
   # Rebuild without cache
   docker-compose build --no-cache
   
   # Check logs
   docker-compose logs taskapi
   ```

### Performance Tuning

1. **Database optimization:**
   - Migrations include performance indexes
   - Use `PRAGMA` settings for SQLite

2. **Application tuning:**
   ```python
   # Increase workers for production
   gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
   ```

3. **Caching:**
   - Add Redis for caching (if needed)
   - Use CDN for static assets

## 📝 Deployment Checklist

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Health checks working
- [ ] SSL/HTTPS configured (production)
- [ ] Monitoring setup
- [ ] Backup strategy implemented
- [ ] Security headers configured
- [ ] CORS origins set correctly
- [ ] Documentation accessible
- [ ] Load testing completed

## 🆘 Support

For deployment issues:
1. Check logs: `docker-compose logs taskapi`
2. Verify health: `curl http://localhost:8000/health`
3. Test endpoints: `python test_advanced_features.py`
4. Check migrations: `python migrate.py status` 