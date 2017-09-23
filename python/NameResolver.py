from miscutils import multihashsha256_58

#TODO-PYTHON3 file needs reviewing for Python3 as well as Python2

class NameResolver(object):
    """
    The NameResolver group of classes manage recognizing a name, and connecting it to resources
    we have at the Archive.

    These are base classes for specific name resolvers like DOI

    it specifies a set of methods we expect to be able to do on a subclass,
    and may have default code for some of them based on assumptions about the data structure of subclasses.

    Each subclass of NameResolver must support:
    content()   Generate an output to return to a browser. (Can be a dict, array or string, later will add Streams)

    Each subclass of NameResolver can provide, but can also use default:
    contenthash()   The hash of the content

    Logically it can represent one or multiple files depending on subclass

    Attributes reqd:
    name:   Name of the object being retrieved (short string)
    namespace:  Store the namespace here.

    A subclass can have any meta-data fields, recommended ones include.
    contentSize:    The size of the content in brief (compatible with Schema.org, not compatible with standard Archive metadata)
    contentType:    The mime-type of the content, (TODO check against schema.org), not compatible with standard Archive metadata which uses three letter types like PNG
    """

    def __init__(self, namespace, *args, **kwargs):
        raise ToBeImplementedException(message="Subclass for namespace",namespace,"needs an __init__")

    def contenthash(self):
        """
        By default contenthash is the hash of the content.

        :return:
        """
        return {'Content-type': 'text/plain',
         'data': multihashsha256_58(self.content())  # A list of names of services supported below  (not currently consumed anywhere)
         }

    def push(self,*args,**kwargs):
        #TODO NameResolver push should add a NameResolverShard to a NameResolverFile or a NameResolverFile to a NameResolverDir - in both cases on _list field
        raise ToBeImplementedException(message="NameResolver.push")

    @classmethod
    def canonical(cls, namespace, *args, **kwargs):
        """
        Should already be a canonical form

        :param cls:
        :param namespace:
        :param multihash58:
        :return:
        """
        return namespace, args.join('/')    # By default reconcatonate args


class NameResolverDir(NameResolver):

    """
    Represents a set of files,

    Attributes:
    _list:  Hold data for a list of files (NameResolverFile) in the directory.
    files():  An iterator over _list - returns NameResolverFile
    name:   Name of the directory
    """
    pass

class NameResolverFile(NameResolver):
    """
    Represents a single file, and its shards,
    It contains enough info for retrieval of the file e.g. HTTP URL, or server and path. Also can have byterange,

    Attributes:
    _list:  Hold data for a list of shards in this file.
    shards(): An iterator over _list
    See NameResolver for other metadata fields

    TODO - define fields for location & byterange

    Any other field can be used as namespace specific metadata
    """
    shardsize = 256000  # A default for shard size, TODO determine best size, subclasses can overwrite, or ignore for things like video.
    pass

    def shards():
        """
        Return an iterator that returns each of the NameResovlerShard in the file's _list attribute.
        * Each time called, should:
            * read next `shardsize` bytes from content (either from a specific byterange, or by reading from an open stream)
            * Pass that through multihash58 service to get a base58 multihash
            * Return that multihash, plus metadata (size may be all required)
            * Store the mapping between that multihash, and location (inc byterange) in locationstore
        * May Need to cache the structure, but since the IPLD that calls this will be cached, that might not be needed.
        """
        pass

class NameResolverShard(NameResolver):
    """
    Represents a single shard returned by a NameResolverFile.shards() iterator
    Holds enough info to do a byte-range retrieval of just those bytes from a server,
    And a multihash that could be retrieved by IPFS for just this shard.
    """
    pass
