# Install sqlite
apt update && apt install sqlite

# Loadpackage
cli -c "request system yang add package sc-discovery module /tmp/yang-pkg/sc-discovery.yang action-script /tmp/yang-pkg/sc-discover_yang_action.py"

