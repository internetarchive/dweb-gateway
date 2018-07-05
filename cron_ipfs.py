import logging
# This is run every 10 minutes by Cron (10 * 58 = 580 ~ 10 hours)
from python.config import config
import redis
import base58
from python.HashStore import StateService
from python.TransportIPFS import TransportIPFS
from python.maintenance import resetipfs

logging.basicConfig(**config["logging"])    # For server
resetipfs(announcedht=True)

# To fully reset IPFS need to also ...
# rm /usr/local/dweb-gateway/.cache/table/{config["domains"]["metadataverifykey"]} which is where leafs stored - these refer to IPFS hashes for metadata
