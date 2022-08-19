#!/usr/bin/python

# Author: aprabh@juniper.net
# Version: 1.0
# Description: Kafka consumer app to parse BGP messages and store 
#              them into a SQLite DB with necessary params.
#              The params include (hostname, untrust interface IP, trust Interface IP)

import sqlite3
import kafka
import concurrent.futures
import json
from kafka import KafkaConsumer
from kafka import KafkaProducer
from sqlite3 import Error
from concurrent.futures import ThreadPoolExecutor

# Supported kafka topics from cRPD
kafka_topics = ["bmp-init", "bmp-peer", "bmp-rm-unicast", "bmp-term", "bmp-rm-tlv", "bmp-stats"]

# Connection detail. Kafka service is used hence no need for IP
KAFKA_BOOTSTRAP_SERVERS_CONS = 'kafka:9092'

# Sqlite DB to store discovered information
DB_FILE = '/opt/discovery.db'

# List of communtiies for trust and untrust
TRUST_COMMUNITIES = ["13979:100"]
UNTRUST_COMMUNITIES = ["13979:200"]

# Create database and connection
#def createConnection(DB_FILE):
#    """
#    Create a database connection and create the DB if not present.
#    """
#    conn = None
#    try:
#        conn = sqlite3.connect(DB_FILE)
#        print(sqlite3.version)
#    except Error as e:
#        print(e)
#    finally:
#        if conn:
#            conn.close()


# Create table 
def sqliteTableAdd(DB_FILE):
    """
    Create the table if it doesnt exist. If it exists, reuse the table.
    """
    connection = sqlite3.connect(DB_FILE)
    connection.execute("CREATE TABLE IF NOT EXISTS SC_BMP_INIT (bmp_client_id TEXT,location TEXT,vendor TEXT,device_id TEXT);")
    connection.execute("CREATE TABLE IF NOT EXISTS SC_BMP_TLV (bmp_client_id TEXT,peerip TEXT,interface_ips TEXT,ip_type TEXT);")
    print("SC_BMP_INIT and SC_BMP_TLV table added...")
    connection.commit()
    connection.close()


# Insert into table
def sqlliteInsertData(bmp_client_id, tabletype, data):
    """
    Insert data into the table. The data typically contains if the service chain element is present
    or not. we need the same params as the input to the function definition. The names are self 
    explanatory.
    Use inner joins to correlate based on primary key bmp_client_id
    """
    print("inserting data into table")
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    if tabletype == "SC_BMP_INIT":
        cursor.execute("INSERT INTO SC_BMP_INIT VALUES (?, ?, ?, ?)", (bmp_client_id,data[0],data[1],data[2]))
        connection.commit()
        print("New BMP client details added")
    elif tabletype == "SC_BMP_TLV":
        # data = [peer_ip, interface_ips, ip_type]
        print(data)
        cursor.execute("INSERT INTO SC_BMP_TLV VALUES (?, ?, ?, ?)", (bmp_client_id,data[0],data[1],data[2]))
        connection.commit()
        print("New service chain update added")
    connection.close()


# Update data in table
# WIP!! Do not use this yet
def sqlliteUpdateData(peer_ip, tabletype, fieldname, fieldvalue):
    """
    Update Table with additional data
    """
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    if tabletype == "SC_BMP_TLV":
        cursor.execute("UPDATE SC_BMP_TLV SET ? = ? WHERE peer_ip = ?", (peer_ip, ))
        #cursor.commit()
        print("UPDATED TRUST IP")


## Delete from table
def sqlliteDeleteData(tabletype, data):
    """
    Delete entry from the DB based on name as the key.
    """
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    if tabletype == "SC_BMP_INIT":
        print("Deleting entry from SC_BMP_INIT table...")
        cursor.execute("DELETE FROM SC_BMP_INIT WHERE bmp_client_id = ?", (data,))
        connection.commit()
    elif tabletype == "SC_BMP_TLV":
        print("Deleting entry from SC_BMP_TLV table..")
        cursor.execute("DELETE FROM SC_BMP_TLV WHERE interface_ips = ? and peerip = ?", (data[0],data[1],))
        connection.commit()
    print("Deleted field based on {}".format(data))
    connection.close()


def thread_kafka_topic_handler(message):
    """
    process threads
    """
    if (message.topic == 'bmp-rm-unicast'):
        processBmpRmUnicast(message)
    elif (message.topic == "bmp-init"):
        processBmpInit(message)
    elif (message.topic == "bmp-term"):
        processBmpTerm(message)
    #elif (message.topic == 'bmp-rm-tlv'):
    #    processBmpRmTlv(message)
    #elif (message.topic == 'bmp-stats'):
    #    processBmpStats(message)
    #elif (message.topic == "bmp-peer"):
    #    processBmpPeer(message)


def processBmpInit(message):
    """
    process BMP Init messages.
    To do:
    1. use regex to grab integers to identify dev name
    """
    print("process bmp-init messsage......")
    bmpinit = json.loads(message.value)
    #print(bmpinit)
    bmp_client_id = bmpinit["keys"]["dut-address"]
    sysname = bmpinit["fields"]["sysname"]
    sysdesc = bmpinit["fields"]["sysdesc"]
    vendor = ""
    if "Juniper" in sysdesc:
        vendor = "Juniper Networks"
    else:
        vendor = "unknown vendor"
    # can parse further based on hostname. For example: ny01fw1
    location = sysname[:2]
    # modify this to use regex to grab all integers in string
    deviceid = sysname[2:]
    print("hostname: {}".format(sysname))
    print("location: {}".format(location))
    sqlliteInsertData(bmp_client_id,"SC_BMP_INIT",[location,vendor,deviceid])


# WIP: Currently not used
def processBmpPeer(message):
    """
    Process BMP Peer message and store into database
    To do:
    1. Identify which is untrust peer and trust peer.
    below uses ASN range which could be used.
    """
    print("currently not processing Bmp-peer...")
    #mpeer = json.loads(message.value)
    #print(mpeer)
    #mpeer_peerip = mpeer["fields"]["peer-bgp-id"]
    #mpeer_is_l3vpn_peer = mpeer["fields"]["is-l3vpn-peer"]
    #mpeer_peer_status = mpeer["fields"]["peer-status"]
    #mpeer_is_v4_peer = mpeer["fields"]["is-v4-peer"]
    #mpeer_local_addr = mpeer["fields"]["local-addr"]
    #mpeer_peer_as = mpeer["fields"]["peer-as"]
    #print(mpeer_peer_as)
    #untrust_as_range = range(65500,65500)
    #trust_as_range = range(65510,65511)
    #if ((mpeer_peer_status == "up") and (mpeer_peer_as in trust_as_range)):
    #    trust_intf_ip = mpeer_peerip
    #elif ((mpeer_peer_status == "up") and (mpeer_peer_as in untrust_as_range)):
    #    untrust_intf_ip = mpeer_peerip
    #print("trust_intf_ip: {}".format(trust_intf_ip))
    #print("untrust_intf_ip: {}".format(untrust_intf_ip))


# WIP: Currently not used 
def processBmpStats(message):
    """
    Process BMP stats message
    """
    print("currently not processing bmp-stats....")
    #mstats = json.loads(message.value)
    #print(mstats)


def processBmpTerm(message):
    """
    Process BMP term message. When BMP goes down, remove entry from table
    SC_BMP_INIT based on dut_ip
    """
    print("currently not processing bmp-term message...")
    mterm = json.loads(message.value)
    print(mterm)
    bmp_client_id = mterm["keys"]["dut-address"]
    term_reason = mterm["fields"]["term-reason"]
    term_time = mterm["fields"]["time-sec"]
    print("BMP CLIENT {} WENT DOWN.. @ time {}..Removing DB entry".format(bmp_client_id, term_time))
    sqlliteDeleteData("SC_BMP_INIT",bmp_client_id)


def processBmpRmUnicast(message):
    """
    process BGP-RM. Find out the advertised prefixes.
    peerid, prefix, community. Validate against the community 
    and load the trust and untrust prefix
    """
    print("processing Bmp-rm-unicast...")
    mrm = json.loads(message.value)
    print(mrm)
    len_fields = len(mrm["fields"]["rm-msgs"])
    bmp_client_id = mrm["keys"]["dut-address"]
    for imrm in range(0, len_fields):
        peerip = ""
        ips = ""
        ip_type = ""
        communities = ""
        next_hop = ""
        action = mrm["fields"]["rm-msgs"][imrm]["fields"]["action"]
        monitor = mrm["fields"]["rm-msgs"][imrm]["fields"]["monitor-type"]
        #print(action, monitor)
        if ((action == "update") and (monitor == "rib-in-pre-policy")):
            print("action Update received.. ")
            if "com" in mrm["fields"]["rm-msgs"][imrm]["fields"].keys():
                communities = mrm["fields"]["rm-msgs"][imrm]["fields"]["com"]
                if "next-hop" in mrm["fields"]["rm-msgs"][imrm]["fields"].keys(): 
                    next_hop = mrm["fields"]["rm-msgs"][imrm]["fields"]["next-hop"]
                    prefixes = mrm["fields"]["rm-msgs"][imrm]["fields"]["prefixes"]
                    peerip = mrm["fields"]["rm-msgs"][imrm]["fields"]["peer-ip"]
                    if (communities.strip(" ") in TRUST_COMMUNITIES):
                        ips = ','.join(prefixes)
                        ip_type = "Trust"
                    elif (communities.strip(" ") in UNTRUST_COMMUNITIES):
                        ips = ','.join(prefixes)
                        ip_type = "Untrust"
                    sqlliteInsertData(bmp_client_id,"SC_BMP_TLV",[peerip,ips,ip_type])
                else:
                    print("no nexthop... continuing..")
                    continue
            else:
                print("no community.. continuing...")
                continue
        elif (( action == "delete") and (monitor == "rib-in-pre-policy")):
            prefixes = mrm["fields"]["rm-msgs"][imrm]["fields"]["prefixes"]
            ips = ','.join(prefixes)
            peerip = mrm["fields"]["rm-msgs"][imrm]["fields"]["peer-ip"]
            #print(ips, peerip, bmp_client_id)
            sqlliteDeleteData("SC_BMP_TLV",[ips,peerip])

def processBmpRmTlv(message):
    """
    process BGP-RM-TLV
    rib-in pre policy only applicable. Everything is TLV based.
    Ignore this and rely on rm-unicast
    """
    print("currently not processing bgp-rm-tlv... ")
    #mrmtlv = json.loads(message.value)
    #print(mrmtlv)

if __name__ == "__main__":
    """
    Main definition
    """
    kafka_connected = False
    print("Connect to SQLite DN")
    #createConnection(DB_FILE)
    sqliteTableAdd(DB_FILE)
    while True:
        if kafka_connected == False:
            try:
                consumer = KafkaConsumer(*kafka_topics,
                                          max_poll_records=100000,
                                          bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS_CONS)
                print("Kafka conenction OK")
                kafka_connected = True
            except:
                print("Kafka not conneccted to: ", KAFKA_BOOTSTRAP_SERVERS_CONS)
                kafka_connected = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            for message in consumer:
                executor.submit(thread_kafka_topic_handler, message=message,)
