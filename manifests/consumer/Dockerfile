# Dockerfile for consumer
FROM alpine:latest
WORKDIR /
RUN apk add --no-cache python3 py3-pip sqlite
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
CMD []
