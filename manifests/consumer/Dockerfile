# Dockerfile for consumer app container
FROM alpine:latest
WORKDIR /opt
RUN apk add --no-cache python3 py3-pip sqlite
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY sc-consumer.py ./
CMD ["python3", "sc-consumer.py"]
