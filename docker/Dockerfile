FROM python:3.9-slim

# Install Node.js and npm
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Mosquitto MQTT broker
RUN apt-get update && apt-get install -y \
    mosquitto \
    mosquitto-clients \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /run/mosquitto \
    && chown mosquitto:mosquitto /run/mosquitto

# Install Node-RED and dashboard nodes
RUN npm install -g --unsafe-perm node-red node-red-dashboard

# Set working directory
WORKDIR /app

# Copy package files and install Node-RED dependencies
COPY node-red/package.json node-red/package-lock.json ./
RUN npm install

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Mosquitto configuration
COPY config/mosquitto.conf /etc/mosquitto/conf.d/

# Copy application code
COPY . .

# Expose ports
EXPOSE 1880 1883 9001

# Copy and set permissions for entrypoint script
COPY docker/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Start services
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD [""]
