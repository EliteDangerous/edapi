"""
Python Implementation of the EDDN publisher:

https://github.com/jamesremuscat/EDDN/blob/master/examples/PHP/EDDN.php
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

    _commodity_schemas = {
        'production': 'http://schemas.elite-markets.net/eddn/commodity/3',
        'test': 'http://schemas.elite-markets.net/eddn/commodity/3/test',
    }

    _shipyard_schemas = {
        'production': 'http://schemas.elite-markets.net/eddn/shipyard/2',
        'test': 'http://schemas.elite-markets.net/eddn/shipyard/2/test',
    }

    _outfitting_schemas = {
        'production': 'http://schemas.elite-markets.net/eddn/outfitting/2',
        'test': 'http://schemas.elite-markets.net/eddn/outfitting/2/test',
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
        noHash,
        softwareName,
        softwareVersion
    ):
        # Obfuscate uploaderID
        if noHash:
            self.uploaderID = uploaderID
        else:
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

        message['$schemaRef'] = self._commodity_schemas[('test' if self._debug else 'production')]  # NOQA

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

    def publishOutfitting(
        self,
        systemName,
        stationName,
        modules,
        timestamp=0
    ):
        message = {}

        message['$schemaRef'] = self._outfitting_schemas[('test' if self._debug else 'production')]  # NOQA

        message['header'] = {
            'uploaderID': self.uploaderID,
            'softwareName': self.softwareName,
            'softwareVersion': self.softwareVersion
        }

        message['message'] = {
            'systemName': systemName,
            'stationName': stationName,
            'modules': modules,
        }

        self.postMessage(message, timestamp)


