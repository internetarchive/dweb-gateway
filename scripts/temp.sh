cd /usr/local/dweb-gateway

python3 -c '
import logging
import os
from python.config import config
from python.maintenance import resetipfs

logging.basicConfig(**config["logging"])    # For server
cachetabledomain=config["domains"]["directory"]+config["domains"]["metadataverifykey"]+"/domain"
cachetable=config["domains"]["directory"]+config["domains"]["metadataverifykey"]

print("Step 2: Remove all REDIS links to MAGNETLINKS  hashes")
resetipfs(removemagnet=True)

'

