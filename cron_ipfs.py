import logging
# This is run every 10 minutes by Cron (10 * 58 = 580 ~ 10 hours)
from python.config import config
import redis
import base58
from python.HashStore import StateService

#logging.basicConfig(level=logging.DEBUG)   # For local debugging
logging.basicConfig(**config["logging"])    # For server

def resetipfs(removeipfs=False, reseedipfs=False, announcedht=False, verbose=False):

    r = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)
    reseeded = 0
    removed = 0
    total = 0
    withipfs = 0
    announceddht = 0
    if announcedht:
        dhtround = (int(((StateService.get("LastDHTround", verbose)) or 0)) + 1 % 58)
        StateService.set("LastDHTround", dhtround, verbose)
        dhtroundletter = base58.b58encode_int(dhtround)
        print("DHT round:",dhtroundletter)
    for i in r.scan_iter():
        total = total+1
        for k in [ "ipldhash", "thumbnailipfs" ]:
            ipfs = r.hget(i, k)
            #print(i, ipfs)
            if ipfs:
                withipfs = withipfs + 1
                ipfs = ipfs.replace("ipfs:/ipfs/", "")
                if removeipfs:
                    r.hdel(i, "ipldhash")
                    removed = removed + 1
                if reseedipfs:
                    print("Reseeding", i, ipfs)
                    TransportIPFS().pinggateway(ipfs)
                    reseeded = reseeded + 1
                if announcedht:
                    if dhtroundletter == ipfs[5]:  # Compare far enough into string to be random
                        print("Announcing", i, ipfs)
                        TransportIPFS().announcedht(ipfs)
                        announceddht = announceddht + 1
    print ("Scanned {}, withipfs {}, deleted {}, reseeded {}, announced {}".format(total, withipfs, removed, reseeded, announceddht))

resetipfs(announcedht=True)
