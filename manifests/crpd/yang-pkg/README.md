# Optional Yang package

This package allows to query the DB as part of junos RPC call. i.e. The discovered devices can now be viewed as part of a show command on cRPD. 

## Steps to load package

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

