# Author: Aravind Prabhakar (aprabh@juniper.net)
# Version: v1.1
# Date: 2022-08-24

# Install sqlite
apt update && apt install sqlite

# Loadpackage
cli -c "request system yang add package sc-discovery module sc-discovery.yang action-script sc-discover_yang_action.py"

