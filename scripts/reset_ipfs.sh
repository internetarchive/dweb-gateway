python3 -c '
import logging
import os
from python.config import config
from python.maintenance import resetipfs

logging.basicConfig(**config["logging"])    # For server
cachetabledomain=config["domains"]["directory"]+config["domains"]["metadataverifykey"]+"/domain"
cachetable=config["domains"]["directory"]+config["domains"]["metadataverifykey"]

print("Step 1: removing", cachetable, "which is where leafs stored - these refer to IPFS hashes for metadata")
try:
    os.remove(cachetabledomain)
except FileNotFoundError:    # Might already have been deleted
    pass
try:
    os.rmdir(cachetable)
except FileNotFoundError:    # Might already have been deleted
    pass

print("Step 2: Remove all REDIS links to IPFS hashes")
resetipfs(removeipfs=True)

print("Step 3: Clearing out IPFS repo")

'
# The sudo stuff below here isn't tested - all these commands need running as ipfs
sudo -u upfs ipfs pin ls --type recursive -q | sudo -u ipfs xargs ipfs pin rm
sudo -u ipfs repo gc

