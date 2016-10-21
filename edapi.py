#!/usr/bin/env python
# ----------------------------------------------------------------
# Elite: Dangerous API Tool
# ----------------------------------------------------------------

from pprint import pprint
import argparse
import json
import platform
import sys
import traceback

import companion
import eddn

__version_info__ = ('4', '0', '0')
__version__ = '.'.join(__version_info__)

# ----------------------------------------------------------------
# Deal with some differences in names between TD, ED and the API.
# ----------------------------------------------------------------

# Categories to ignore. Commander specific stuff, like limpets.
cat_ignore = [
    'NonMarketable',
]

# ----------------------------------------------------------------
# Some lookup tables.
# ----------------------------------------------------------------

bracket_levels = ('-', 'L', 'M', 'H')

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

    # colors
    default = (platform.system() == 'Windows')
    parser.add_argument("--no-color",
                        dest="nocolor",
                        action="store_true",
                        default=default,
                        help="Disable the use of ansi colors in output.")

    # Base file name.
    parser.add_argument("--basename",
                        default="edapi",
                        help='Base file name. This is used to construct the\
                        cookie and vars file names.')

    # vars file
    parser.add_argument("--vars",
                        action="store_true",
                        default=False,
                        help="Output a file that sets environment variables\
                        for current cargo capacity, credits, and current\
                        system/station.")

    # Import from JSON
    parser.add_argument("--import",
                        metavar="FILE",
                        dest="json_file",
                        default=None,
                        help="Import API info from a JSON file instead of the\
                        API. Used mostly for debugging purposes.")

    # Export to JSON
    parser.add_argument("--export",
                        metavar="FILE",
                        default=None,
                        help="Export API response to a file as JSON.")

    # EDDN
    parser.add_argument("--eddn",
                        action="store_true",
                        default=False,
                        help="Post price, shipyards, and outfitting to the \
                        EDDN.")

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

    # Hashing CMDR name
    parser.add_argument("--hash",
                        action="store_true",
                        default=False,
                        help="Obfuscate commander name for EDDN.")

    # Force login
    parser.add_argument("--login",
                        action="store_true",
                        default=False,
                        help="Clear any cached user login cookies and force\
                        login. (Doesn't clear the machine token)")

    # Parse the command line.
    args = parser.parse_args()

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


# ----------------------------------------------------------------
# Main.
# ----------------------------------------------------------------


def Main():
    '''
    Main function.
    '''
    # Connect to the API and grab all the info!
    api = companion.EDAPI(
        debug=args.debug,
        json_file=args.json_file,
        login=args.login
    )

    # User specified --export. Print JSON and exit.
    if args.export:
        with open(args.export, 'w') as outfile:
            json.dump(api.profile, outfile, indent=4, sort_keys=True)
            sys.exit()

    # Colors
    c = ansiColors()

    # User specified the --keys option. Use this to display some subset of the
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

    # Process the commodities market.
    eddn_commodities = []
    if 'commodities' in api.profile['lastStarport']:

        def commodity_int(key):
            try:
                ret = int(float(commodity[key])+0.5)
            except (ValueError, KeyError):
                ret = 0
            return ret

        for commodity in api.profile['lastStarport']['commodities']:
            # Ignore any special categories.
            if commodity['categoryname'] in cat_ignore:
                continue

            # Add it to the EDDN list.
            if args.eddn:
                itemEDDN = {
                    "name":          commodity['name'],
                    "meanPrice":     commodity_int('meanPrice'),
                    "buyPrice":      commodity_int('buyPrice'),
                    "stock":         commodity_int('stock'),
                    "stockBracket":  commodity['stockBracket'],
                    "sellPrice":     commodity_int('sellPrice'),
                    "demand":        commodity_int('demand'),
                    "demandBracket": commodity['demandBracket'],
                }
                if len(commodity['statusFlags']) > 0:
                    itemEDDN["statusFlags"] = commodity['statusFlags']
                eddn_commodities.append(itemEDDN)

    # Process shipyard.
    eddn_ships = []
    if 'ships' in api.profile['lastStarport']:

        # Ships that can be purchased.
        if 'shipyard_list' in api.profile['lastStarport']['ships']:
            for ship in api.profile['lastStarport']['ships']['shipyard_list'].values():  # NOQA
                # Add to EDDN.
                eddn_ships.append(ship['name'])

        # Ships that are restricted.
        if 'unavailable_list' in api.profile['lastStarport']['ships']:
            for ship in api.profile['lastStarport']['ships']['unavailable_list']:  # NOQA
                # Add to EDDN.
                eddn_ships.append(ship['name'])

    # Process outfitting.
    eddn_modules = []
    if 'modules' in api.profile['lastStarport']:
        # For EDDN, only add non-commander specific items that can be
        # purchased.
        # https://github.com/jamesremuscat/EDDN/wiki
        for module in api.profile['lastStarport']['modules'].values():
            if (
                module.get('sku', None) in (
                    None,
                    'ELITE_HORIZONS_V_PLANETARY_LANDINGS'
                ) and
                (
                    module['name'].startswith(('Hpt_', 'Int_')) or
                    module['name'].find('_Armour_') > 0
                )
            ):
                eddn_modules.append(module['name'])

    # Publish to EDDN
    if args.eddn:
        # Open a connection.
        con = eddn.EDDN(
            api.profile['commander']['name'],
            not args.hash,
            'EDAPI',
            __version__
        )
        con._debug = args.debug

        if eddn_commodities:
            print('Posting commodities to EDDN...')
            con.publishCommodities(
                system,
                station,
                eddn_commodities
            )

        if eddn_ships:
            print('Posting shipyard to EDDN...')
            con.publishShipyard(
                system,
                station,
                sorted(eddn_ships)
            )

        if eddn_modules:
            print('Posting outfitting to EDDN...')
            con.publishOutfitting(
                system,
                station,
                sorted(eddn_modules)
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
