#!/bin/bash

curl -O $ACCOUNT_BALANCES_TASK_URL

influx config rm primoco-influx.conf
influx config create --config-name primoco-influx.conf --host-url http://influxdb:8086 --org $INFLUXDB_ORG --token $INFLUXDB_TOKEN --active

influx config
echo "Calculate account balances..."
SECONDS=0
influx query --file ./accounts-balances.js 1> /dev/null
duration=$SECONDS
echo "Done in $(($duration / 60)) minutes and $(($duration % 60)) seconds."
