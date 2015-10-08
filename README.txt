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

usage: edapi.py [-h] [--version] [--debug] [--tdpath TDPATH] [--no-color]
                [--basename BASENAME] [--vars] [--ships] [--import FILE]
                [--export FILE] [--eddn] [--keys [KEYS [KEYS ...]]] [--tree]

EDAPI: Elite Dangerous API Tool

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --debug               Output additional debug info. (default: False)
  --tdpath TDPATH       Path to the Trade Dangerous root. This is used to
                        locate the Trade Dangerous python modules and data/
                        directory. (default: .)
  --no-color            Disable the use of ansi colors in output. (default:
                        False)
  --basename BASENAME   Base file name. This is used to construct the cookie
                        and vars file names. (default: edapi)
  --vars                Output a file that sets environment variables for
                        current cargo capacity, credits, and current
                        system/station. (default: False)
  --ships               Write shipyards to the TD ShipVendor.csv. (default:
                        False)
  --import FILE         Import API info from a JSON file instead of the API.
                        Used mostly for debugging purposes. (default: None)
  --export FILE         Export API response to a file as JSON. (default: None)
  --eddn                Post price, shipyards, and outfitting to the EDDN.
                        (default: False)
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

==============================================================================
== Acknowledgements
==============================================================================

"Elite: Dangerous" is © 1984 - 2015 Frontier Developments Plc.
Oliver "kfsone" Smith for his excellent tool, Trade Dangerous.
Jonathan Harris for ED Market Connector and doing all the hard work on modules.

==============================================================================
== License
==============================================================================

All code specificially for the EDAPI application and plugin are released
under the MIT License. Any data associated with Elite: Dangerous is
intellectual property and copyright of Frontier Developments plc
('Frontier', 'Frontier Developments') and are subject to their terms and
conditions. (https://www.frontierstore.net/terms-and-conditions/)

Copyright (c) 2014-2015 Tyler Lund

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
