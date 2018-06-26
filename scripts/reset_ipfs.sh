python3 -c '
import logging
import os
from python.config import config
from python.maintenance import resetipfs

logging.basicConfig(**config["logging"])    # For server
cachetabledomain=config["domains"]["directory"]+config["domains"]["metadata"]+"/domain"
cachetable=config["domains"]["directory"]+config["domains"]["metadata"]
print("removing",cachetable)
try:
    os.remove(cachetabledomain)
except FileNotFoundError:    # Might already have been deleted
    pass
try:
    os.rmdir(cachetable)
except FileNotFoundError:    # Might already have been deleted
    pass
print("Resetting IPFS - slowish loop")
resetipfs(removeipfs=True)
'

# To fully reset IPFS need to also ...
# rm /usr/local/dweb-gateway/.cache/table/{config["domains"]["metadata"]} which is where leafs stored - these refer to IPFS hashes for metadata


