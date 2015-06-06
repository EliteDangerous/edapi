"""
Python Implementation of the EDDN publisher:

    https://github.com/jamesremuscat/EDDN/blob/master/examples/PHP/EDDN.php

Only supports schema v2
"""

from datetime import datetime, timezone
import hashlib
import json
import random
import requests
from time import time

# As of 1.3, ED reports four levels. 
levels = (
    'Low',
    'Low',
    'Med',
    'High',
)

class EDDN:
    _gateways = (
        'http://eddn-gateway.elite-markets.net:8080/upload/',
#        'http://eddn-gateway.ed-td.space:8080/upload/',
    )

    _schemas = {
        'production': 'http://schemas.elite-markets.net/eddn/commodity/2',
        'test': 'http://schemas.elite-markets.net/eddn/commodity/2/test',
    }

    _debug = True

    def __init__(
        self,
        uploaderID,
        softwareName,
        softwareVersion
    ):
        # Obfuscate uploaderID
        self.uploaderID = hashlib.sha1(uploaderID.encode('utf-8')).hexdigest()
        self.softwareName = softwareName
        self.softwareVersion = softwareVersion

    def publishCommodities(
        self,
        systemName,
        stationName,
        commodities,
        timestamp=0
    ):
        message = {}

        message['$schemaRef'] = self._schemas[('test' if self._debug else 'production')]

        message['header'] = {
            'uploaderID': self.uploaderID,
            'softwareName': self.softwareName,
            'softwareVersion': self.softwareVersion
        }

        if timestamp:
            timestamp = datetime.fromtimestamp(timestamp).isoformat()
        else:
            timestamp = datetime.now(timezone.utc).astimezone().isoformat()

        message['message'] = {
            'systemName': systemName,
            'stationName': stationName,
            'timestamp': timestamp,
            'commodities': commodities,
        }

        url = random.choice(self._gateways)

        headers = {
            'content-type' : 'application/json; charset=utf8'
        }

        if self._debug:
            print(
                json.dumps(
                    message,
                    sort_keys=True,
                    indent=4
                )
            )

        r = requests.post(
            url,
            data=json.dumps(
                message,
                ensure_ascii=False
            ).encode('utf8'),
            verify=True
        )

        r.raise_for_status()
