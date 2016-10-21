==============================================================================
EDAPI: Elite Dangerous API Tool
Requires Python 3.4, and requests.
Plugin requires Trade Dangerous.
==============================================================================

Pulls your profile information from the mobile API, and optionally uploads
info to EDDN. Also included is a Trade Dangerous plugin that will import 
data into the local TD database as well.

==============================================================================
== Command line usage:
==============================================================================

usage: edapi.py [-h] [--version] [--debug] [--no-color] [--basename BASENAME]
                [--vars] [--import FILE] [--export FILE] [--eddn]
                [--keys [KEYS [KEYS ...]]] [--tree] [--hash] [--login]

EDAPI: Elite Dangerous API Tool

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --debug               Output additional debug info. (default: False)
  --no-color            Disable the use of ansi colors in output. (default:
                        False)
  --basename BASENAME   Base file name. This is used to construct the cookie
                        and vars file names. (default: edapi)
  --vars                Output a file that sets environment variables for
                        current cargo capacity, credits, and current
                        system/station. (default: False)
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
  --hash                Obfuscate commander name for EDDN. (default: False)
  --login               Clear any cached user login cookies and force login.
                        (Doesn't clear the machine token) (default: False)

==============================================================================
== Trade Dangerous plugin usage:
==============================================================================

Copy edapi_plug.py to the plugins directory in Trade Dangerous. Use the
import command to connect to the API and import price, shipyard and
outfitting data.

Basic usage:

    trade.py import --plug edapi
      This will query the API for information abotu your currently docked
      station and import any market prices and shipyard information
      available. You will be prompted to enter any missing station information.

    trade.py imp -P edapi -O eddn
      This will do the same thing, but also post your market, shipyard, and
      outfitting modules to EDDN.

    trade.py imp -P edapi -O test=tmp/profile.20160707_202255.json
      This will load a API-response from the given file and work with that
      instead of querying to the companion API. If the EDDN option is also
      given, it will use the "test" schema instead of the production one
      and print out the sent message(s).

Options (-O):

    csvs:  Merge shipyards into ShipVendor.csv.
    edcd:  Call the EDCD plugin first
    eddn:  Post market, shipyard and outfitting to EDDN.
    name:  Do not obfuscate commander name for EDDN submit.
    save:  Save the API response (tmp/profile.YYYYMMDD_HHMMSS.json).
    test:  Test the plugin with a json file (test=[FILENAME]).
    warn:  Ask for station update if a API<->DB diff is encountered.

==============================================================================
== Acknowledgements
==============================================================================

"Elite: Dangerous" is © 1984 - 2016 Frontier Developments Plc.

Oliver "kfsone" Smith for his excellent tool, Trade Dangerous.

Jonathan Harris for ED Market Connector and doing all the hard work on
modules.

Bernd Gollesch for his continued support of Trade Dangerous and plugin
contributions.

All the folks contributing to EDCD, EDDN, and others!

==============================================================================
== License
==============================================================================

All code specificially for the EDAPI application and plugin are released
under the MIT License. Any data associated with Elite: Dangerous is
intellectual property and copyright of Frontier Developments plc
('Frontier', 'Frontier Developments') and are subject to their terms and
conditions. (https://www.frontierstore.net/terms-and-conditions/)

Copyright (c) 2014-2016 Tyler Lund

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
