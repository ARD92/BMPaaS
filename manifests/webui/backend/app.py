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


def queryDb(DB_FILE):
    """
    Query the database to get vals
    """
    KEYLIST = ["Location", "Vendor", "PeerIP", "DeviceID", "InterfaceIPs", "IPtype"]
    DICT = { key: None for key in KEYLIST }
    FINAL = []

    engine = create_engine('sqlite:///'+DB_FILE, echo = True)
    conn = engine.connect()
    rows = text("SELECT location, vendor, peerip, device_id, interface_ips, ip_type FROM SC_BMP_INIT inner join SC_BMP_TLV on SC_BMP_INIT.bmp_client_id=SC_BMP_TLV.bmp_client_id")
    result = conn.execute(rows).fetchall()

    for i in result:
        DICT["Location"] = i[0]
        DICT["Vendor"] = i[1]
        DICT["PeerIP"] = i[2]
        DICT["DeviceID"] = i[3]
        DICT["InterfaceIPs"] = i[4]
        DICT["IPtype"] = i[5]
        FINAL.append(DICT)

    return FINAL

@app.route("/")
def display():
    """
    View the root page with the table
    """
    result = init_db()
    if result == 1:
        rows = queryDb(DB_FILE)
        return rows


if __name__ == '__main__':
    app.run(debug=True)
