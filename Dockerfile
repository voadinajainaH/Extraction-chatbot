FROM python:3.12.1-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies + cron + chromium
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        cron \
        # chromium \
        chromium-driver \
        wget \
        curl \
        unzip \
        python3-pip && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# RUN python -m nltk.downloader punkt averaged_perceptron_tagger

# Copy app files
COPY extraction.py .
COPY aaa ./aaa
# COPY data.json .

# Cron job every 30 min for testing
RUN echo "0 3 * * * root cd /app && /usr/local/bin/python /app/extraction.py >> /var/log/extraction.log 2>&1" \
    > /etc/cron.d/extraction-cron \
    && chmod 0644 /etc/cron.d/extraction-cron \
    && crontab /etc/cron.d/extraction-cron \
    && touch /var/log/extraction.log

# Entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
