#!/usr/bin/env python
#----------------------------------------------------------------
# Elite: Dangerous Market Scraper
#----------------------------------------------------------------

import argparse
import csv
from datetime import datetime
from datetime import tzinfo
import getpass
import http.client
import http.cookiejar
import json
import os
from pathlib import Path
import platform
from pprint import pprint
import sqlite3
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

# Categories to ignore. Drones end up here. No idea what they are.
cat_ignore = [
        'NonMarketable',
]

# TD has different names for these.
cat_correct = {
        'Narcotics': 'Legal Drugs'
}

# Commodities to ignore. Don't try to pass these to TD. This is mostly for
# rares.
comm_ignore = (
    'Alien Eggs',
    'Lavian Brandy',
)

# TD has different names for these.
comm_correct = {
        'Agricultural Medicines': 'Agri-Medicines',
        'Atmospheric Extractors': 'Atmospheric Processors',
        'Auto Fabricators': 'Auto-Fabricators',
        'Basic Narcotics': 'Narcotics',
        'Bio Reducing Lichen': 'Bioreducing Lichen',
        'Hazardous Environment Suits': 'H.E. Suits',
        'Heliostatic Furnaces': 'Microbial Furnaces',
        'Marine Supplies': 'Marine Equipment',
        'Non Lethal Weapons': 'Non-Lethal Weapons',
        'Terrain Enrichment Systems': 'Land Enrichment Systems',
}

#----------------------------------------------------------------
# Some lookup tables.
#----------------------------------------------------------------

bracket_levels = ('-', 'L', 'M', 'H')

# This translates what the API calls a ship into what TD calls a
# ship.

ship_names = {
    'Adder': 'Adder',
    'Anaconda': 'Anaconda',
    'Asp': 'Asp Explorer',
    'CobraMkIII': 'Cobra',
    'Eagle': 'Eagle',
    'Empire_Fighter': 'Empire_Fighter',
    'Empire_Trader': 'Clipper',
    'Federation_Dropship': 'Dropship',
    'Federation_Fighter': 'Federation_Fighter',
    'Hauler': 'Hauler',
    'Orca': 'Orca',
    'Python': 'Python',
    'SideWinder': 'Sidewinder',
    'Type6': 'Lakon Type 6',
    'Type7': 'Lakon Type 7',
    'Type9': 'Lakon Type 9',
    'Viper': 'Viper',
}

rank_names = {
    'combat': (
        'Harmless',
        'Mostly Harmless',
        'Novice',
        'Competent',
        'Expert',
        'Master',
        'Dangerous',
        'Deadly',
        'Elite',
    ),
    'crime': (
        'Rank 0',
        'Rank 1',
        'Rank 2',
        'Rank 3',
        'Rank 4',
        'Rank 5',
        'Rank 6',
        'Rank 7',
        'Rank 8',
    ),
    'empire': (
        'None',
        'Outsider',
        'Serf',
        'Master',
        'Squire',
        'Knight',
        'Lord',
        'Baron',
        'Viscount',
        'Count',
        'Earl',
    ),
    'explore': (
        'Aimless',
        'Mostly Aimless',
        'Scout',
        'Surveyor',
        'Trailblazer',
        'Pathfinder',
        'Ranger',
        'Starblazer',
        'Elite',
    ),
    'federation': (
        'None',
        'Recruit',
        'Cadet',
        'Midshipman',
        'Petty Officer',
        'Chief Petty Officer',
        'Warrant Officer',
        'Ensign',
        'Lieutenant',
        'Lieutenant Commander',
        'Post Commander',
    ),
    'service': (
        'Rank 0',
        'Rank 1',
        'Rank 2',
        'Rank 3',
        'Rank 4',
        'Rank 5',
        'Rank 6',
        'Rank 7',
        'Rank 8',
    ),
    'trade': (
        'Penniless',
        'Mostly Penniless',
        'Pedlar',
        'Dealer',
        'Merchant',
        'Broker',
        'Entrepreneur',
        'Tycoon',
        'Elite',
    ),
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
                        for current cargo capacity, credits, and current\
                        system/station.")

    # Base file name. 
    parser.add_argument("--basename",
                        default="edms",
                        help='Base file name. This is used to construct the\
                        cookie and vars file names. Defaults to "edms"')

    # tdpath
    parser.add_argument("--tdpath",
                        default=".",
                        help="Path to the TradeDangerous root. This is used to\
                        locate the TradeDangerous python modules and data/\
                        directory. Defaults to the cwd.")

    # colors
    parser.add_argument("--no-color",
                        dest="color",
                        action="store_false",
                        default=True,
                        help="Disable the use of ansi colors in output.")

    # keys
    parser.add_argument("--keys",
                        action="append",
                        nargs="*",
                        help="Instead of normal import, display raw API data\
                        given a set of dictionary keys.")

    # tree
    parser.add_argument("--tree",
                        action="store_true",
                        default=False,
                        help="Used with --keys. If present will print all\
                        content below the specificed key.")

    # Parse the command line.
    args = parser.parse_args()

    # Fixup the tdpath
    if args.tdpath is not '.':
        args.tdpath = os.path.abspath(args.tdpath)

    if args.debug:
        pprint(args)

    return args


def read_ship_vendors():
    '''
    Read the ShipVendor CSV.
    Returns a list of lists for feeding into the CSV writer later.
    '''

    # Be OS friendly
    csvFileName = os.path.abspath(args.tdpath+'/data/ShipVendor.csv')

    # Open the current csv
    reader = csv.reader(
        open(csvFileName, 'r'),
        delimiter=',',
        quotechar="'",
        doublequote=True
    )

    # Pull in the field names, in case they change again
    fieldnames = next(reader)

    # Pull in all the rows, casting them to proper types
    result = [[
        str(x[0]).upper(),
        str(x[1]),
        str(x[2])
    ] for x in reader]

    return fieldnames, result


def write_ship_vendors(fieldnames, vendors):
    '''
    Write out the ShipVendors CSV file given a list.
    '''

    # Be OS friendly
    csvFileName = os.path.abspath(args.tdpath+'/data/ShipVendor.csv')

    # Sort the list
    vendors.sort(
        key=lambda k: (
            k[0].lower(),
            k[1].lower(),
            k[2].lower()
        )
    )

    # Open /data/ShipVendor.csv for write
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

    # Write out the sorted ship list
    writer.writerows(vendors)


def add_ship_vendor(system, station, ships, fieldnames=None, vendors=None
    ):
    '''
    Add a list of ships to ShipVenddor.csv, and sort it.
    '''

    # Check to see if we were given the data. If not,
    # go read it.
    if fieldnames is None or vendors is None:
        (fieldnames, vendors) = read_ship_vendors()

    # TD keeps systems in upper case. No idea why.
    system = system.upper()

    # for each ship, make sure it's in the list.
    for ship in ships:
        # Translate the name.
        ship = ship_names[ship]

        # check the list
        if [system, station, ship] not in vendors:
            vendors.append(
                [
                    str(system),
                    str(station),
                    str(ship),
                ]
            )

    # Write out the file.
    write_ship_vendors(fieldnames, vendors)


def convertSecs(seconds):
    '''
    Convert a number of seconds to a string.
    '''
    if not isinstance(seconds, int):
        return seconds 

    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    result = "{:2d}s".format(
        seconds
    )

    if minutes or hours:
        result = "{:2d}m ".format(
            minutes
        )+result

    if hours:
        result = "{:2d}h ".format(
            hours
        )+result

    return result


#----------------------------------------------------------------
# Classes.
#----------------------------------------------------------------

# Some fun shell colors.
class ansiColors:
    '''
    Simple class for ansi colors
    '''

    defaults = {
        'HEADER': '\033[95m',
        'OKBLUE': '\033[94m',
        'OKGREEN': '\033[92m',
        'WARNING': '\033[93m',
        'FAIL': '\033[91m',
        'ENDC': '\033[00m',
    }

    def __init__(self):
        if args.color:
            self.__dict__.update(ansiColors.defaults)
        else:
            self.__dict__.update({n: '' for n in ansiColors.defaults.keys()})


class EDAPI:
    '''
    A class that handles the Frontier ED API.
    '''

    _agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Mobile/12B411'
    _baseurl = 'https://companion.orerve.net/'
    _basename = 'edms'
    _cookiefile = _basename + '.cookies'
    _envfile = _basename + '.vars'


    def __init__(self):
        '''
        Initialize
        '''

        self.args = args

        # Bash colors.
        self.c = ansiColors()

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
            print(self.c.OKBLUE+'-----')
            if data is None:
                print('GET: ', end='')
                print(self._baseurl+uri, self.c.ENDC)
            else:
                print('POST: ', end='')
                print(self._baseurl+uri, data, self.c.ENDC)

        # Open the URL.
        if data is None:
                response = self.opener.open(self._baseurl+uri)
        else:
                response = self.opener.open(self._baseurl+uri, data)

        # Debug info for the response.
        if self.args.debug:
            print(self.c.HEADER+'-----')
            print('HTTP', response.code)
            print(response.url)
            print()
            print(response.info(), self.c.OKGREEN)
            print(self.c.ENDC)

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

def Main():
    '''
    Main function.
    '''
    # Insert the tdpath to python path so we can find the proper modules to
    # import.
    sys.path.insert(0, args.tdpath)

    # Connect to the API and grab all the info!
    api = EDAPI()

    # Colors
    c = ansiColors()

    # Print the commander profile
    print('Commander:', c.OKGREEN+api.profile['commander']['name']+c.ENDC)
    print('Game Time: {:>12}'.format(convertSecs(api.profile['stats']['game_time'])))
    print('Credits  : {:>12,d}'.format(api.profile['commander']['credits']))
    print('Debt     : {:>12,d}'.format(api.profile['commander']['debt']))
    print('Capacity : {} tons'.format(api.profile['ship']['cargo']['capacity']))
    print("+------------+------------------+---+---------------+---------------------+")
    print("|  Rank Type |        Rank Name | # |     Game Time |           Timestamp |")
    print("+------------+------------------+---+---------------+---------------------+")
    r = api.profile['stats']['ranks']
    for rankType in sorted(api.profile['commander']['rank']):
        rank = api.profile['commander']['rank'][rankType]
        if rankType in rank_names:
            rankName = rank_names[rankType][rank]
        else:
            rankName = ''
        if rankType in r:
            maxGT = max([r[rankType][x]['gt'] for x in r[rankType].keys()])
            maxTS = max([r[rankType][x]['ts'] for x in r[rankType].keys()])
        else:
            maxGT = ''
            maxTS = 0
        if maxTS:
            maxTS = datetime.fromtimestamp(maxTS).isoformat()
        else:
            maxTS = ''
        print("| {:>10} | {:>16} | {:1} | {:>13} | {:19} |".format(
            rankType,
            rankName,
            rank,
            convertSecs(maxGT),
            maxTS
            )
        )
    print("+------------+------------------+---+---------------+---------------------+")
    print('Docked:', api.profile['commander']['docked'])

    # User specified the --keys option. Use this to display some subzet of the
    # API response and exit.
    if args.keys is not None:
        # A little legend.
        for key in args.keys[0]:
            print(key, end="->")
        print()

        # Start a thr root
        ref = api.profile
        # Try to walk the tree
        for key in args.keys[0]:
            try:
                ref = ref[key]
            except:
                print("key:", key)
                print("not found. Contents at previous key:")
                try:
                    pprint(sorted(ref.keys()))
                except:
                    pprint(ref)
                sys.exit(1)
        # Print whatever we found here.
        try:
            if args.tree:
                pprint(ref)
            else:
                pprint(sorted(ref.keys()))
        except:
            pprint(ref)
        # Exit without doing anything else.
        sys.exit()

    # Sanity check that we are docked
    if not api.profile['commander']['docked']:
        print(c.WARNING+'Commander not docked.'+c.ENDC)
        print(c.FAIL+'Aborting!'+c.ENDC)
        sys.exit(1)

    system = api.profile['lastSystem']['name']
    station = api.profile['lastStarport']['name']
    print('System:', c.OKBLUE+system+c.ENDC)
    print('Station:', c.OKBLUE+station+c.ENDC)

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
            myfile.write('export TDCAP={}\n'.format(
                    api.profile['ship']['cargo']['capacity']
                )
            )

    # Setup TD
    print ('Initializing TradeDangerous...')
    import tradeenv
    tdenv = tradeenv.TradeEnv()
    if args.tdpath is not '.':
        tdenv.dataDir = args.tdpath+'/data'
    import tradedb
    tdb = tradedb.TradeDB(tdenv)
    import cache
    import csvexport

    # Check to see if this system is in the Stations file
    try:
        station_lookup = tdb.lookupStation(station, system)
    except:
        station_lookup = None

    # The station isn't in the stations file. Add it.
    if not station_lookup:
        print(c.WARNING+'WARNING! Station unknown.'+c.ENDC)
        print('Adding station...')
        lsFromStar = int(input("Distance from star (enter for 0): ")) or 0
        blackMarket = input("Black market present (Y, N or enter for ?): ") or '?'
        maxPadSize = input("Max pad size (S, M, L or enter for ?): ") or '?'
        system_lookup = tdb.lookupSystem(system)
        if tdb.addLocalStation(
            system = system_lookup,
            name = station,
            lsFromStar = lsFromStar,
            blackMarket = blackMarket,
            maxPadSize = maxPadSize,
        ):
            lines, csvPath = csvexport.exportTableToFile(
                tdb,
                tdenv,
                "Station"
            )
            tdenv.NOTE("{} updated.", csvPath)
    else:
        print(c.OKGREEN+'Station found in station file.'+c.ENDC)

        # See if we need to update the info for this station.
        lsFromStar = station_lookup.lsFromStar
        blackMarket = station_lookup.blackMarket
        maxPadSize = station_lookup.maxPadSize

        if lsFromStar == 0:
            lsFromStar = int(input("Update distance from star (enter for 0): ")) or 0
        if blackMarket is '?':
            blackMarket = input("Update black market present (Y, N or enter for ?): ") or '?'
        if maxPadSize is '?':
            maxPadSize = input("Update max pad size (S, M, L or enter for ?): ") or '?'
        if (lsFromStar != station_lookup.lsFromStar or
            blackMarket != station_lookup.blackMarket or
            maxPadSize != station_lookup.maxPadSize):
            if tdb.updateLocalStation(
                station = station_lookup,
                lsFromStar = lsFromStar,
                blackMarket = blackMarket,
                maxPadSize = maxPadSize,
            ):
                lines, csvPath = csvexport.exportTableToFile(
                    tdb,
                    tdenv,
                    "Station"
                )
                tdenv.NOTE("{} updated.", csvPath)

    # If a shipyard exists, update the ship vendor csv
    if 'ships' in api.profile['lastStarport']:
        print('Updating shipyard vendor...')
        ships = api.profile['lastStarport']['ships']['shipyard_list']
        add_ship_vendor(system, station, ships)

    # Some sanity checking on the market
    if 'commodities' not in api.profile['lastStarport']:
        print(c.FAIL+'This station does not appear to have a commodity market.'+c.ENDC)
        print('Keys for this station:')
        pprint(api.profile['lastStarport'].keys())
        sys.exit(1)

    # Station exists. Import.
    # Grab the old prices so we can print a comparison.
    conn = sqlite3.connect(os.path.abspath(args.tdpath+'/data/TradeDangerous.db'))
    conn.execute("PRAGMA foreign_keys=ON")
    cur  = conn.cursor()

    oldPrices = {n: (s, b) for (n, s, b) in cur.execute(
        """
        SELECT
            Item.name,
            vPrice.sell_to,
            vPrice.buy_from
        FROM
            vPrice,
            System,
            Station,
            Item
        WHERE
            Item.item_id = vPrice.item_id AND
            System.name = '{}' AND
            Station.name = '{}' AND
            System.system_id = Station.system_id AND
            Station.station_id = vPrice.station_id
        ORDER BY Item.ui_order
        """.format(
            system,
            station
            )
    )}

    print('Writing trade data...')

    # Find a temp file
    f = tempfile.NamedTemporaryFile(delete=False)
    if args.debug:
        print('Temp file is:', f.name)

    # Write out trade data
    header = False
    f.write("@ {}/{}\n".format(system, station).encode('UTF-8'))
    for commodity in api.profile['lastStarport']['commodities']:
        if commodity['categoryname'] in cat_ignore:
            continue

        if commodity['name'] in comm_ignore:
            continue

        if commodity['categoryname'] in cat_correct:
            commodity['categoryname'] = cat_correct[commodity['categoryname']]

        if commodity['name'] in comm_correct:
            commodity['name'] = comm_correct[commodity['name']]

        f.write(
            "\t+ {}\n".format(
                commodity['categoryname']
            ).encode('UTF-8')
        )

        # If stock is zero, list it as unavailable.
        if commodity['stock'] == 0:
            commodity['stock'] = '-'
        else:
            demand = bracket_levels[int(commodity['stockBracket'])]
            commodity['stock'] = str(int(commodity['stock']))+demand

        # If demand is zero, list it as unknown. This is required, or TD will
        # zero out the sell price.
        if commodity['demandBracket'] == 0:
            commodity['demand'] = '?'
        else:
            demand = bracket_levels[int(commodity['demandBracket'])]
            commodity['demand'] = str(int(commodity['demand']))+demand

        # Print price differences
        oldCom = oldPrices.get(commodity['name'], (0,0))
        diffSell = commodity['sellPrice'] - oldCom[0]
        diffBuy = commodity['buyPrice'] - oldCom[1]

        # Only print if the prices changed.
        if (diffSell != 0 or diffBuy != 0):
            if header is False:
                header = True
                print("{:>25} {:>13} {:>13}".format(
                    'Commodity',
                    'Sell Price',
                    'Buy Price'
                ))
            if diffSell < 0:
                sellColor = c.FAIL
            elif diffSell > 0:
                sellColor = c.OKGREEN
            else:
                sellColor = c.ENDC
            if diffBuy > 0:
                buyColor = c.FAIL
            elif diffBuy < 0:
                buyColor = c.OKGREEN
            else:
                buyColor = c.ENDC
            if args.color:
                s = "{:>25} {:>5}{:<17} {:>5}{:<17}"
            else:
                s = "{:>25} {:>5}{:<8} {:>5}{:<8}"
            print(s.format(
                commodity['name'],
                commodity['sellPrice'],
                '('+sellColor+"{:+d}".format(diffSell)+c.ENDC+')',
                commodity['buyPrice'],
                '('+buyColor+"{:+d}".format(diffBuy)+c.ENDC+')'
                )
            )

        f.write(
            "\t\t{} {} {} {} {}\n".format(
                commodity['name'],
                commodity['sellPrice'],
                commodity['buyPrice'],
                commodity['demand'],
                commodity['stock'],
            ).encode('UTF-8')
        )
    f.close()

    # All went well. Try the import.
    print('Importing into TradeDangerous...')

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
        test = args

        # Command line overrides
        if args.debug is True:
            print('***** Debug mode *****')

        # Execute the Main() function and return results.
        sys.exit(Main())
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
