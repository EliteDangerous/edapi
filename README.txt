==============================================================================
EDMS: Elite Dangerous Market Scraper
Requires Python 3.4 and TradeDangerous.
==============================================================================
Automates pulling your profile information from the mobile API, and populating
TradeDangerous with station, market, and shipyard data.

==============================================================================
== Command line usage:
==============================================================================

Either place edms.py in the TradeDangerous root, or tell it where to
find TradeDangerous with the --tdpath option.

usage: edms.py [-h] [--version] [--debug] [--vars] [--basename BASENAME]
               [--tdpath TDPATH] [--no-color] [--keys [KEYS [KEYS ...]]]
               [--tree]

EDMS: Elite Dangerous Market Scraper

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --debug               Output additional debug info. (default: False)
  --vars                Output a file that sets environment variables for
                        current cargo capacity, credits, and current
                        system/station. (default: False)
  --basename BASENAME   Base file name. This is used to construct the cookie
                        and vars file names. (default: edms)
  --tdpath TDPATH       Path to the TradeDangerous root. This is used to
                        locate the TradeDangerous python modules and data/
                        directory. (default: .)
  --no-color            Disable the use of ansi colors in output. (default:
                        False)
  --keys [KEYS [KEYS ...]]
                        Instead of normal import, display raw API data given a
                        set of dictionary keys. (default: None)
  --tree                Used with --keys. If present will print all content
                        below the specificed key. (default: False)

==============================================================================
== TradeDangerous plugin usage:
==============================================================================

Copy api_plug.py to the plugins directory in TradeDangerous. Use the
import command to connect to the API and import price and shipyard
data.

./trade.py import --plug api
