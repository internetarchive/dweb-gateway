"""
Hash Store set of classes for storage and retrieval
"""
import redis
import logging
from .Errors import CodingException


class HashStore(object):
    """
    Superclass for key value storage

    Will tie to a REDIS database initially.

    """
    """
    OLD NOTES
    Stores and retrieves meta data for hashes, NOTE the hash is NOT the hash of the metadata, and metadata is mutable.
    * Not exposed as a URL (can do internally if reqd)
    * hash_store(multihash, field, value)    # Replace the data in hash
    * hash_push(multihash, field, value)     # Append data to anything already there (use a REDIS RPUSH)
    * hash_delete(multihash, field)          # Delete anything stored (probably not required).
    * hash_get(multihash, field)             # Return python obj relating to field (list, or string)
    * param multihash: Base58 string of self describing hash: e.g. SHA256 is "Qm..." and SHA1 is "5..."
    * param field: Field to store data in.
    
    * Consumes: REDIS
    * ConsumedBy: *TBC*
    
    The fields allow essentially for independent indexes. 
    
    It should be a simple shim around REDIS, note will have to combine multihash and field to get a redis "key" as if we 
    used multihash as the key, and field is one field of a Redis dict type, then we won't be able to "push" to it. 
    
    Note we can assume that this is used in a consistent fashion, e.g. won't do hash_store then hash_push which would be invalid.
    """
    """
    SAMPLE CODE - THAT ACCESSES REDIS - 
    import redis
    from flask import Flask
    from flask import request
    import pdb
    app = Flask(__name__)
    
    r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
    #.set('foo', 'bar')
    #print(r.get('foo'))
    
    @app.route("/content/contenthash/<contenthash>")
    def get_content_hash(contenthash):
        print('l:%s' % contenthash)
        location = r.hgetall('location_%s' % contenthash)
        if 'url' in location:
            return location['url']
        else:
            return "", 404
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
    def hash_set(cls, multihash, field, value):
        """
        :param multihash:
        :param field:
        :param value:
        :return:
        """
        logging.debug("Hash set:", multihash, field, "=", value)
        cls.redis().hset(multihash, field, value)

    @classmethod
    def hash_get(cls, multihash, field):
        """

        :param multihash:
        :param field:
        :return:
        """
        res = cls.redis().hget(multihash, field)
        logging.debug("Hash found:", multihash, field, "=", res)
        return res

    @classmethod
    def set(cls, multihash, value):
        """

        :param multihash:
        :param value:   What we want to store in the redisfield
        :return:
        """
        return cls.hash_set(multihash, cls.redisfield, value)

    @classmethod
    def get(cls, multihash, verbose=False):
        """

        :param multihash:
        :return: string stored in Redis
        """
        return cls.hash_get(multihash, cls.redisfield)


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
