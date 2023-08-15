#!/bin/bash


# Pull latest changes from the repository
git pull origin main

# Full path to the 'docker' executable
DOCKER_EXECUTABLE=/usr/bin/docker

echo "PATH: $PATH"
echo "DOCKER_EXECUTABLE: $DOCKER_EXECUTABLE"

# Rebuild the Docker image
$DOCKER_EXECUTABLE build -t yt-api .

# Stop and remove the existing container
$DOCKER_EXECUTABLE stop yt-api-container
$DOCKER_EXECUTABLE rm yt-api-container

# Run the updated container
$DOCKER_EXECUTABLE run -d --name yt-api-container -p 5000:5000 yt-api
