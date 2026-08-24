# 1. Rebuild the Docker image without cache
docker build --no-cache -t gurucool-api:v1 .

# 2. Stop and remove the old container
docker rm -f api

# 3. Run the container with host-gateway mapping to reach Ollama on your host machine
docker run -d \
  --name api \
  --network guru-net \
  --add-host=host.docker.internal:host-gateway \
  --restart unless-stopped \
  -p 8080:8000 \
  --env-file .env \
  gurucool-api:v1

# 4. Check application logs to confirm startup
docker logs -f api