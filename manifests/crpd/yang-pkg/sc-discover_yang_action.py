#!/usr/bin/python3

# Date: 2022-08-23
# Author: aprabh@juniper.net
# Version: v1.1
# Description: Action script for the yang rpc package 
#              which queries the DB and displays the discovered service 
# 
# Copy this file to /var/db/scripts/action

import os
import jcs
import argparse
import sqlite3
from sqlite3 import Error

DB_FILE = "/mnt/service_chain.db"

def queryDb(DB_FILE):
    """
    Query the database to get vals
    """
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    rows = cursor.execute("SELECT location, vendor, peerip, device_id, interface_ips, ip_type FROM SC_BMP_INIT inner join SC_BMP_TLV on SC_BMP_INIT.bmp_client_id=SC_BMP_TLV.bmp_client_id").fetchall()
    for row in rows:
        location = row[0]
        vendor = row[1]
        peer_ip = row[2]
        device_id = row[3]
        service_ip = row[4]
        service_ip_type = row[5]
        print("<discovered>")
        print("<bmp_client_id>{}</bmp_client_id>".format(bmp_client_id))
        print("<location>{}</location>".format(location))
        print("<vendor>{}</vendor>".format(vendor))
        print("<device_id>{}</device_id>".format(device_id))
        print("<service_ip>{}</service_ip>".format(service_ip))
        print("<service_ip_type>{}</service_ip_type>".format(service_ip_type))
        print("</discovered>")

def main():
    parser = argparse.ArgumentParser(description='This is a demo script.')
    parser.add_argument('--discovered', required=True)
    parser.add_argument('--rpc_name', required=True)
    args = parser.parse_args()
    queryDb(DB_FILE)

if __name__ == "__main__":
    main()
