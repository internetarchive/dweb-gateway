"""
Hash Store set of classes for storage and retrieval
"""
import redis


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

    def __init__(self):
        self.r = redis.StrictRedis(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=True
        )

    def hash_set(self, multihash, field, value, verbose=False):
        """

        :param multihash:
        :param field:
        :param value:
        :return:
        """
        if verbose: print("Hash set:",multihash, field,"=",value)
        self.r.hset(multihash, field, value)

    def hash_get(self, multihash, field, verbose=False):
        """

        :param multihash:
        :param field:
        :return:
        """
        res = self.r.hget(multihash, field)
        if verbose: print("Hash found:",multihash, field,"=",res)
        return res


    def set(self, multihash, value, verbose=False):
        """

        :param multihash:
        :param location:
        :return:
        """
        return self.hash_set(multihash, self.redisfield, value, verbose)

    def get(self, multihash, verbose=False):
        """

        :param multihash:
        :return: string stored in Redis
        """
        return self.hash_get(multihash, self.redisfield, verbose)

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
    redisfield="location"

class MimetypeService(HashStore):
    redisfield="mimetype"

class IPLDService(HashStore):
    #TODO-IPFS may need to move this to ContentStore (which needs implementing)
    redisfield="ipld"

class IPLDHashService(HashStore):
    redisfield="ipldhash"

