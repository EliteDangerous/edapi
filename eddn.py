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


class EDDN:
    _gateways = (
        'http://eddn-gateway.elite-markets.net:8080/upload/',
        # 'http://eddn-gateway.ed-td.space:8080/upload/',
    )

    _market_schemas = {
        'production': 'http://schemas.elite-markets.net/eddn/commodity/2',
        'test': 'http://schemas.elite-markets.net/eddn/commodity/2/test',
    }

    _shipyard_schemas = {
        'production': 'http://schemas.elite-markets.net/eddn/shipyard/1',
        'test': 'http://schemas.elite-markets.net/eddn/shipyard/1/test',
    }

    _debug = True

    # As of 1.3, ED reports four levels.
    _levels = (
        'Low',
        'Low',
        'Med',
        'High',
    )

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

    def postMessage(
        self,
        message,
        timestamp=0
    ):
        if timestamp:
            timestamp = datetime.fromtimestamp(timestamp).isoformat()
        else:
            timestamp = datetime.now(timezone.utc).astimezone().isoformat()

        message['message']['timestamp'] = timestamp

        url = random.choice(self._gateways)

        headers = {
            'content-type': 'application/json; charset=utf8'
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
            headers=headers,
            data=json.dumps(
                message,
                ensure_ascii=False
            ).encode('utf8'),
            verify=True
        )

        r.raise_for_status()

    def publishCommodities(
        self,
        systemName,
        stationName,
        commodities,
        timestamp=0
    ):
        message = {}

        message['$schemaRef'] = self._market_schemas[('test' if self._debug else 'production')]  # NOQA

        message['header'] = {
            'uploaderID': self.uploaderID,
            'softwareName': self.softwareName,
            'softwareVersion': self.softwareVersion
        }

        message['message'] = {
            'systemName': systemName,
            'stationName': stationName,
            'commodities': commodities,
        }

        self.postMessage(message, timestamp)

    def publishShipyard(
        self,
        systemName,
        stationName,
        ships,
        timestamp=0
    ):
        message = {}

        message['$schemaRef'] = self._shipyard_schemas[('test' if self._debug else 'production')]  # NOQA

        message['header'] = {
            'uploaderID': self.uploaderID,
            'softwareName': self.softwareName,
            'softwareVersion': self.softwareVersion
        }

        message['message'] = {
            'systemName': systemName,
            'stationName': stationName,
            'ships': ships,
        }

        self.postMessage(message, timestamp)
