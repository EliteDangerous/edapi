==============================================================================
EDAPI: Elite Dangerous API Tool
Requires Python 3.4, requests, and Trade Dangerous.
==============================================================================
Automates pulling your profile information from the mobile API, and populating
Trade Dangerous with station, market, and shipyard data. Optionally post info
to the EDDN.

==============================================================================
== Command line usage:
==============================================================================

usage: edapi.py [-h] [--version] [--debug] [--import FILE] [--eddn]
                [--export FILE] [--vars] [--basename BASENAME]
                [--tdpath TDPATH] [--no-color] [--keys [KEYS [KEYS ...]]]
                [--tree]

EDAPI: Elite Dangerous API Tool

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --debug               Output additional debug info. (default: False)
  --import FILE         Import API info from a JSON file instead of the API.
                        Used mostly for debugging purposes. (default: None)
  --eddn                Post prices and shipyards to the EDDN. (default:
                        False)
  --export FILE         Export API response to a file as JSON. (default: None)
  --vars                Output a file that sets environment variables for
                        current cargo capacity, credits, and current
                        system/station. (default: False)
  --basename BASENAME   Base file name. This is used to construct the cookie
                        and vars file names. (default: edapi)
  --tdpath TDPATH       Path to the Trade Dangerous root. This is used to
                        locate the Trade Dangerous python modules and data/
                        directory. (default: .)
  --no-color            Disable the use of ansi colors in output. (default:
                        False)
  --keys [KEYS [KEYS ...]]
                        Instead of normal import, display raw API data given a
                        set of dictionary keys. (default: None)
  --tree                Used with --keys. If present will print all content
                        below the specificed key. (default: False)

==============================================================================
== Trade Dangerous plugin usage:
==============================================================================

Copy edapi_plug.py to the plugins directory in Trade Dangerous. Use the
import command to connect to the API and import price and shipyard
data.

./trade.py import -P edapi

You can also import to EDDN with the plugin:

./trade.py import -P edapi -O eddn
