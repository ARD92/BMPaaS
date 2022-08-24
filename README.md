# BMPaaS
Using BMP as a service

Using BMP has many advantages in terms of looking glass and monitoring capabilities. The behavior of BMP has been captured [here](https://ard92.github.io/2022/08/04/BMP_RFC7954.html)
One can use these BMP messages to transform into meaningful data. This repo contains an example to discover service chains. 
The service routes of the service chain element are advertised with a BGP community. This community is monitored from the BMP message and then later stored in the database.
The database itself contains 2 tables 
- SC_BMP_INIT (BMP client information which provides information such as location, client id )
- SC_BMP_TLV (service chain service address information. Trust side interface , untrust side interface IP of the firewall/service chain)

Together with this one can derive information and feed it to other applications such as website which can read from DB. 
In this example, SQLite DB is used because of ease of use and simplicity. 

## Quick steps to test

### Clone the repo
```
git clone https://github.com/ARD92/BMPaaS.git
```
### Bring up the topology 
Use crpd-topology-builder to bring up a test topology.
The tool can be found [here](https://github.com/ARD92/crpd-topology-builder)

```
(venv) root@k8s-master:/home/aprabh/crpd-topology-builder# python topo_builder/topo_builder.py -a create -t topologies/bmp.yml
+-----------------------------------------------------------------------+
|           container topology builder                                  |
+-----------------------------------------------------------------------+
| Usage: ./topo_builder.py -a create/delete/config/backup -t <yml file> |
|  In case you want to pass common initial configuration                |
|  to all containers then. issue the below command to all               |
|                                                                       |
|  In case you want to delete the created volumes pass -f flag.         |
|  Only applicable when issuing the delete action.                      |
|                                                                       |
|./topo_builder.py -a config -t <yml file> -cfg <config.txt>            |
|                                                                       |
| In case you want to configure different containers with               |
| with different configuration files then issue the below.              |
|                                                                       |
| ./topo_builder.py -a config -c <container name> -cfg <file>           |
|                                                                       |
| ./topo_builder.py -a backup -c <container name>   to backup single    |
| ./topo_builder.py -a backup -t <yml file> to backup all               |
|    For general help: ./topo_builder.py --help                         |
|  Log file would be generated in cwd as topo_creator.log               |
+-----------------------------------------------------------------------+
 ********** Creating topology *************
entered container spe1
entered container sc1
entered container spe1
entered container sc1
entered container spe1
entered container sc2
entered container spe1
entered container sc2
entered container spe2
entered container sc3
entered container spe2
entered container sc3
entered container spe2
entered container sc4
entered container spe2
entered container sc4
entered container spe3
entered container sc5
entered container spe3
entered container sc5
entered container spe3
entered container sc6
entered container spe3
entered container sc6
```
### Configure the nodes 
you can run the below command to load the containers with necessary config. Note that cRPD license would be required for BGP to come up. 

```
(venv) root@k8s-master:/home/aprabh/crpd-topology-builder# python topo_builder/topo_builder.py -a config -c <container name> -cfg <backup_filename.txt>
```
The configs can be found [here](https://github.com/ARD92/crpd-topology-builder/tree/master/configs/bmp)

### Setup the discovery app
Ensure this is run on a kubernetes cluster
```
./install.sh
```

## Verify

### Topology related
```
root@k8s-master:/home/aprabh/crpd-topology-builder# docker ps | grep spe
521ce1fb4112   crpd:latest            "/sbin/runit-init.sh"    39 hours ago   Up 39 hours   179/tcp, 3784/tcp, 4784/tcp, 6784/tcp, 7784/tcp, 50051/tcp, 0.0.0.0:49295->22/tcp, :::49293->22/tcp, 0.0.0.0:49294->830/tcp, :::49292->830/tcp, 0.0.0.0:49293->40051/tcp, :::49291->40051/tcp   spe3
40397d074cec   crpd:latest            "/sbin/runit-init.sh"    39 hours ago   Up 39 hours   179/tcp, 3784/tcp, 4784/tcp, 6784/tcp, 7784/tcp, 50051/tcp, 0.0.0.0:49292->22/tcp, :::49290->22/tcp, 0.0.0.0:49291->830/tcp, :::49289->830/tcp, 0.0.0.0:49290->40051/tcp, :::49288->40051/tcp   spe2
c4a8ddd31487   crpd:latest            "/sbin/runit-init.sh"    39 hours ago   Up 39 hours   179/tcp, 3784/tcp, 4784/tcp, 6784/tcp, 7784/tcp, 50051/tcp, 0.0.0.0:49289->22/tcp, :::49287->22/tcp, 0.0.0.0:49287->830/tcp, :::49286->830/tcp, 0.0.0.0:49285->40051/tcp, :::49285->40051/tcp   spe1
root@k8s-master:/home/aprabh/crpd-topology-builder# docker ps | grep sc
486fe142b38c   crpd:latest            "/sbin/runit-init.sh"    39 hours ago   Up 39 hours   179/tcp, 3784/tcp, 4784/tcp, 6784/tcp, 7784/tcp, 50051/tcp, 0.0.0.0:49313->22/tcp, :::49311->22/tcp, 0.0.0.0:49312->830/tcp, :::49310->830/tcp, 0.0.0.0:49311->40051/tcp, :::49309->40051/tcp   sc6
fb1aa4ec2807   crpd:latest            "/sbin/runit-init.sh"    39 hours ago   Up 39 hours   179/tcp, 3784/tcp, 4784/tcp, 6784/tcp, 7784/tcp, 50051/tcp, 0.0.0.0:49310->22/tcp, :::49308->22/tcp, 0.0.0.0:49309->830/tcp, :::49307->830/tcp, 0.0.0.0:49308->40051/tcp, :::49306->40051/tcp   sc5
0b3d66e9df42   crpd:latest            "/sbin/runit-init.sh"    39 hours ago   Up 39 hours   179/tcp, 3784/tcp, 4784/tcp, 6784/tcp, 7784/tcp, 50051/tcp, 0.0.0.0:49307->22/tcp, :::49305->22/tcp, 0.0.0.0:49306->830/tcp, :::49304->830/tcp, 0.0.0.0:49305->40051/tcp, :::49303->40051/tcp   sc4
c0439f3a2a57   crpd:latest            "/sbin/runit-init.sh"    39 hours ago   Up 39 hours   179/tcp, 3784/tcp, 4784/tcp, 6784/tcp, 7784/tcp, 50051/tcp, 0.0.0.0:49304->22/tcp, :::49302->22/tcp, 0.0.0.0:49303->830/tcp, :::49301->830/tcp, 0.0.0.0:49302->40051/tcp, :::49300->40051/tcp   sc3
f7d40c52e756   crpd:latest            "/sbin/runit-init.sh"    39 hours ago   Up 39 hours   179/tcp, 3784/tcp, 4784/tcp, 6784/tcp, 7784/tcp, 50051/tcp, 0.0.0.0:49301->22/tcp, :::49299->22/tcp, 0.0.0.0:49300->830/tcp, :::49298->830/tcp, 0.0.0.0:49299->40051/tcp, :::49297->40051/tcp   sc2
dde1080a0f39   crpd:latest            "/sbin/runit-init.sh"    39 hours ago   Up 39 hours   179/tcp, 3784/tcp, 4784/tcp, 6784/tcp, 7784/tcp, 50051/tcp, 0.0.0.0:49298->22/tcp, :::49296->22/tcp, 0.0.0.0:49297->830/tcp, :::49295->830/tcp, 0.0.0.0:49296->40051/tcp, :::49294->40051/tcp   sc1
ffb9e58f7a7c   ed0ccfa052ab           "kube-scheduler --au…"   2 months ago   Up 2 months
```

### K8s setup
```
root@k8s-master:/home/aprabh/crpd-topology-builder# k get pods -n discovery
NAME                           READY   STATUS    RESTARTS   AGE
consumer-76c57d77d5-kgj2h      1/1     Running   0          40h
crpd-749558787c-jmzmf          1/1     Running   0          8d
kafka-687579d-92jzx            1/1     Running   0          4d21h
zookeeper-2-57dd75f449-vsnrd   1/1     Running   0          4d21h
zookeeper-8546b5ccfb-qqt5q     1/1     Running   0          4d21h
```
Ensure that kafka and zookeeper hit no exceptions with service connectivity. Else, data would not get published. 
you can check logs 

```
kubectl logs <pod name> -n discovery
```
### Configure BMP station

Enter the pod. This part can be automated using config maps.

```
root@k8s-master:/home/aprabh/crpd-topology-builder# k exec -it crpd-749558787c-jmzmf -n discovery cli
kubectl exec [POD] [COMMAND] is DEPRECATED and will be removed in a future version. Use kubectl exec [POD] -- [COMMAND] instead.
```
#### Load config
```
set routing-options bmp traceoptions file bmp.log
set routing-options bmp traceoptions file size 3g
set routing-options bmp traceoptions flag event
set routing-options bmp station SC-DISCOVERY local-port 17002
set routing-options bmp station SC-DISCOVERY station-address 10.244.0.0
set routing-options bmp station SC-DISCOVERY bmp-server
set routing-options bmp station SC-DISCOVERY kafka broker-address kafka:9092
commit
```

### BMP related
```
root@crpd-749558787c-jmzmf> show bgp bmp
Station name: SC-DISCOVERY
  Local address/port: -/17002, Station address/port: 10.244.0.0/-, passive
  State: listening
  Last state change: 1w0d 8:38:38
  Hold-down: 600, flaps 3, period 300
  Priority: low
  BMP server: enabled
  Clients count (current/max): 7/20
  Version: 3
  Routing Instance: default
  Trace options: event
  Trace file: /var/log//bmp.log size 3221225472 files 10
  Kafka broker address: kafka:9092, status: Up, elapsed time: 4d 21:06:22
  BMP server connected clients:
    Remote sysname: la06emd address/port: 10.244.1.1+28279, up time: 12:18:57
    Remote sysname: md04emd address/port: 10.244.1.1+8036, up time: 12:18:33
    Remote sysname: nj01emd address/port: 10.244.1.1+23551, up time: 12:17:33
```

#### View statistics
```
root@crpd-749558787c-jmzmf> show bgp bmp statistics kafka
Producer:
  Name: juniper.bmp-server#producer-1
  Current number of messages in queues:                                       0
  Current total bytes of messages in queues:                                  0

Broker:
  Name: 10.85.47.166:31092/1
  State: UP
  Total number of requests sent:                                          11092
  Total number of bytes sent:                                           4903095
  Total number of requests timed out:                                         2

Topics:

  Name                      Messages Tx/Queued                   Bytes Tx/Queued

  bmp-init                                42/0                           18736/0
  bmp-peer                               658/0                          490250/0
  bmp-rm-unicast                         794/0                         1547474/0
  bmp-rm-tlv                             465/0                          604752/0
  bmp-stats                             2366/0                         1289330/0
  bmp-term                                37/0                           12057/0
```

### SQL commands 

sqlite3 <dbname>
```
sqlite> SELECT * FROM SC_BMP_INIT;
10.244.1.1|ny|Juniper Networks|01emd

sqlite> SELECT * FROM SC_BMP_TLV;
10.244.1.1|100.1.1.2|10.10.10.12/32|Untrust
10.244.1.1|100.1.1.2|10.10.10.13/32|Trust
10.244.1.1|100.1.1.2|10.10.10.11/32|Trust

sqlite> SELECT * FROM SC_BMP_INIT left join SC_BMP_TLV on SC_BMP_INIT.bmp_client_id=SC_BMP_TLV.bmp_client_id;
10.244.1.1|ny|Juniper Networks|01emd|10.244.1.1|100.1.1.2|10.10.10.11/32|Trust
10.244.1.1|ny|Juniper Networks|01emd|10.244.1.1|100.1.1.2|10.10.10.12/32|Untrust
10.244.1.1|ny|Juniper Networks|01emd|10.244.1.1|100.1.1.2|10.10.10.13/32|Trust
```

## Optional Yang package
Optional yang package is available to view the discovered service chain elements. This needs to be installed on cRPD.
Follow the steps under manifests/crpd/yang-pkg

This will give an option to use a "show" command which queries the DB for the results.

```
root@crpd-f4556f7c-bwbpr> show service-chain discovered
		Location	: nj
		Vendor	  	: Juniper Networks
		Peer IP	  	: 1.1.1.1
		Device ID	: 01emd
		Service IP	: 21.21.21.21/32
		Service IP Type : Trust

		Location	: nj
		Vendor	  	: Juniper Networks
		Peer IP	  	: 1.1.1.1
		Device ID	: 01emd
		Service IP	: 31.31.31.0/30
		Service IP Type : Trust
```
