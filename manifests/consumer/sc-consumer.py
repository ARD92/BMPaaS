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
    """
    print(name, location, vendor, trust_intf_ip, untrust_intf_ip)
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO DISCOVERY VALUES (?, ?, ?, ?, ?)", (name, location, vendor, trust_intf_ip, untrust_intf_ip))
    connection.commit()
    print("New SC discovered Data added")


# Update data in table
# WIP!! Do not use this yet
def sqlliteUpdateData(name, fieldname, fieldvalue):
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
    if ((message.topic == 'bmp-rm') or (message.topic == 'bmp-rm-tlv')):
        print("BGP RM TLV recevied!!\n ")
        processBmpRm(message)
    elif (message.topic == 'bmp-stats'):
        processBmpStats(message)
    elif (message.topic == "bmp-peer"):
        processBmpPeer(message)
    elif (message.topic == "bmp-init"):
        processBmpInit(message)

def processBmpPeer(message):
    """
    Process BMP Peer message and store into database
    """
    print("process BMP peer")
    mpeer = json.loads(message.value)
    print(mpeer)

def processBmpStats(message):
    """
    Process BMP stats message
    """
    print("process BMP stats")
    mstats = json.loads(message.value)
    print(mstats)

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
