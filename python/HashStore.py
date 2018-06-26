"""
Hash Store set of classes for storage and retrieval
"""
import redis
import logging
from .Errors import CodingException
from .TransportIPFS import TransportIPFS
from .miscutils import loads, dumps

class HashStore(object):
    """
    Superclass for key value storage, a shim around REDIS intended to be subclassed (see LocationService for example)

    Will tie to a REDIS database initially.

    Class Fields:
    _redis: redis object    Redis Connection object once connection to redis once established,

    Fields:
    redisfield: string  name of field in redis store being used.

    Class methods:
    redis()             Initiate connection to redis or return already open one.

    Instance methods:
    hash_set(multihash, field, value, verbose=False)    Set Redis.multihash.field to value
    hash_get(multihash, field, verbose=False)           Retrieve value of Redis.multihash.field
    set(multihash, value, verbose=False)                Set Redis.multihash.<redisfield> = value
    get(multihash, value, verbose=False)                Retrieve Redis.multihash.<redisfield>

    Delete and Push are not supported but could be if required.

    Subclasses map

    Note Contenthash = multihash base58 of content (typically SHA1 on IA at present)
    itemid = archive's item id, e.g. "commute"

    Class               StoredAt                        Maps        To
    StateService        __STATE__.<field>               field       arbitraryvalue    For global state
    StateService        __STATE__.LastDHTround          number?     Used by cron_ipfs.py to track whats up next
    LocationService     <contenthash>.location          url         As returned by rawstore or url of content on IA
    MimetypeService     <contenthash>.mimetype          mimetype
    IPLDService         Not used currently
    IPLDHashService     <contenthash>.ipld              IPFS hash   e.g. Q123 or z123 (hash of the IPLD)
    ThumbnailIPFSfromItemIdService <itemid>.thumbnailipfs ipfsurl   e.g. ipfs:/ipfs/Q1…
    MagnetLinkService   bits:<b32hash>.magnetlink       magnetlink
    MagnetLinkService   archived:<itemid>.magnetlink    magnetlink
    TitleService        archived:<itemid>.title         title       Used to map collection item’s to their titles (cache search query)
    """

    _redis = None   # Will be connected to a redis instance by redis()
    redisfield = None   # Subclasses define this, and use set & get

    @classmethod
    def redis(cls):
        if not HashStore._redis:
            logging.debug("HashStore connecting to Redis")
            HashStore._redis = redis.StrictRedis(   # Note uses HashStore cos this connection is shared across subclasses
                host="localhost",
                port=6379,
                db=0,
                decode_responses=True
            )
        return HashStore._redis

    def __init__(self):
        raise CodingException(message="It is meaningless to instantiate an instance of HashStore, its all class methods")

    @classmethod
    def hash_set(cls, multihash, field, value, verbose=False):
        """
        :param multihash:
        :param field:
        :param value:
        :return:
        """
        if verbose: logging.debug("Hash set: {0} {1}={2}".format(multihash, field, value))
        cls.redis().hset(multihash, field, value)

    @classmethod
    def hash_get(cls, multihash, field, verbose=False):
        """

        :param multihash:
        :param field:
        :return:
        """
        res = cls.redis().hget(multihash, field)
        if verbose: logging.debug("Hash found: {0} {1}={2}".format(multihash, field, res))
        return res

    @classmethod
    def set(cls, multihash, value, verbose=False):
        """

        :param multihash:
        :param value:   What we want to store in the redisfield
        :return:
        """
        return cls.hash_set(multihash, cls.redisfield, value, verbose)

    @classmethod
    def get(cls, multihash, verbose=False):
        """

        :param multihash:
        :return: string stored in Redis
        """
        return cls.hash_get(multihash, cls.redisfield, verbose)


    @classmethod
    def archiveidget(cls, itemid, verbose=False):
        return cls.get("archiveid:"+itemid)

    @classmethod
    def archiveidset(cls, itemid, value, verbose=False):
        return cls.set("archiveid:" + itemid, value)

    @classmethod
    def btihget(cls, btihhash, verbose=False):
        return cls.get("btih:"+btihhash)

    @classmethod
    def btihset(cls, btihhash, value, verbose=False):
        return cls.set("btih:"+btihhash, value)

class StateService(HashStore):
    """
    Store some global state for the server

    Field   Value   Means
    LastDHTround    ??  Used by cron_ipfs.py to record which part of hash table it last worked on
    """

    @classmethod
    def set(cls, field, value, verbose=False):
        """
        Store to global state
        field:  Name of field to store
        value:  Content to store
        """
        return cls.hash_set("__STATE__", field, dumps(value), verbose)

    @classmethod
    def get(cls, field, verbose=False):
        """
        Store to global state saving
        :param field:
        :return: string stored in Redis
        """
        res = cls.hash_get("__STATE__", field, verbose)
        if res is None:
            return None
        else:
            return loads(res)

class LocationService(HashStore):
    """
    OLD NOTES
    Maps hashes to locations
    * set(multihash, location)
    * get(multihash) => url (currently)
    * Consumes: Hashstore
    * ConsumedBy: DOI Name Resolver

    The multihash represents a file or a part of a file. Build upon hashstore.
    It is split out because this could be a useful service on its own.
    """
    redisfield = "location"


class MimetypeService(HashStore):
    # Maps contenthash58 to mimetype
    redisfield = "mimetype"


class IPLDService(HashStore):
    # TODO-IPFS may need to move this to ContentStore (which needs implementing)
    # Note this doesnt appear to be used except by IPLDFile/IPLDdir which themselves arent used
    redisfield = "ipld"


class IPLDHashService(HashStore):
    # Maps contenthash58 to IPLD's multihash CIDv0 or CIDv1
    redisfield = "ipldhash"

class ThumbnailIPFSfromItemIdService(HashStore):
    # Maps itemid to IPFS URL (e.g. ipfs:/ipfs/Q123...)
    redisfield = "thumbnailipfs"

class MagnetLinkService(HashStore):
    # uses archiveidset/get
    redisfield = "magnetlink"

class TitleService(HashStore):
    # Cache collection names, they dont change often enough to worry
    # uses archiveidset/get
    # TODO-REDIS note this is caching for ever, which is generally a bad idea ! Should figure out how to make Redis expire this cache every few days
    redisfield = "title"
