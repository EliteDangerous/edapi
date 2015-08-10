#!/usr/bin/env python
# ----------------------------------------------------------------
# Simple EDDN client for debug purposes. Based on the example at
# https://github.com/jamesremuscat/EDDN
# ----------------------------------------------------------------

import argparse
import datetime
import simplejson
import sys
import time
import traceback
import zlib
import zmq

__version_info__ = ('3', '3', '2')
__version__ = '.'.join(__version_info__)


# ----------------------------------------------------------------
# Functions.
# ----------------------------------------------------------------


def parse_args():
    '''
    Parse arguments.
    '''
    # Basic argument parsing.
    parser = argparse.ArgumentParser(
        description='EDDN Test Client.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Version
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s '+__version__)

    # Debug
    parser.add_argument("--debug",
                        action="store_true",
                        default=False,
                        help="Output additional debug info, and use test\
                        schema.")

    # relay
    parser.add_argument("--relay",
                        default="tcp://eddn-relay.elite-markets.net:9500",
                        help='EDDN replay to connect to.')
    # timeout
    parser.add_argument("--timeout",
                        default=600000,
                        type=int,
                        help='Connection timeout.')

    # Software
    parser.add_argument("--software",
                        default=[
                            "EDAPI",
                            "EDAPI Trade Dangerous Plugin",
                        ],
                        nargs='+',
                        help="A list of whitelisted software. Use \"all\" to\
                        see all messages.")

    # Parse the command line.
    args = parser.parse_args()

    return args


def date(format):
    '''
    Date format helper.
    '''
    d = datetime.datetime.utcnow()
    return d.strftime(format)


def echoLog(line):
    '''
    Format console output.
    '''
    if (echoLog.oldTime is False) or (echoLog.oldTime != date('%H:%M:%S')):
        echoLog.oldTime = date('%H:%M:%S')
        line = str(echoLog.oldTime) + ' | ' + str(line)
    else:
        line = '        ' + ' | ' + str(line)

    print(line)
    sys.stdout.flush()
echoLog.oldTime = False


def Main():
    '''
    Main()
    '''
    # These are the schemas we will decode.
    allowed_schemas = {
        'http://schemas.elite-markets.net/eddn/commodity/2': 'commodity-v2',
        'http://schemas.elite-markets.net/eddn/shipyard/1': 'shipyard-v1',
    }

    # If debug, only listen for test type messages.
    if args.debug:
        for key, name in allowed_schemas.items():
            del allowed_schemas[key]
            key += '/test'
            allowed_schemas[key] = name

    echoLog('Starting EDDN Subscriber...')
    echoLog('')

    # Some info
    echoLog('Software white list:')
    for soft in args.software:
        echoLog('\t' + soft)
    echoLog('')

    echoLog('Schema white list:')
    for schema in allowed_schemas:
        echoLog('\t' + schema)
    echoLog('')

    # Configure the zmq subscriber.
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.setsockopt(zmq.SUBSCRIBE, b"")
    subscriber.setsockopt(zmq.RCVTIMEO, args.timeout)

   # Do this forever.
    while True:
        try:
            # Connect.
            subscriber.connect(args.relay)
            echoLog('Connected to ' + args.relay)
            echoLog('')
            echoLog('')

            # Keep reading until disconnected.
            while True:
                message = subscriber.recv()

                # We were disconnected.
                if message is False:
                    subscriber.disconnect(args.relay)
                    echoLog('Disconnected from ' + args.relay)
                    echoLog('')
                    echoLog('')
                    break

                # Decode the JSON message.
                message = simplejson.loads(zlib.decompress(message))

                # ID the schema.
                schema = "Unknown"
                if message['$schemaRef'] in allowed_schemas:
                    schema = allowed_schemas[message['$schemaRef']]
                else:
                    schema += ': ' + message['$schemaRef']
                echoLog('Received ' + schema)

                # Check if the software is white listed.
                if (
                    (
                        message['header']['softwareName'] in args.software or
                        args.software == ['all']
                    ) and
                    not schema.startswith("Unknown")
                ):
                    pass
                else:
                    continue

                # Log common info.
                echoLog('\t- Schema: ' + message['$schemaRef'])
                echoLog('\t- Software: ' + message['header']['softwareName'] + ' / ' + message['header']['softwareVersion'])  # NOQA
                echoLog('\t- Timestamp: ' + message['message']['timestamp'])
                echoLog('\t- Uploader ID: ' + message['header']['uploaderID'])
                echoLog('\t\t- System Name: ' + message['message']['systemName'])  # NOQA
                echoLog('\t\t- Station Name: ' + message['message']['stationName'])  # NOQA

                # Handle commodity v2
                if schema == 'commodity-v2':
                    for com in message['message']['commodities']:
                        echoLog('\t\t\t- Name: ' + com['name'])
                        echoLog('\t\t\t\t- Buy Price: ' + str(com['buyPrice']))
                        echoLog(
                            '\t\t\t\t- Supply: ' +
                            str(com['supply']) +
                            ' (' + com['supplyLevel'] + ')'
                        )
                        echoLog('\t\t\t\t- Sell Price: ' + str(com['sellPrice']))  # NOQA
                        echoLog(
                            '\t\t\t\t- Demand: ' +
                            str(com['demand']) +
                            ' (' + com['demandLevel'] + ')'
                        )

                    echoLog('')
                    echoLog('')

                # Handle shipyard v1
                if schema == 'shipyard-v1':
                    for ship in message['message']['ships']:
                        echoLog('\t\t\t- Ship: ' + ship)

                    echoLog('')
                    echoLog('')

        # Connect error... Retry...
        except zmq.ZMQError as e:
            echoLog('')
            echoLog('ZMQSocketException: ' + str(e))
            echoLog('')
            time.sleep(10)


if __name__ == '__main__':
    '''
    Command line invocation.
    '''

    try:
        # Parse any command line arguments.
        args = parse_args()

        # Command line overrides
        if args.debug is True:
            print('***** Debug mode *****')
            print(args)

        # Execute the Main() function and return results.
        sys.exit(Main())
    except KeyboardInterrupt as e:
        print("Disconnecting...")
        sys.exit(0)
    except SystemExit as e:
        # Clean exit, provide a return code.
        sys.exit(e.code)
    except:
        # Handle all other exceptions.
        ErrStr = traceback.format_exc()
        print('Exception in main loop. Exception info below:')
        sys.exit(ErrStr)
