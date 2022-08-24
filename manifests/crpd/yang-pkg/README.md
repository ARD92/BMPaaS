# Optional Yang package

This package allows to query the DB as part of junos RPC call. i.e. The discovered devices can now be viewed as part of a show command on cRPD. 

## Steps to load package

## Ensure volume mounts
Ensure cRPD has the volume mounted with the same PVC as the consumer pod. The DB PVC would be mounted on cRPD as well under /mnt. This will ensure the package works as expected.

### Copy the folder to cRPD
```
kubectl cp yang-pkg -n discovery <crpd-pod>:/tmp
```

### Login to cRPD and navigate to the package
```
kubectl exec -it -n discovery <crpd-pod> bash

cd /tmp/yang-pkg
```

### Install
```
./install.sh
```
This will install the below 
- sqlite package which would be needed to query the DB
- yang package which creates the show command and the RPC call
- action script for the respective yang file which processes the data

## Notes
- Ensure the consumer pod volume is mounted to cRPD. i.e. both pods to share the PVC which hosts the database.
- consumer pod will perform write functions on the database
- cRPD RPC call will only perform read operations

### Verify

#### Verify package
```
root@crpd-f4556f7c-bwbpr> show system yang package
Package ID            :sc-discovery
YANG Module(s)        :sc-discovery.yang
Action Script(s)      :sc-discover_yang_action.py
Translation Script(s) :*
Translation script status is disabled
```
#### Verify volume mount

From shell check if DB is present
```
root@crpd-f4556f7c-bwbpr:/tmp/yang-pkg# ls -l /mnt/
total 288
-rw-r--r-- 1 root root 268785 Aug 24 04:20 sc-discovery.log
-rw-r--r-- 1 root root  20480 Aug 24 04:20 service_chain.db
```

#### Verify command
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
