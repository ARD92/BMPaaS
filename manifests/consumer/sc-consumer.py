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
kafka_topics = ["bmp-init", "bmp-peer", "bmp-rm-unicast", "bmp-rm-tlv", "bmp-stats", "bmp-term"]

# Connection detail. Kafka service is used hence no need for IP
KAFKA_BOOTSTRAP_SERVERS_CONS = 'kafka:9092'

# Sqlite DB to store discovered information
DB_FILE = '/opt/sc-discovery.db'

# List of communtiies for trust and untrust
TRUST_COMMUNITIES = ["13979:100"]
UNTRUST_COMMUNITIES = ["13979:200"]

# Create database and connection
def createConnection(DB_FILE):
    """
    Create a database connection and create the DB if not present.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        print(sqlite3.version)
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


# Create table 
def sqliteTableAdd(DB_FILE):
    """
    Create the table if it doesnt exist. If it exists, reuse the table.
    """
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS SC_BMP_INIT (bmp_client_id TEXT,location TEXT,vendor TEXT,device_id TEXT);")
    cursor.execute("CREATE TABLE IF NOT EXISTS SC_BMP_TLV (bmp_client_id TEXT,peerip TEXT,trust_intf_ip TEXT,untrust_intf_ip TEXT);")
    print("SC_BMP_INIT and SC_BMP_TLV table added...")


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
        cursor.execute("INSERT INTO SC_BMP_TLV VALUES (?, ?, ?, ?)", (bmp_client_id,data[0],data[1],data[2]))
        connection.commit()
        print("New service chain update added")


# Update data in table
# WIP!! Do not use this yet
def sqlliteUpdateData(name, fieldname, fieldvalue):
    """
    Update Table with additional data
    """
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("UPDATE DISCOVERY SET ? = ? WHERE name = ?", (fieldname, fieldvalue, name))
    print("UPDATED TRUST IP")


# Delete from table
def sqlliteDeleteData(name):
    """
    Delete entry from the DB based on name as the key.
    """
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM DISCOVERY WHERE name = ?", (name,))
    connection.commit()
    print("Deleted field with name {}".format(name))


def thread_kafka_topic_handler(message):
    """
    process threads
    """
    if (message.topic == 'bmp-rm-unicast'):
        processBmpRm(message)
    elif (message.topic == 'bmp-rm-tlv'):
        processBmpRmTlv(message)
    elif (message.topic == 'bmp-stats'):
        processBmpStats(message)
    elif (message.topic == "bmp-peer"):
        processBmpPeer(message)
    elif (message.topic == "bmp-init"):
        processBmpInit(message)
    elif (messgae.topic == "bmp-term"):
        processBmpTerm(message)


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
    #print(bmp_client_id)
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
    mpeer = json.loads(message.value)
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
    #print("currently not processing bmp-stats....")
    mstats = json.loads(message.value)
    #print(mstats)


# WIP: Currently not used
def processBmpTerm(message):
    """
    Process BMP term message.
    """
    #print("currently not processing bmp-term message...")
    mterm = json.loads(message.value)
    #print(mterm)


# WIP: Currently not used
def processBmpRm(message):
    """
    process BGP-RM. Find out the advertised prefixes.
    peerid, prefix, community. Validate against the community 
    and load the trust and untrust prefix
    """
    print("currently not processing Bmp-rm...")
    mrm = json.loads(message.value)


def processBmpRmTlv(message):
    """
    process BGP-RM-TLV
    use peerip as primary key
    """
    print("process bgp-rm-tlv")
    mrmtlv = json.loads(message.value)
    trust_intf_ip = ""
    untrust_intf_ip = ""
    peerip = ""
    len_fields = len(mrmtlv["fields"]["rm-msgs"])
    bmp_client_id = mrmtlv["keys"]["dut-address"]
    for imrmtlv in range(1, len_fields):
        prefixes = mrmtlv["fields"]["rm-msgs"][imrmtlv]["fields"]["prefixes"]
        communities = mrmtlv["fields"]["rm-msgs"][imrmtlv]["fields"]["attributes"]["Communities"]["hex_val"]
        next_hop = mrmtlv["fields"]["rm-msgs"][imrmtlv]["fields"]["attributes"]["Nexthop"]["hex_val"]
        dec_comm = communities.split(" ")
        dec_comm_fin = str(int(''.join(dec_comm[:2]),16))+":"+str(int(''.join(dec_comm[2:]),16))
        peerip = mrmtlv["fields"]["rm-msgs"][imrmtlv]["fields"]["peer-ip"]
        action = mrmtlv["fields"]["rm-msgs"][imrmtlv]["fields"]["action"]
        if ((dec_comm_fin in TRUST_COMMUNITIES) and (action == "update")):
            trust_intf_ip = ','.join(prefixes)
        elif ((dec_comm_fin in UNTRUST_COMMUNITIES) and (action == "update")):
            untrust_intf_ip = ','.join(prefixes)
    print("bmp_client_id: {}".format(bmp_client_id))
    print("peerip: {}".format(peerip))
    print("trust_ips: {}".format(trust_intf_ip))
    print("untrust_ips: {}".format(untrust_intf_ip))
    sqlliteInsertData(bmp_client_id,"SC_BMP_TLV",[peerip, trust_intf_ip, untrust_intf_ip])

if __name__ == "__main__":
    """
    Main definition
    """
    kafka_connected = False
    print("Connect to SQLite DN")
    createConnection(DB_FILE)
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
                #print(message)
                executor.submit(thread_kafka_topic_handler, message=message,)
