#!/usr/bin/env python
#----------------------------------------------------------------
# Elite: Dangerous Market Scraper
#----------------------------------------------------------------

import argparse
import csv
import getpass
import http.client
import http.cookiejar
import json
import os
from pathlib import Path
import platform
from pprint import pprint
import sys
import tempfile
import traceback
import urllib.parse
import urllib.request as urllib2

__version_info__ = ('2', '0', '0')
__version__ = '.'.join(__version_info__)

#----------------------------------------------------------------
# Deal with some differences in names between TD, ED and the API.
#----------------------------------------------------------------

# Not real items?
skip_categories = [
        'NonMarketable',
]

# TD has different names for these.
cat_corrections = {
        'Narcotics': 'Legal Drugs'
}

# TD has different names for these.
comm_corrections = {
        'Agricultural Medicines': 'Agri-Medicines',
        'Atmospheric Extractors': 'Atmospheric Processors',
        'Auto Fabricators': 'Auto-Fabricators',
        'Basic Narcotics': 'Narcotics',
        'Bio Reducing Lichen': 'Bioreducing Lichen',
        'Consumer Technology': 'Consumer Tech',
        'Domestic Appliances': 'Dom. Appliances',
        'Fruit And Vegetables': 'Fruit and Vegetables',
        'Hazardous Environment Suits': 'H.E. Suits',
        'Heliostatic Furnaces': 'Microbial Furnaces',
        'Non Lethal Weapons': 'Non-Lethal Wpns',
        'Terrain Enrichment Systems': 'Land Enrichment Systems',
}

#----------------------------------------------------------------
# Functions.
#----------------------------------------------------------------

def parse_args():
    '''
    Parse arguments.
    '''
    # Basic argument parsing.
    parser = argparse.ArgumentParser(description='EDMS: Elite Dangerous Market Scraper')

    # Version
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s '+__version__)

    # Debug
    parser.add_argument("--debug",
                        action="store_true",
                        default=False,
                        help="Output additional debug info.")

    # vars file
    parser.add_argument("--vars",
                        action="store_true",
                        default=False,
                        help="Output a file that sets environment variables\
                        for current cargo capacity, credits, insurance,\
                        and current system/station.")

    # Base file name. 
    parser.add_argument("--basename",
                        default="get_market",
                        help='Base file name. This is used to construct the\
                        cookie and vars file names. Defaults to "get_market"')

    # Parse the command line.
    args = parser.parse_args()

    return args

def add_station(system, station, distance=0.0):
    '''
    Add a station to data/Station.csv, and sort it.
    This is a real PITA because the Python csv module sucks, and TD basically
    does its own thing.
    '''

    # Be OS friendly
    csvFileName = os.path.abspath('data/Station.csv')

    # Open the current csv
    reader = csv.reader(
        open(csvFileName, 'r'),
        delimiter=',',
        quotechar="'",
        doublequote=True
    )

    # Pull in the field names, in case they change again
    fieldnames = next(reader)

    # Pull in all the rows, casing them to proper types
    result = [[
        str(x[0]),
        str(x[1]),
        float(x[2])
    ] for x in reader]

    # Append the new station
    result.append(
        [
            str(system),
            str(station),
            float(distance)
        ]
    )

    # Sort the list
    result.sort(
        key=lambda k: (
            k[0].lower(),
            k[1].lower()
        )
    )

    # Open Station.csv for write
    fh = open(csvFileName, 'w')

    # csv writer
    writer = csv.writer(
        fh,
        delimiter=',',
        quotechar="'",
        doublequote=True,
        quoting=csv.QUOTE_NONNUMERIC,
        lineterminator="\n"
    )

    # Manually write the field names. The stupid csv module wants to quote
    # these, but TD doesn't want that.
    fh.write(fieldnames[0]+','+fieldnames[1]+','+fieldnames[2]+'\n')

    # Write out the sorted station list
    writer.writerows(result)

#----------------------------------------------------------------
# Classes.
#----------------------------------------------------------------

# Some fun shell colors.
class bcolors:
    if platform.system() is not 'Windows':
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
    else:
        HEADER = ''
        OKBLUE = ''
        OKGREEN = ''
        WARNING = ''
        FAIL = ''
        ENDC = ''

class EDAPI:
    '''
    A class that handles the Frontier ED API.
    '''

    _agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Mobile/12B411'
    _baseurl = 'https://companion.orerve.net/'
    _basename = 'get_market'
    _cookiefile = _basename + '.cookies'
    _envfile = _basename + '.vars'

    def __init__(self, args):
        '''
        Initialize
        '''

        self.args = args

        # Build common file names from basename.
        self._basename = args.basename
        self._cookiefile = self._basename + '.cookies'
        self._envfile = self._basename + '.vars'

        if self.args.debug:
            debug = 1
        else:
            debug = 0

        # Create the cookie jar.
        self.cookie = http.cookiejar.MozillaCookieJar(self._cookiefile)
        try:
            self.cookie.load(ignore_discard=True, ignore_expires=True)
        except:
            self.cookie.save(ignore_discard=True, ignore_expires=True)

        # Setup a custom opener.
        self.opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(self.cookie),
            urllib2.HTTPRedirectHandler(),
            urllib2.HTTPHandler(debuglevel=debug),
            urllib2.HTTPSHandler(debuglevel=debug),
        )

        self.opener.addheaders = [
            ('User-Agent', self._agent),
        ]

        urllib2.install_opener(self.opener)

        # Grab the commander profile
        response = self._getURI('profile').read().decode()
        try:
            self.profile = json.loads(response)
        except:
            sys.exit('Unable to parse JSON response for /profile!\
                     Try with --debug and report this.')

        if self.args.debug:
            pprint(self.profile)


    def _getBasicURI(self, uri, values=None):
        '''
        Perform a GET/POST to a URI with proper login and
        debug handling.
        '''

        # Encode any post variables.
        if values is None:
            data = None
        else:
            data = urllib.parse.urlencode(values)
            data = data.encode('utf-8')

        # Debug info for the GET/POST.
        if self.args.debug:
            print(bcolors.OKBLUE+'-----')
            if data is None:
                print('GET: ', end='')
                print(self._baseurl+uri, bcolors.ENDC)
            else:
                print('POST: ', end='')
                print(self._baseurl+uri, data, bcolors.ENDC)

        # Open the URL.
        if data is None:
                response = self.opener.open(self._baseurl+uri)
        else:
                response = self.opener.open(self._baseurl+uri, data)

        # Debug info for the response.
        if self.args.debug:
            print(bcolors.HEADER+'-----')
            print('HTTP', response.code)
            print(response.url)
            print()
            print(response.info(), bcolors.OKGREEN)
            print(bcolors.ENDC)

        # Save the cookies.
        self.cookie.save(ignore_discard=True, ignore_expires=True)

        # Return the response object.
        return response

    def _getURI(self, uri, values=None):
        '''
        Perform a GET/POST and make sure the login
        cookies are valid
        '''

        # Try the URL. If our credentials are no good, try to
        # login then ask again.

        response = self._getBasicURI(uri, values=values)

        if str(response.url).endswith('user/login'):
            self._doLogin()
            response = self._getBasicURI(uri, values)

        if str(response.url).endswith('user/login'):
            sys.exit("Something went terribly wrong. The login credentials\
                     appear correct, but we are being denied access.\n\
                     Try using --debug and report this.")

        return response

    def _doLogin(self):
        '''
        Go though the login process
        '''
        # First hit the login page to get our auth cookies set.
        response = self._getBasicURI('')

        # Our current cookies look okay? No need to login.
        if str(response.url).endswith('/'):
            if self.args.debug:
                print('Current auth is valid!')
            return

        # Performe the login POST.
        values = {}
        values['email'] = input("User Name (email):")
        values['password'] = getpass.getpass()
        response = self._getBasicURI('user/login', values=values)

        # If we end up being redirected back to login,
        # the login failed.
        if str(response.url).endswith('user/login'):
            sys.exit('Login failed.')

        # Check to see if we need to do the auth token dance.
        if str(response.url).endswith('user/confirm'):
            print()
            print("A verification code should have been sent to your email address.")
            print("Please provide that code (case sensitive!)")
            values = {}
            values['code'] = input("Code:")
            response = self._getBasicURI('user/confirm', values=values)

#----------------------------------------------------------------
# Main.
#----------------------------------------------------------------


def Main(args):
    '''
    Main function.
    '''

    # Connect tot the API and grab all the info!
    api = EDAPI(args)

    # Print the commander profile
    print('Commander:', bcolors.OKGREEN+api.profile['commander']['name']+bcolors.ENDC)
    print('Credits  : {:>11,d}'.format(api.profile['commander']['credits']))
    print('Debt     : {:>11,d}'.format(api.profile['commander']['debt']))
    print('Insurance: {:>11,d}'.format(api.profile['stats']['ship']['insurance']['value']))
    print('Capacity : {} tons'.format(api.profile['ship']['cargo']['capacity']))
    print('Ranks    :')
    print('\t    Combat:', api.profile['commander']['rank']['combat'])
    print('\t     Trade:', api.profile['commander']['rank']['trade'])
    print('\t     Crime:', api.profile['commander']['rank']['crime'])
    print('\t   Explore:', api.profile['commander']['rank']['explore'])
    print('\t   Service:', api.profile['commander']['rank']['service'])
    print('\tFederation:', api.profile['commander']['rank']['empire'])
    print('\t    Empire:', api.profile['commander']['rank']['federation'])
    print('Docked:', api.profile['commander']['docked'])

    # Sanity check that we are docked
    if not api.profile['commander']['docked']:
        print(bcolors.WARNING+'Commander not docked.'+bcolors.ENDC)
        print(bcolors.FAIL+'Aborting!'+bcolors.ENDC)
        sys.exit(1)

    system = api.profile['lastSystem']['name']
    station = api.profile['lastStarport']['name']
    print('System:', bcolors.OKBLUE+system+bcolors.ENDC)
    print('Station:', bcolors.OKBLUE+station+bcolors.ENDC)

    # Some sanity checking on the market
    if 'commodities' not in api.profile['lastStarport']:
        print(bcolors.FAIL+'This station does not appear to have a commodity market.'+bcolors.ENDC)
        print('Keys for this station:')
        pprint(api.profile['lastStarport'].keys())
        sys.exit(1)

    # Write out an environment file.
    if args.vars:
        print('Writing {}...'.format(api._envfile))
        with open(api._envfile, "w") as myfile:
            myfile.write('export TDFROM="{}/{}"\n'.format(
                    api.profile['lastSystem']['name'],
                    api.profile['lastStarport']['name']
                )
            )
            myfile.write('export TDCREDITS={}\n'.format(
                    api.profile['commander']['credits']
                )
            )
            myfile.write('export TDINS={}\n'.format(
                    api.profile['stats']['ship']['insurance']['value']
                )
            )
            myfile.write('export TDCAP={}\n'.format(
                    api.profile['ship']['cargo']['capacity']
                )
            )

    # Check to see if this system is in the Stations file
    myfile = csv.DictReader(open(os.path.abspath('data/Station.csv')),
                            quotechar="'",
                            fieldnames=('system',
                                        'station',
                                        'dist'
                                       )
                           )
    found = False
    for row in myfile:
        if (row['system'].lower() == system.lower() and
            row['station'].lower() == station.lower()):
            found = True
            break

    # The station isn't in the stations file. Prompt to add it.
    if not found:
        print(bcolors.WARNING+'WARNING! Station not in station file.'+bcolors.ENDC)
        print('Add this station to Station.csv? (Be SURE this is correct!)')
        r = input("Type YES: ")
        if r != 'YES':
            print(bcolors.FAIL+'Aborting!'+bcolors.ENDC)
            sys.exit(1)
        add_station(system, station)
    else:
        print(bcolors.OKGREEN+'Station found in station file.'+bcolors.ENDC)

    # Station exists. Prompt for import.
    print('Import station market with the current time stamp?')
    r = input("Type YES: ")
    if r != 'YES':
        print(bcolors.FAIL+'Aborting!'+bcolors.ENDC)
        sys.exit(1)

    print('Writing trade data...')

    # Find a temp file
    f = tempfile.NamedTemporaryFile(delete=False)
    if args.debug:
        print('Temp file is:', f.name)

    # Write out trade data
    f.write("@ {}/{}\n".format(system, station).encode('UTF-8'))
    for commodity in api.profile['lastStarport']['commodities']:
        if commodity['categoryname'] in skip_categories:
            continue

        if commodity['categoryname'] in cat_corrections:
            commodity['categoryname'] = cat_corrections[commodity['categoryname']]

        if commodity['name'] in comm_corrections:
            commodity['name'] = comm_corrections[commodity['name']]

        f.write(
            "\t+ {}\n".format(
                commodity['categoryname']
            ).encode('UTF-8')
        )

        # If stock is zero, list it as unavailable.
        # Otherwise record stock at an unknown demand.
        # TODO: figure out how to calculate demand.
        if commodity['stock'] == 0:
            commodity['stock'] = '-'
        else:
            commodity['stock'] = str(commodity['stock'])+'?'

        f.write(
            "\t\t{} {} {} ? {}\n".format(
                commodity['name'],
                commodity['sellPrice'],
                commodity['buyPrice'],
                commodity['stock'],
            ).encode('UTF-8')
        )
    f.close()

    # All went well. Let's load up TradeDangerous and try
    # to load the prices.
    print('Importing into TradeDangerous...')

    # Setup TD
    import tradeenv
    tdenv = tradeenv.TradeEnv()
    import tradedb
    tdb = tradedb.TradeDB(tdenv)
    import cache

    # TD likes to use Path objects
    fpath = Path(f.name)

    # Ask TD to parse the system from the temp file.
    cache.importDataFromFile(tdb, tdenv, fpath)

    # Remove the temp file.
    if not args.debug:
        fpath.unlink()

    # No errors.
    return False

#----------------------------------------------------------------
# __main__
#----------------------------------------------------------------
if __name__ == "__main__":
    '''
    Command line invocation.
    '''

    try:
        # Parse any command line arguments.
        args = parse_args()

        # Command line overrides
        if args.debug is True:
            print('***** Debug mode *****')

        # Execute the Main() function and return results.
        sys.exit(Main(args))
    except SystemExit as e:
        # Clean exit, provide a return code.
        sys.exit(e.code)
    except urllib2.HTTPError as e:
        print('HTTP error:', str(e.code))
    except:
        # Handle all other exceptions.
        ErrStr = traceback.format_exc()
        print('Exception in main loop. Exception info below:')
        sys.exit(ErrStr)
