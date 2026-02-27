# Pushing SARG Docker Image to Docker Hub

## Prerequisites
1. Create a Docker Hub account at https://hub.docker.com if you don't have one
2. Your image should be built successfully (13.9GB in this case)

## Step-by-Step Guide

### 1. Login to Docker Hub
```bash
docker login
```
You'll be prompted for your Docker Hub username and password.

### 2. Tag Your Image
Replace `YOUR_DOCKERHUB_USERNAME` with your actual Docker Hub username:

```bash
docker tag sarg:dev YOUR_DOCKERHUB_USERNAME/sarg:latest
```

You can also create a versioned tag:
```bash
docker tag sarg:dev YOUR_DOCKERHUB_USERNAME/sarg:v1.0
```

### 3. Push to Docker Hub
```bash
docker push YOUR_DOCKERHUB_USERNAME/sarg:latest
```

If you created a version tag:
```bash
docker push YOUR_DOCKERHUB_USERNAME/sarg:v1.0
```

**Note:** This will take time (uploading ~14GB), but it's a one-time process.

### 4. Make Repository Public (Optional but Recommended for Team)
- Go to https://hub.docker.com
- Navigate to your repository
- Click Settings → Make Public

## For Your Teammates

### Quick Start (Pull Pre-built Image)
```bash
# Pull the image (much faster than building)
docker pull YOUR_DOCKERHUB_USERNAME/sarg:latest

# Start the container
docker compose up -d sarg-dev
docker exec -it sarg-research bash
```

### Full Setup Instructions

1. **Clone/Copy the SARG project:**
   ```bash
   git clone <your-repo-url>
   cd SARG
   ```

2. **Pull the pre-built image:**
   ```bash
   docker compose pull
   ```

3. **Start development environment:**
   ```bash
   docker compose up -d sarg-dev
   docker exec -it sarg-research bash
   ```

## Updating the Image

When you update dependencies or the Dockerfile:

1. **Rebuild locally:**
   ```bash
   docker compose build
   ```

2. **Tag with new version:**
   ```bash
   docker tag sarg:dev YOUR_DOCKERHUB_USERNAME/sarg:v1.1
   docker tag sarg:dev YOUR_DOCKERHUB_USERNAME/sarg:latest  # Update latest
   ```

3. **Push updates:**
   ```bash
   docker push YOUR_DOCKERHUB_USERNAME/sarg:v1.1
   docker push YOUR_DOCKERHUB_USERNAME/sarg:latest
   ```

4. **Notify team to pull updates:**
   ```bash
   docker compose pull
   docker compose up -d --force-recreate
   ```

## Alternative: GitHub Container Registry (ghcr.io)

If you prefer using GitHub instead of Docker Hub:

```bash
# Login to GitHub Container Registry
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Tag for GHCR
docker tag sarg:dev ghcr.io/YOUR_GITHUB_USERNAME/sarg:latest

# Push to GHCR
docker push ghcr.io/YOUR_GITHUB_USERNAME/sarg:latest
```

## Bandwidth Considerations

The image is ~14GB, so:
- **First push:** Will take 1-3 hours depending on your upload speed
- **Teammate pulls:** Will be faster (download is typically faster than upload)
- **Updates:** Only changed layers are pushed/pulled (much faster)

## Storage Limits

- **Docker Hub Free:** Unlimited public repositories, 6-month inactivity limit
- **Docker Hub Pro:** $5/month, removes limits
- **GitHub Container Registry:** Free for public repositories
