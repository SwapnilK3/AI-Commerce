FROM node:18-slim

# Install only the minimal deps Puppeteer needs + Chromium
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Tell Puppeteer to use system Chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

WORKDIR /app

# Copy ONLY package.json first — this layer is cached unless deps change
COPY package.json .
RUN npm install --cache /root/.npm

# Copy app code (changes here won't re-trigger npm install)
COPY index.js .

# Session data folder (mount as volume for persistence)
RUN mkdir -p session_data

EXPOSE 3001

CMD ["node", "index.js"]
