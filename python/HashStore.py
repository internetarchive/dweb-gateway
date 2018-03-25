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

class StateService(HashStore):

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
        return loads(cls.hash_get("__STATE__", field, verbose))

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
    redisfield = "mimetype"


class IPLDService(HashStore):
    # TODO-IPFS may need to move this to ContentStore (which needs implementing)
    redisfield = "ipld"


class IPLDHashService(HashStore):
    redisfield = "ipldhash"

class ThumbnailIPFSfromItemIdService(HashStore):
    redisfield = "thumbnailipfs"

class MagnetLinkService(HashStore):
    # uses archiveidset/get
    redisfield = "magnetlink"

    @classmethod
    def btihget(cls, btihhash, verbose=False):
        return cls.get("btih:"+btihhash)

    @classmethod
    def btihset(cls, btihhash, value, verbose=False):
        return cls.set("btih:"+btihhash, value)

class TitleService(HashStore):
    # Cache collection names, they dont change often enough to worry
    # uses archiveidset/get
    # TODO-REDIS note this is caching for ever, which is generally a bad idea ! Should figure out how to make Redis expire this cache every few days
    redisfield = "title"
