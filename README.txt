==============================================================================
EDMS: Elite Dangerous Market Scraper
Requires Python 3.4.
==============================================================================
Automates pulling your current station info and market data and
importing into TradeDangerous.

==============================================================================
== Usage:
==============================================================================

Either place edms.py in the TradeDangerous root, or tell it where to
find TradeDangerous with the --tdpath option.

usage: edms.py [-h] [--version] [--debug] [--vars] [--basename BASENAME]
               [--tdpath TDPATH] [--no-color] [-y] [--keys [KEYS [KEYS ...]]]
               [--tree]

EDMS: Elite Dangerous Market Scraper

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --debug               Output additional debug info.
  --vars                Output a file that sets environment variables for
                        current cargo capacity, credits, and current
                        system/station.
  --basename BASENAME   Base file name. This is used to construct the cookie
                        and vars file names. Defaults to "edms"
  --tdpath TDPATH       Path to the TradeDangerous root. This is used to
                        locate the TradeDangerous python modules and data/
                        directory. Defaults to the cwd.
  --no-color            Disable the use of ansi colors in output.
  -y, --yes             Always accept new station names and import latest data
                        without prompting.
  --keys [KEYS [KEYS ...]]
                        Instead of normal import, display raw API data given a
                        set of dictionary keys.
  --tree                Used with --keys. If present will print all content
                        below the specificed key.
