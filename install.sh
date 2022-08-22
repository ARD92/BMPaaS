# Install package
#namespace
kubectl apply -f manifests/namespace.yaml
#cRPD
kubectl apply -f manifests/crpd/sc-crpd.yaml
kubectl apply -f manifests/crpd/crpd-pvc.yaml
#Kafka and zookeeper
kubectl apply -f manifests/kafka/sc-zookeeper.yaml
kubectl apply -f manifests/kafka/sc-kafka.yaml
#Consumer
docker build -t consumer:latest -f /manifests/consumer/Dockerfile
kubectl apply -f manifests/consumer/sc-consumer.yaml
kubectl apply -f manifests/consumer/consumer-pvc.yaml
