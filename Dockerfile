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

# Copy project
COPY . .

# Create weekly cron job: Friday at 00:00
RUN echo "0 0 * * 5 python3 /app/main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/weeklyjob \
    && chmod 0644 /etc/cron.d/weeklyjob \
    && crontab /etc/cron.d/weeklyjob

# Environment variables for Selenium
ENV PATH="/usr/lib/chromium/:$PATH"
ENV CHROME_BIN="/usr/bin/chromium"

# Run main.py at startup, then start cron in foreground
CMD ["bash", "-c", "python3 /app/main.py && cron -f"]
