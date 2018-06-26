python3 -c '
import logging
import os
from python.config import config
from python.maintenance import resetipfs

logging.basicConfig(**config["logging"])    # For server
cachetabledomain=config["domains"]["directory"]+config["domains"]["metadata"]+"/domain"
cachetable=config["domains"]["directory"]+config["domains"]["metadata"]

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
ipfs pin ls --type recursive -q | xargs ipfs pin rm
