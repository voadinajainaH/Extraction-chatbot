#!/bin/bash
echo "Starting cron service..."
service cron start
echo "Cron service started. Logs at /var/log/extraction.log"
tail -F /var/log/extraction.log
