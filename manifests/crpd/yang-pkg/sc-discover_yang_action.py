#!/usr/bin/python3

# Date: 2022-08-23
# Author: aprabh@juniper.net
# Version: v1.1
# Description: Action script for the yang rpc package 
#              which queries the DB and displays the discovered service 
# 
# Copy this file to /var/db/scripts/action

import os
import argparse
import sqlite3
#import pprint
from sqlite3 import Error

DB_FILE = "/mnt/service_chain.db"

def generate_xml(args):
    xml_items = []
    if (args.rpc_name == "get-discovery"):
        rows =  queryDb(DB_FILE)
        for row in rows:
            XML = '''
                <discovered>
                <location>{0}</location>
                <vendor>{1}</vendor>
                <peer_ip>{2}</peer_ip>
                <device_id>{3}</device_id>
                <service_ip>{4}</service_ip>
                <service_ip_type>{5}</service_ip_type>
                </discovered>
                '''.format(row[0], row[1], row[2], row[3], row[4], row[5])
            xml_items.append(XML)

    return xml_items

def queryDb(DB_FILE):
    """
    Query the database to get vals
    """
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    rows = cursor.execute("SELECT location, vendor, peerip, device_id, interface_ips, ip_type FROM SC_BMP_INIT inner join SC_BMP_TLV on SC_BMP_INIT.bmp_client_id=SC_BMP_TLV.bmp_client_id").fetchall()

    return rows

def main():
    parser = argparse.ArgumentParser(description='This is a demo script.')
    parser.add_argument('--rpc_name', required=True)
    parser.add_argument('--discovered', required=True, default=None)
    args = parser.parse_args()

    # generate XML for RPC
    rpc_output_xml = generate_xml(args)
    #pp = pprint.PrettyPrinter() 
    for xml_val in rpc_output_xml:
        print(xml_val)


if __name__ == "__main__":
    main()
