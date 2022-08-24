#!/usr/bin/python

# Author: aprabh@juniper.net
# Version: v1.1
# Description: Kafka consumer app to parse BGP messages and store 
#              them into a SQLite DB with necessary params.
#              The params include (hostname, untrust interface IP, trust Interface IP)

import sqlite3
import kafka
import concurrent.futures
import json
import logging
from kafka import KafkaConsumer
from kafka import KafkaProducer
from sqlite3 import Error
from concurrent.futures import ThreadPoolExecutor
from logging import handlers

# Logging
Logrotate = logging.handlers.RotatingFileHandler(
    filename="/opt/sc-discovery.log",
    mode='a',
    maxBytes=1024000,
    backupCount=10,
    encoding=None,
    delay=0
)

logger_blocklist = ["sqlite3", "kafka", "json", "concurrent.futures"]
logging.basicConfig(format='%s(name)s - %(levelname)s - %(message)s', level=logging.INFO, handlers=[Logrotate])
for module in logger_blocklist:
    logging.getLogger(module).setLevel(logging.WARNING)

# Supported kafka topics from cRPD
#kafka_topics = ["bmp-init", "bmp-peer", "bmp-rm-unicast", "bmp-term", "bmp-rm-tlv", "bmp-stats"]
kafka_topics = ["bmp-init", "bmp-rm-unicast", "bmp-term"]

# Connection detail. Kafka service is used hence no need for IP
KAFKA_BOOTSTRAP_SERVERS_CONS = 'kafka:9092'

# Sqlite DB to store discovered information
DB_FILE = '/opt/service_chain.db'

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
    connection.execute("CREATE TABLE IF NOT EXISTS SC_BMP_INIT (bmp_client_id TEXT NOT NULL,location TEXT NOT NULL,vendor TEXT,device_id TEXT NOT NULL, PRIMARY KEY (bmp_client_id, location, device_id));")
    connection.execute("CREATE TABLE IF NOT EXISTS SC_BMP_TLV (bmp_client_id TEXT NOT NULL ,peerip TEXT NOT NULL,interface_ips TEXT NOT NULL,ip_type TEXT, PRIMARY KEY (bmp_client_id, peerip, interface_ips));")
    logging.info("SC_BMP_INIT and SC_BMP_TLV table added...")
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
    try:
        logging.info("inserting data into table")
        connection = sqlite3.connect(DB_FILE)
        cursor = connection.cursor()
        if tabletype == "SC_BMP_INIT":
            cursor.execute("INSERT INTO SC_BMP_INIT VALUES (?, ?, ?, ?)", (bmp_client_id,data[0],data[1],data[2]))
            logging.info("New BMP client details added")
        elif tabletype == "SC_BMP_TLV":
            logging.debug(data)
            cursor.execute("INSERT INTO SC_BMP_TLV VALUES (?, ?, ?, ?)", (bmp_client_id,data[0],data[1],data[2]))
            logging.info("New service chain update added")
    except Error as err:
        logging.info(err)
    finally:
        connection.commit()
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
        logging.info("UPDATED TRUST IP")


## Delete from table
def sqlliteDeleteData(tabletype, data):
    """
    Delete entry from the DB based on name as the key.
    """
    logging.info("delete call made...{} ,{}".format(tabletype, data))
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    if tabletype == "SC_BMP_INIT":
        logging.info("Deleting entry from SC_BMP_INIT table...")
        cursor.execute("DELETE FROM SC_BMP_INIT WHERE bmp_client_id = ?", (data,))
    elif tabletype == "SC_BMP_TLV":
        logging.info("Deleting entry from SC_BMP_TLV table..")
        cursor.execute("DELETE FROM SC_BMP_TLV WHERE interface_ips = ? and peerip = ?", (data[0],data[1],))
    logging.info("Deleted field based on {}".format(data))
    connection.commit()
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
    logging.info("process bmp-init messsage......")
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
    logging.debug("hostname: {}".format(sysname))
    logging.debug("location: {}".format(location))
    sqlliteInsertData(bmp_client_id,"SC_BMP_INIT",[location,vendor,deviceid])


# WIP: Currently not used
def processBmpPeer(message):
    """
    Process BMP Peer message and store into database
    To do:
    1. Identify which is untrust peer and trust peer.
    below uses ASN range which could be used.
    """
    logging.info("currently not processing Bmp-peer...")
    #mpeer = json.loads(message.value)
    #print(mpeer)


# WIP: Currently not used 
def processBmpStats(message):
    """
    Process BMP stats message
    """
    logging.info("currently not processing bmp-stats....")
    #mstats = json.loads(message.value)
    #print(mstats)


def processBmpTerm(message):
    """
    Process BMP term message. When BMP goes down, remove entry from table
    SC_BMP_INIT based on dut_ip
    """
    logging.info("currently not processing bmp-term message...")
    mterm = json.loads(message.value)
    #print(mterm)
    bmp_client_id = mterm["keys"]["dut-address"]
    term_reason = mterm["fields"]["term-reason"]
    term_time = mterm["fields"]["time-sec"]
    logging.info("BMP CLIENT {} WENT DOWN.. @ time {}..Removing DB entry".format(bmp_client_id, term_time))
    sqlliteDeleteData("SC_BMP_INIT",bmp_client_id)


def processBmpRmUnicast(message):
    """
    process BGP-RM. Find out the advertised prefixes.
    peerid, prefix, community. Validate against the community 
    and load the trust and untrust prefix
    """
    logging.info("processing Bmp-rm-unicast...")
    mrm = json.loads(message.value)
    #print(mrm)
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
        logging.debug(action, monitor)
        if ((action == "update") and (monitor == "rib-in-pre-policy")):
            logging.info("action Update received.. ")
            if "com" in mrm["fields"]["rm-msgs"][imrm]["fields"].keys():
                communities = mrm["fields"]["rm-msgs"][imrm]["fields"]["com"]
                if "next-hop" in mrm["fields"]["rm-msgs"][imrm]["fields"].keys(): 
                    next_hop = mrm["fields"]["rm-msgs"][imrm]["fields"]["next-hop"]
                    prefixes = mrm["fields"]["rm-msgs"][imrm]["fields"]["prefixes"]
                    logging.debug(prefixes)
                    peerip = mrm["fields"]["rm-msgs"][imrm]["fields"]["peer-ip"]
                    if (communities.strip(" ") in TRUST_COMMUNITIES):
                        ip_type = "Trust"
                        for prefix in prefixes:
                            sqlliteInsertData(bmp_client_id,"SC_BMP_TLV",[peerip,prefix,ip_type])
                    elif (communities.strip(" ") in UNTRUST_COMMUNITIES):
                        ip_type = "Untrust"
                        for prefix in prefixes:
                            sqlliteInsertData(bmp_client_id,"SC_BMP_TLV",[peerip,prefix,ip_type])
                else:
                    logging.debug("no nexthop... continuing..")
                    continue
            else:
                loggin.debug("no community.. continuing...")
                continue
        elif (( action == "delete") and (monitor == "rib-in-pre-policy")):
            prefixes = mrm["fields"]["rm-msgs"][imrm]["fields"]["prefixes"]
            peerip = mrm["fields"]["rm-msgs"][imrm]["fields"]["peer-ip"]
            logging.debug(ips, peerip, bmp_client_id)
            for prefix in prefixes:
                sqlliteDeleteData("SC_BMP_TLV",[prefix,peerip])


def processBmpRmTlv(message):
    """
    process BGP-RM-TLV
    rib-in pre policy only applicable. Everything is TLV based.
    Ignore this and rely on rm-unicast
    """
    logging.info("currently not processing bgp-rm-tlv... ")
    #mrmtlv = json.loads(message.value)
    #print(mrmtlv)

if __name__ == "__main__":
    """
    Main definition
    """
    kafka_connected = False
    logging.info("Connect to SQLite DN")
    #createConnection(DB_FILE)
    sqliteTableAdd(DB_FILE)
    while True:
        if kafka_connected == False:
            try:
                consumer = KafkaConsumer(*kafka_topics,
                                          max_poll_records=100000,
                                          bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS_CONS)
                logging.debug("Kafka conenction OK")
                kafka_connected = True
            except:
                print("Kafka not conneccted to: ", KAFKA_BOOTSTRAP_SERVERS_CONS)
                kafka_connected = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            for message in consumer:
                executor.submit(thread_kafka_topic_handler, message=message,)
