#!/usr/bin/env python3

import logging
import sys
import redis

from python.config import config
from python.Archive import ArchiveItem, ArchiveFile

logging.basicConfig(**config["logging"])    # On server logs to /usr/local/dweb_gateway/dweb_gateway.log

#print(config);
logging.debug("load_ipfs args={}".format(sys.argv)) # sys.argv[1] is first arg (0 is this script)
if (len(sys.argv) > 1) and ("/" in sys.argv[1]):
    args = sys.argv[1].split('/')
else:
    args = sys.argv[1:]

#Can override args while testin
#args = ["commute"]
#args = ["commute", "commute.avi"]
#args = ["commute", "closeup.gif"]

# Set one of these to True based on whether want to use IPFS add or IPFS urlstore
forceadd = True
forceurlstore = False
# Set to true if want each ipfs hash added to DHT via DHT provide
announcedht = False

obj = ArchiveItem.new("archiveid", *args, wanttorrent=False)
print('"URL","Add/Urlstore","Hash","Size","Announced"')
if isinstance(obj, ArchiveFile):
    obj.cache_ipfs(url = obj.archive_url, forceadd=forceadd, forceurlstore=forceurlstore, verbose=False,  printlog=True, announcedht=announcedht, size=int(obj._metadata["size"]))
else:
    obj.cache_ipfs(forceurlstore=forceurlstore, forceadd=forceadd, verbose=False, announcedht=announcedht, printlog=True)  # Will Loop through all files in Item

#print("---FINISHED ---")
