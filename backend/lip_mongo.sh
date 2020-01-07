#!/bin/bash
DBPATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
nohup mongod --dbpath ${DBPATH}/mongodb > ${DBPATH}/mongodb/dm_mongo.log 2>&1 &

