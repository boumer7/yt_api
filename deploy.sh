
# Pull latest changes from the repository
git pull

# Rebuild the Docker image
docker build -t yt-api .

# Stop and remove the existing container
docker stop yt-api-container
docker rm yt-api-container

# Run the updated container
docker run -d --name yt-api-container -p 5000:5000 yt-api
