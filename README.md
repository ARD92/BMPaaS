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

## Verify
### SQL commands 

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

