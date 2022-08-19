FROM alpine:latest
RUN apk add --no-cache python3 py3-pip sqlite runit
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /etc/runit/sc-consumer/
ADD ./run-sc-consumer /etc/runit/sc-consumer/run
RUN chmod +x /etc/runit/sc-consumer/run
RUN ln -s /etc/runit/sc-consumer/ /etc/service/sc-consumer

COPY sc-consumer.py /var/opt/sc-consumer.py
RUN chmod -R 777 /var/opt/sc-consumer.py
CMD ["python3", "/var/opt/sc-consumer.py"]
