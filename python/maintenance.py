import logging
# This is run every 10 minutes by Cron (10 * 58 = 580 ~ 10 hours)
from python.config import config
import redis
import base58
from .HashStore import StateService
from .TransportIPFS import TransportIPFS

logging.basicConfig(**config["logging"])    # For server

def resetipfs(removeipfs=False, reseedipfs=False, removemagnet=False, announcedht=False, verbose=False, fixbadurls=False):
    """
    Loop over and "reset" ipfs
    :param removeipfs:      If set will remove all cached pointers to IPFS - note this is part of a three stage process see notes in cleanipfs.sh
    :param reseedipfs:      If set we will ping the ipfs.io gateway to make sure it knows about our files, this isn't used any more
    :param removemagnet:    Remove all cached magnet links (e.g. to add a new default tracker
    :param announcedht:     Announce our files to the DHT - currently run by cron regularly
    :param verbose:         Generate verbose debugging - the code below could use more of this
    :param fixbadurls:      Removes some historically bad URLs, this was done so isn't needed again - just left as a modifyable stub.
    :return:
    """
    knownbadhashes = [
        "zb2rhhEncXjn7PnqJ16mzfeug1bqWuupQ3PnkhnWLpAaDatiZ", # audio
        "zb2rhiSEszTZ4YuY7GJScy6jKZTJuR97MLs7KSe2nKLHwb4A7", # texts
        "zb2rhk2FYVEy5VRHmaEzor7NuA936E8GGaokZFurKmUE959zx", # movies
    ]
    r = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)
    reseeded = 0
    removed = 0
    magremoved = 0
    total = 0
    withipfs = 0
    withmagnet = 0
    announceddht = 0
    if announcedht:
        dhtround = ((int(((StateService.get("LastDHTround", verbose)) or 0)) + 1) % 58)
        StateService.set("LastDHTround", dhtround, verbose)
        dhtroundletter = base58.b58encode_int(dhtround)
        logging.debug("DHT round: {}".format(dhtroundletter))
    for i in r.scan_iter():
        total = total+1
        if fixbadurls:
            url = r.hget(i, "url")
            if urls.startswith("ipfs:"):
                logging.debug("Would delete {} .url= {}".format(i,url))
                #r.hdel(i, "url")
        for k in ["magnetlink"]:
            magnetlink = r.hget(i, k)
            if magnetlink:
                withmagnet = withmagnet + 1
                if removemagnet:
                    r.hdel(i, k)
                    magremoved = magremoved + 1

        for k in [ "ipldhash", "thumbnailipfs" ]:
            ipfs = r.hget(i, k)
            #print(i, ipfs)
            if ipfs:
                withipfs = withipfs + 1
                ipfs = ipfs.replace("ipfs:/ipfs/", "")  # The hash
                if removeipfs or (ipfs in knownbadhashes):
                    r.hdel(i, k)
                    removed = removed + 1
                if reseedipfs:
                    #logging.debug("Reseeding {} {}".format(i, ipfs))  # Logged in TransportIPFS
                    TransportIPFS().pinggateway(ipfs)
                    reseeded = reseeded + 1
                if announcedht:
                    #print("Testing ipfs {} .. {} from {}".format(ipfs[6],dhtroundletter,ipfs))
                    if dhtroundletter == ipfs[6]:  # Compare far enough into string to be random
                        # logging.debug("Announcing {} {}".format(i, ipfs))  # Logged in TransportIPFS
                        TransportIPFS().announcedht(ipfs)
                        announceddht = announceddht + 1
    logging.debug("Scanned {}, withipfs {}, deleted {}, reseeded {}, announced {}, magremoved {}".format(total, withipfs, removed, reseeded, announceddht, magremoved))

# To announce DHT under cron
#logging.basicConfig(**config["logging"])    # For server
#resetipfs(announcedht=True)

# To fully reset IPFS need to also ...
# rm /usr/local/dweb-gateway/.cache/table/{config["domains"]["metadataverifykey"]} which is where leafs stored - these refer to IPFS hashes for metadata
# Clean out the repo (Arkadiy to provide info)
