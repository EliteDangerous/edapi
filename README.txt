==============================================================================
EDMS: Elite Dangerous Market Scraper
Requires Python 3.4.
==============================================================================
Automates pulling your current station info and market data and
importing into TradeDangerous.

==============================================================================
== Usage:
==============================================================================

Place get_market.py in the tradedangerous root, and execute it.

usage: get_market.py [-h] [--version] [--debug] [--vars] [--basename BASENAME]

optional arguments:
  -h, --help           show this help message and exit
  --version            show program's version number and exit
  --debug              Output additional debug info.
  --vars               Output a file that sets environment variables for
                       current cargo capacity, credits, insurance, and current
                       system/station.
  --basename BASENAME  Base file name. This is used to construct the cookie
                       and vars file names. Defaults to "get_market"
