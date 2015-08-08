#!/usr/bin/env python
# ----------------------------------------------------------------
# Elite: Dangerous API Tool
# ----------------------------------------------------------------

import argparse
from datetime import datetime
import getpass
import json
import os
from pathlib import Path
import platform
import pickle
from pprint import pprint
import requests
from requests.utils import dict_from_cookiejar
from requests.utils import cookiejar_from_dict
import sys
import tempfile
import textwrap
import traceback

import eddn

__version_info__ = ('3', '2', '1')
__version__ = '.'.join(__version_info__)

# ----------------------------------------------------------------
# Deal with some differences in names between TD, ED and the API.
# ----------------------------------------------------------------

# Categories to ignore. Drones end up here. No idea what they are.
cat_ignore = [
    'NonMarketable',
]

# TD has different names for these.
cat_correct = {
    'Narcotics': 'Legal Drugs',
    'Slaves': 'Slavery',
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
    'S A P8 Core Container': 'SAP 8 Core Container',
    'Terrain Enrichment Systems': 'Land Enrichment Systems',
}

# ----------------------------------------------------------------
# Some lookup tables.
# ----------------------------------------------------------------

bracket_levels = ('-', 'L', 'M', 'H')

# This translates what the API calls a ship into what TD calls a
# ship.

ship_names = {
    'Adder': 'Adder',
    'Anaconda': 'Anaconda',
    'Asp': 'Asp',
    'CobraMkIII': 'Cobra',
    'DiamondBack': 'Diamondback Scout',
    'DiamondBackXL': 'Diamondback Explorer',
    'Eagle': 'Eagle',
    'Empire_Courier': 'Imperial Courier',
    'Empire_Fighter': 'Empire_Fighter',
    'Empire_Trader': 'Clipper',
    'Federation_Dropship': 'Dropship',
    'Federation_Fighter': 'Federation_Fighter',
    'FerDeLance': 'Fer-de-Lance',
    'Hauler': 'Hauler',
    'Orca': 'Orca',
    'Python': 'Python',
    'SideWinder': 'Sidewinder',
    'Type6': 'Type 6',
    'Type7': 'Type 7',
    'Type9': 'Type 9',
    'Viper': 'Viper',
    'Vulture': 'Vulture',
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
        'Marquis',
        'Duke',
        'Prince',
        'King',
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
        'Post Captain',
        'Rear Admiral',
        'Vice Admiral',
        'Admiral',
    ),
    'service': (
        'Rank 0',
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

# ----------------------------------------------------------------
# Functions.
# ----------------------------------------------------------------


def parse_args():
    '''
    Parse arguments.
    '''
    # Basic argument parsing.
    parser = argparse.ArgumentParser(
        description='EDAPI: Elite Dangerous API Tool',
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
                        help="Output additional debug info.")

    # JSON
    parser.add_argument("--import",
                        metavar="FILE",
                        dest="json_file",
                        default=None,
                        help="Import API info from a JSON file instead of the\
                        API. Used mostly for debugging purposes.")

    # EDDN
    parser.add_argument("--eddn",
                        action="store_true",
                        default=False,
                        help="Post prices to the EDDN.")

    # Export
    parser.add_argument("--export",
                        metavar="FILE",
                        default=None,
                        help="Export API response to a file as JSON.")

    # vars file
    parser.add_argument("--vars",
                        action="store_true",
                        default=False,
                        help="Output a file that sets environment variables\
                        for current cargo capacity, credits, and current\
                        system/station.")

    # Base file name.
    parser.add_argument("--basename",
                        default="edapi",
                        help='Base file name. This is used to construct the\
                        cookie and vars file names.')

    # tdpath
    parser.add_argument("--tdpath",
                        default=".",
                        help="Path to the Trade Dangerous root. This is used to\
                        locate the Trade Dangerous python modules and data/\
                        directory.")

    # colors
    default = (platform.system() == 'Windows')
    parser.add_argument("--no-color",
                        dest="nocolor",
                        action="store_true",
                        default=default,
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


# ----------------------------------------------------------------
# Classes.
# ----------------------------------------------------------------

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
        if args.nocolor:
            self.__dict__.update({n: '' for n in ansiColors.defaults.keys()})
        else:
            self.__dict__.update(ansiColors.defaults)


class EDAPI:
    '''
    A class that handles the Frontier ED API.
    '''

    _agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Mobile/12B411'  # NOQA
    _baseurl = 'https://companion.orerve.net/'
    _basename = 'edapi'
    _cookiefile = _basename + '.cookies'
    _envfile = _basename + '.vars'

    def __init__(
        self,
        basename='edapi',
        debug=False,
        cookiefile=None,
        json_file=None
    ):
        '''
        Initialize
        '''

        # Build common file names from basename.
        self._basename = basename
        if cookiefile:
            self._cookiefile = cookiefile
        else:
            self._cookiefile = self._basename + '.cookies'

        self._envfile = self._basename + '.vars'

        self.debug = debug

        # If json_file was given, just load that instead.
        if json_file:
            with open(json_file) as file:
                self.profile = json.load(file)
                return

        # if self.debug:
        #     import http.client
        #     http.client.HTTPConnection.debuglevel = 3

        # Setup the HTTP session.
        self.opener = requests.Session()

        self.opener.headers = {
            'User-Agent': self._agent
        }

        # Read/create the cookie jar.
        if os.path.exists(self._cookiefile):
            try:
                with open(self._cookiefile, 'rb') as h:
                    self.opener.cookies = cookiejar_from_dict(pickle.load(h))
            except:
                print('Unable to read cookie file.')

        else:
            with open(self._cookiefile, 'wb') as h:
                pickle.dump(dict_from_cookiejar(self.opener.cookies), h)

        # Grab the commander profile
        response = self._getURI('profile')
        try:
            self.profile = response.json()
        except:
            sys.exit('Unable to parse JSON response for /profile!\
                     Try with --debug and report this.')

    def _getBasicURI(self, uri, values=None):
        '''
        Perform a GET/POST to a URI
        '''

        # POST if data is present, otherwise GET.
        if values is None:
            if self.debug:
                print('GET on: ', self._baseurl+uri)
                print(dict_from_cookiejar(self.opener.cookies))
            response = self.opener.get(self._baseurl+uri)
        else:
            if self.debug:
                print('POST on: ', self._baseurl+uri)
                print(dict_from_cookiejar(self.opener.cookies))
            response = self.opener.post(self._baseurl+uri, data=values)

        if self.debug:
            print('Final URL:', response.url)
            print(dict_from_cookiejar(self.opener.cookies))

        # Save the cookies.
        with open(self._cookiefile, 'wb') as h:
            pickle.dump(dict_from_cookiejar(self.opener.cookies), h)

        # Return the response object.
        return response

    def _getURI(self, uri, values=None):
        '''
        Perform a GET/POST and try to login if needed.
        '''

        # Try the URI. If our credentials are no good, try to
        # login then ask again.
        response = self._getBasicURI(uri, values=values)

        if str(response.url).endswith('user/login'):
            self._doLogin()
            response = self._getBasicURI(uri, values=values)

        if str(response.url).endswith('user/login'):
            sys.exit(textwrap.fill(textwrap.dedent("""\
                Something went terribly wrong. The login credentials
                appear correct, but we are being denied access. Sometimes the
                API is slow to update, so if you are authenticating for the
                first time, wait a minute or so and try again. If this
                persists try using --debug and report this.
                """)))

        return response

    def _doLogin(self):
        '''
        Go though the login process
        '''
        # First hit the login page to get our auth cookies set.
        response = self._getBasicURI('')

        # Our current cookies look okay? No need to login.
        if str(response.url).endswith('/'):
            return

        # Perform the login POST.
        print(textwrap.fill(textwrap.dedent("""\
              You do not appear to have any valid login cookies set.
              We will attempt to log you in with your Frontier
              account, and cache your auth cookies for future use.
              THIS WILL NOT STORE YOUR USER NAME AND PASSWORD.
              """)))

        print("\nYour auth cookies will be stored here:")

        print("\n"+self._cookiefile+"\n")

        print(textwrap.fill(textwrap.dedent("""\
            It is advisable that you keep this file secret. It may
            be possible to hijack your account with the information
            it contains.
            """)))

        print(
            "\nIf you are not comfortable with this, "
            "DO NOT USE THIS TOOL."
        )
        print()

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
            print("A verification code should have been sent to your "
                  "email address.")
            print("Please provide that code (case sensitive!)")
            values = {}
            values['code'] = input("Code:")
            response = self._getBasicURI('user/confirm', values=values)


# ----------------------------------------------------------------
# Main.
# ----------------------------------------------------------------

def Main():
    '''
    Main function.
    '''
    # Insert the tdpath to python path so we can find the proper modules to
    # import.
    sys.path.insert(0, args.tdpath)

    # Connect to the API and grab all the info!
    api = EDAPI(debug=args.debug, json_file=args.json_file)

    # User specified --export. Print JSON and exit.
    if args.export:
        with open(args.export, 'w') as outfile:
            json.dump(api.profile, outfile, indent=4, sort_keys=True)
            sys.exit()

    # Colors
    c = ansiColors()

    # User specified the --keys option. Use this to display some subzet of the
    # API response and exit.
    if args.keys is not None:
        # A little legend.
        for key in args.keys[0]:
            print(key, end="->")
        print()

        # Start a the root
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

    # Print the commander profile
    print('Commander:', c.OKGREEN+api.profile['commander']['name']+c.ENDC)
    print('Credits  : {:>12,d}'.format(api.profile['commander']['credits']))
    print('Debt     : {:>12,d}'.format(api.profile['commander']['debt']))
    print('Capacity : {} tons'.format(api.profile['ship']['cargo']['capacity']))  # NOQA
    print("+------------+------------------+---+")  # NOQA
    print("|  Rank Type |        Rank Name | # |")  # NOQA
    print("+------------+------------------+---+")  # NOQA
    for rankType in sorted(api.profile['commander']['rank']):
        rank = api.profile['commander']['rank'][rankType]
        if rankType in rank_names:
            try:
                rankName = rank_names[rankType][rank]
            except:
                rankName = "Rank "+str(rank)
        else:
            rankName = ''
        print("| {:>10} | {:>16} | {:1} |".format(
            rankType,
            rankName,
            rank,
            )
        )
    print("+------------+------------------+---+")  # NOQA
    print('Docked:', api.profile['commander']['docked'])

    system = api.profile['lastSystem']['name']
    station = api.profile['lastStarport']['name']
    print('System:', c.OKBLUE+system+c.ENDC)
    print('Station:', c.OKBLUE+station+c.ENDC)

    # Write out an environment file.
    if args.vars:
        print('Writing {}...'.format(api._envfile))
        with open(api._envfile, "w") as myfile:
            myfile.write(
                'export TDFROM="{}/{}"\n'.format(
                    api.profile['lastSystem']['name'],
                    api.profile['lastStarport']['name']
                )
            )
            myfile.write(
                'export TDCREDITS={}\n'.format(
                    api.profile['commander']['credits']
                )
            )
            myfile.write(
                'export TDCAP={}\n'.format(
                    api.profile['ship']['cargo']['capacity']
                )
            )

    # Setup TD
    print('Initializing Trade Dangerous...')
    try:
        import tradeenv
    except:
        sys.exit('Can\'t find Trade Dangerous. Do you need --tdpath?')
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
        lsFromStar = input(
            "Distance from star (enter for 0): "
        ) or 0
        lsFromStar = int(lsFromStar)
        blackMarket = input(
            "Black market present (Y, N or enter for ?): "
        ) or '?'
        maxPadSize = input(
            "Max pad size (S, M, L or enter for ?): "
        ) or '?'
        outfitting = input(
            "Outfitting present (Y, N or enter for ?): "
        ) or '?'
        rearm = input(
            "Rearm present (Y, N or enter for ?): "
        ) or '?'
        refuel = input(
            "Refuel present (Y, N or enter for ?): "
        ) or '?'
        repair = input(
            "Repair present (Y, N or enter for ?): "
        ) or '?'
        # This is unreliable, so default to unknown.
        if 'commodities' in api.profile['lastStarport']:
            market = 'Y'
        else:
            market = '?'
        # This is also unreliable, so default to unknown.
        if 'ships' in api.profile['lastStarport']:
            shipyard = 'Y'
        else:
            shipyard = '?'
        system_lookup = tdb.lookupSystem(system)
        if tdb.addLocalStation(
            system=system_lookup,
            name=station,
            lsFromStar=lsFromStar,
            blackMarket=blackMarket,
            maxPadSize=maxPadSize,
            market=market,
            shipyard=shipyard,
            outfitting=outfitting,
            rearm=rearm,
            refuel=refuel,
            repair=repair
        ):
            lines, csvPath = csvexport.exportTableToFile(
                tdb,
                tdenv,
                "Station"
            )
            tdenv.NOTE("{} updated.", csvPath)
        station_lookup = tdb.lookupStation(station, system)
    else:
        print(c.OKGREEN+'Station found in station file.'+c.ENDC)

        # See if we need to update the info for this station.
        lsFromStar = station_lookup.lsFromStar
        blackMarket = station_lookup.blackMarket
        maxPadSize = station_lookup.maxPadSize
        market = station_lookup.market
        shipyard = station_lookup.shipyard
        outfitting = station_lookup.outfitting
        rearm = station_lookup.rearm
        refuel = station_lookup.refuel
        repair = station_lookup.repair

        if lsFromStar == 0:
            lsFromStar = input(
                "Update distance from star (enter for 0): "
            ) or 0
            lsFromStar = int(lsFromStar)
        if blackMarket is '?':
            blackMarket = input(
                "Update black market present (Y, N or enter for ?): "
            ) or '?'
        if maxPadSize is '?':
            maxPadSize = input(
                "Update max pad size (S, M, L or enter for ?): "
            ) or '?'
        if outfitting is '?':
            outfitting = input(
                "Update outfitting present (Y, N or enter for ?): "
            ) or '?'
        if rearm is '?':
            rearm = input(
                "Update rearm present (Y, N or enter for ?): "
            ) or '?'
        if refuel is '?':
            refuel = input(
                "Update refuel present (Y, N or enter for ?): "
            ) or '?'
        if repair is '?':
            repair = input(
                "Update repair present (Y, N or enter for ?): "
            ) or '?'
        # This is unreliable, so default to unchanged.
        if 'commodities' in api.profile['lastStarport']:
            market = 'Y'
        # This is also unreliable, so default to unchanged.
        if 'ships' in api.profile['lastStarport']:
            shipyard = 'Y'
        if (
            lsFromStar != station_lookup.lsFromStar or
            blackMarket != station_lookup.blackMarket or
            maxPadSize != station_lookup.maxPadSize or
            market != station_lookup.market or
            shipyard != station_lookup.shipyard or
            outfitting != station_lookup.outfitting or
            rearm != station_lookup.rearm or
            refuel != station_lookup.refuel or
            repair != station_lookup.repair
        ):
            if tdb.updateLocalStation(
                station=station_lookup,
                lsFromStar=lsFromStar,
                blackMarket=blackMarket,
                maxPadSize=maxPadSize,
                market=market,
                shipyard=shipyard,
                outfitting=outfitting,
                rearm=rearm,
                refuel=refuel,
                repair=repair
            ):
                lines, csvPath = csvexport.exportTableToFile(
                    tdb,
                    tdenv,
                    "Station"
                )
                tdenv.NOTE("{} updated.", csvPath)

    # If a shipyard exists, update the ship vendor csv
    if 'ships' in api.profile['lastStarport']:
        print(c.OKBLUE+'Updating shipyard vendor...'+c.ENDC)
        ships = list(
            api.profile['lastStarport']['ships']['shipyard_list'].keys()
        )
        for ship in api.profile['lastStarport']['ships']['unavailable_list']:
            ships.append(ship['name'])
        db = tdb.getDB()
        for ship in ships:
            ship_lookup = tdb.lookupShip(ship_names[ship])
            db.execute("""
                       REPLACE INTO ShipVendor
                       (ship_id, station_id)
                       VALUES
                       (?, ?)
                       """,
                       (ship_lookup.ID, station_lookup.ID))
            db.commit()
        tdenv.NOTE("Updated {} ships in {} shipyard.", len(ships), station)
        lines, csvPath = csvexport.exportTableToFile(
            tdb,
            tdenv,
            "ShipVendor",
        )
        tdenv.NOTE("{} updated.", csvPath)

    # Some sanity checking on the market
    if 'commodities' not in api.profile['lastStarport']:
        print(
            c.FAIL +
            'This station does not appear to have a commodity market.' +
            c.ENDC
        )
        print('Keys for this station:')
        pprint(api.profile['lastStarport'].keys())
        sys.exit(1)

    # Station exists. Import.
    # Grab the old prices so we can print a comparison.
    db = tdb.getDB()
    oldPrices = {n: (s, b) for (n, s, b) in db.execute(
        """
        SELECT
            Item.name,
            StationItem.demand_price,
            StationItem.supply_price
        FROM
            StationItem,
            System,
            Station,
            Item
        WHERE
            Item.item_id = StationItem.item_id AND
            System.name = ? AND
            Station.name = ? AND
            System.system_id = Station.system_id AND
            Station.station_id = StationItem.station_id
        ORDER BY Item.ui_order
        """,
        (
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
    eddn_market = []
    for commodity in api.profile['lastStarport']['commodities']:
        if commodity['categoryname'] in cat_ignore:
            continue

        if commodity['name'] in comm_ignore:
            continue

        if commodity['categoryname'] in cat_correct:
            commodity['categoryname'] = cat_correct[commodity['categoryname']]

        if commodity['name'] in comm_correct:
            commodity['name'] = comm_correct[commodity['name']]

        # Populate EDDN
        if args.eddn:
            eddn_market.append(
                {
                    "name": commodity['name'],
                    "buyPrice": int(commodity['buyPrice']),
                    "supply": int(commodity['stock']),
                    "supplyLevel": eddn.EDDN._levels[int(commodity['stockBracket'])],  # NOQA
                    "sellPrice": int(commodity['sellPrice']),
                    "demand": int(commodity['demand']),
                    "demandLevel": eddn.EDDN._levels[int(commodity['demandBracket'])]  # NOQA
                }
            )

        f.write(
            "\t+ {}\n".format(
                commodity['categoryname']
            ).encode('UTF-8')
        )

        def commodity_int(key):
            try:
                commodity[key] = int(commodity[key])
            except (ValueError, KeyError):
                commodity[key] = 0

        commodity_int('stock')
        commodity_int('demand')
        commodity_int('demandBracket')
        commodity_int('stockBracket')

        # If stock is zero, list it as unavailable.
        if not commodity['stock']:
            commodity['stock'] = '-'
        else:
            demand = bracket_levels[commodity['stockBracket']]
            commodity['stock'] = str(commodity['stock'])+demand

        # If demand is zero or demand bracket is zero, zero the sell price.
        if not (commodity['demand'] and commodity['demandBracket']):
            commodity['demand'] = '?'
            commodity['sellPrice'] = 0
        else:
            demand = bracket_levels[commodity['demandBracket']]
            commodity['demand'] = str(commodity['demand'])+demand

        # Print price differences
        oldCom = oldPrices.get(commodity['name'], (0, 0))
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
            if args.nocolor:
                s = "{:>25} {:>5}{:<8} {:>5}{:<8}"
            else:
                s = "{:>25} {:>5}{:<17} {:>5}{:<17}"
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
    print('Importing into Trade Dangerous...')

    # TD likes to use Path objects
    fpath = Path(f.name)

    # Ask TD to parse the system from the temp file.
    cache.importDataFromFile(tdb, tdenv, fpath)

    # Remove the temp file.
    fpath.unlink()

    # Post to EDDN
    if args.eddn:
        print('Posting prices to EDDN...')
        con = eddn.EDDN(
            api.profile['commander']['name'],
            'EDAPI',
            __version__
        )
        con._debug = args.debug
        con.publishCommodities(
            system,
            station,
            eddn_market
        )

    # No errors.
    return False

# ----------------------------------------------------------------
# __main__
# ----------------------------------------------------------------
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
    except:
        # Handle all other exceptions.
        ErrStr = traceback.format_exc()
        print('Exception in main loop. Exception info below:')
        sys.exit(ErrStr)
