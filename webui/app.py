__author__ = "Aravind Prabhakar"
__email__ = "aprabh@juniper.net"
# app.py
"""
- render_template used to render an html page
- Bulma for CSS
- sqlalchemy to read data from DB
"""
import os
from flask import Flask
from flask import render_template
from sqlalchemy import text
from sqlalchemy import create_engine

app = Flask(__name__)
DB_FILE = '/opt/service_chain.db'

"""
Verify if DB Exists
"""
def init_db():
    """ Initialize database"""
    try:
        if os.path.isfile(DB_FILE):
            msg = "INIT DB: Successful => Found database file {0}".format(DB_FILE)
            print(msg)
            return 1
    except Exception as e:
        msg = "Exception occured! DB initialization failed!!"
        print(msg)

def queryDblocation(DB_FILE):
    """
    query the locations. Based on locations display devices
    """
    FINAL = []
    KEYLIST = ["Location"]
    DICT = { key: None for key in KEYLIST }

    engine = create_engine('sqlite:///'+DB_FILE, echo = True)
    conn = engine.connect()
    rows = text("SELECT DISTINCT location FROM SC_BMP_INIT")
    result = conn.execute(rows).fetchall()

    for i in result:
        DICT["Location"] = i[0]
        FINAL.append(DICT)
        DICT = { key: None for key in KEYLIST }

    return FINAL

def queryDbdevice(DB_FILE, location):
    """
    Query the database to get vals for all devices
    """
    KEYLIST = ["Location", "Vendor", "PeerIP", "DeviceID", "InterfaceIPs", "IPtype"]
    DICT = { key: None for key in KEYLIST }
    FINAL = []

    engine = create_engine('sqlite:///'+DB_FILE, echo = True)
    conn = engine.connect()
    rows = text("SELECT DISTINCT location, vendor, peerip, device_id, interface_ips, ip_type FROM SC_BMP_INIT inner join SC_BMP_TLV on SC_BMP_INIT.bmp_client_id=SC_BMP_TLV.bmp_client_id WHERE location='{}'".format(location))
    result = conn.execute(rows).fetchall()
    for i in result:
        DICT["Location"] = i[0]
        DICT["Vendor"] = i[1]
        DICT["PeerIP"] = i[2]
        DICT["DeviceID"] = i[3]
        DICT["InterfaceIPs"] = i[4]
        DICT["IPtype"] = i[5]
        FINAL.append(DICT)
        DICT = { key: None for key in KEYLIST }

    return FINAL

@app.route("/")
def display():
    """
    View the root page with the table
    """
    result = init_db()
    if result == 1:
        title = "J-Discoverer"
        description = "Discover service chains in the underlay"
        subtitle = "Discovery using BMPaaS"
        footer = "Juniper Networks"
        rows = queryDblocation(DB_FILE)
        return render_template('index.html', display=rows, title=title, subtitle=subtitle, description=description, footer=footer)

@app.route("/<location>")
def displayLocation(location):
    """
    display discovered nodes based on location
    """
    rows = queryDbdevice(DB_FILE, location)
    return render_template("discovered.html", location=location, displaylocation=rows)

if __name__ == '__main__':
    app.run(debug=True)
