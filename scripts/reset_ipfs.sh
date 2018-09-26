# Removes references to IPFS from the server, and cleans up ipfs.
# It might be worth running `sudo ipfs sh; cd /home/ipfs; gzip -c -r .ipfs >ipfsrepo.20180915.prerestore.zip` before 
# And will need to run the preseeder in /usr/local/dweb-mirror afterwards to get the popular collections back in
cd /usr/local/dweb-gateway

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
sudo -u ipfs ipfs pin ls --type recursive -q | sudo -u ipfs xargs ipfs pin rm
sudo -u ipfs ipfs repo gc

