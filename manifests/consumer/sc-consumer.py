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
    cursor.execute("CREATE TABLE IF NOT EXISTS DISCOVERY (name TEXT, location TEXT, vendor TEXT, trust_intf_ip TEXT, untrust_intf_ip TEXT);")
    print("table added")


# Insert into table
def sqlliteInsertData(
                        name,
                        location, 
                        vendor,
                        trust_intf_ip,
                        untrust_intf_ip
                        ):
    """
    Insert data into the table. The data typically contains if the service chain element is present
    or not. we need the same params as the input to the function definition. The names are self 
    explanatory.
    To do:
    1. Identify common param between BMPinit and BMPpeer topics
    """
    if name is None:
        name = ""
    elif location is None:
        location = ""
    elif vendor is None:
        vendor = ""
    elif trust_intf_ip is None:
        trust_intf_ip = ""
    elif untrust_intf_ip is None:
        untrust_intf_ip = ""

    print(name, location, vendor, trust_intf_ip, untrust_intf_ip)
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO DISCOVERY VALUES (?, ?, ?, ?, ?)", (name, location, vendor, trust_intf_ip, untrust_intf_ip))
    connection.commit()
    print("New SC discovered Data added")


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
        print("BGP RM unicast recevied!!\n ")
        processBmpRm(message)
    elif (message.topic == 'bmp-rm-tlv'):
        print("BGP RM TLV")
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
    bmpinit = json.loads(message.value)
    sysname = bmpinit["fields"]["sysname"]
    sysdesc = bmpinit["fields"]["sysdesc"]
    if "Juniper" in sysdesc:
        vendor = "Juniper Networks"
    # can parse further based on hostname. For example: ny01fw1
    hostname = sysname
    location = sysname[:2]
    # modify this to use regex to grab all integers in string
    device_id = sysname[2:4]
    print("hostname: {}".format(hostname))
    print("location: {}".format(location))
    #sqlliteInsertData(sysname, location, vendor, "", "")


def processBmpPeer(message):
    """
    Process BMP Peer message and store into database
    To do:
    1. Identify which is untrust peer and trust peer.
    below uses ASN range which could be used.
    """
    print("process BMP peer")
    mpeer = json.loads(message.value)
    #print(mpeer)
    mpeer_peerip = mpeer["fields"]["peer-bgp-id"]
    mpeer_is_l3vpn_peer = mpeer["fields"]["is-l3vpn-peer"]
    mpeer_peer_status = mpeer["fields"]["peer-status"]
    mpeer_is_v4_peer = mpeer["fields"]["is-v4-peer"]
    mpeer_local_addr = mpeer["fields"]["local-addr"]
    mpeer_peer_as = mpeer["fields"]["peer-as"]
    #print(mpeer_peer_as)
    #untrust_as_range = range(65500,65500)
    #trust_as_range = range(65510,65511)
    #if ((mpeer_peer_status == "up") and (mpeer_peer_as in trust_as_range)):
    #    trust_intf_ip = mpeer_peerip
    #elif ((mpeer_peer_status == "up") and (mpeer_peer_as in untrust_as_range)):
    #    untrust_intf_ip = mpeer_peerip
    #print("trust_intf_ip: {}".format(trust_intf_ip))
    #print("untrust_intf_ip: {}".format(untrust_intf_ip))


def processBmpStats(message):
    """
    Process BMP stats message
    """
    print("process BMP stats")
    mstats = json.loads(message.value)
    #print(mstats)

# WIP
def processBmpTerm(message):
    """
    Process BMP term message.
    """
    print("process term message")
    mterm = json.loads(message.value)
    #print(mterm)


def processBmpRm(message):
    """
    process BGP-RM
    """
    print("process BGP RM UNICAST")
    mrm = json.loads(message.value)
    #print(mrm)
    len_fields = len(mrm["fields"]["rm-msgs"])
    prefixes = mrm["fields"]["rm-msgs"][len_fields-1]["fields"]["prefixes"]
    communities = mrm["fields"]["rm-msgs"][len_fields-1]["fields"]["com"]
    print("prefixes: {}".format(prefixes))
    print("communities: {}".format(communities))
    if communities in TRUST_COMMUNITIES:
        trust_intf_ip = prefixes
    if communities in UNTRUST_COMMUNITIES:
        untrust_intf_ip = prefixes
    print("trust_intf_ip: {}".format(trust_intf_ip))
    print("untrust_intf_ip: {}".format(untrust_intf_ip))


def processBmpRmTlv(message):
    """
    process BGP-RM-TLV
    """
    print("process bgp-rm-tlv")
    mrmtlv = json.loads(message.value)
    #print(mrmtlv)


if __name__ == "__main__":
    """
    Main definition
    """
    kafka_connected = False
    print("Connect to SQLite DN")
    createConnection(DB_FILE)
    sqliteTableAdd(DB_FILE)
    #sqlliteInsertData("test", "nyc", "jnpr", "10.1.1.1", "10.2.1.1")
    #sqlliteDeleteData("test")
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
