#!/bin/bash
if [ "$#" -gt 1 ]; then
    echo "too many arguments!" 2>&1
    exit 1
fi
if [ "$#" = 1 ]; then
    user="$1"
else
    user=$(/usr/bin/whoami)
fi
/usr/bin/sacctmgr --json show associations user=$user | /usr/bin/jq -r '.associations[].account'

