FROM ubuntu:22.04

# Install necessary packages
RUN apt-get update && apt-get install -y \
    socat \
    && rm -rf /var/lib/apt/lists/*

# Create ubuntu user
RUN useradd -m -s /bin/bash ubuntu

# Set working directory
WORKDIR /home/ubuntu

# Copy the dist files
COPY dist/ /home/ubuntu/dist/

# Set permissions
RUN chown -R ubuntu:ubuntu /home/ubuntu

USER ubuntu