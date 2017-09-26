from .NameResolver import NameResolverFile
from .miscutils import httpget
from .Errors import CodingException, NoContentException
from .HashStore import LocationService, MimetypeService

class ContentHash(NameResolverFile):
    """
    ContentHash is a class for retrieval by content hash
    typically of form   contenthash/Qmd.... for SHA256 or contenthahs/5.... for SHA1
    URL: `/xxx/contenthash/Q...` (forwarded here by ServerGateway methods)

    Implements name resolution of the ContentHash namespace, via a local store and any other internal archive method

    Future Work
    * Build way to preload the hashstore with the hashes and URLs from various parts of the Archive
    """

    def __init__(self, namespace, multihash58, **kwargs):
        """
        Creates the object

        :param namespace:   "contenthash"
        :param multihash:   Base58 representation of multihash (could be sha256 or sha1, we may not have both)
        :param kwargs:      Any other args to the URL, ignored for now.
        """
        """
        Pseudo-code
        Looks up the multihash in Location Service to find where can be retrieved from.
        """
        super(ContentHash, self).__init__(self, namespace, multihash58, **kwargs)
        verbose=kwargs.get("verbose")
        if namespace != "contenthash":
            raise CodingException(message="namespace != contenthash")
        self.url = LocationService().get(multihash58, verbose) #TODO-FUTURE recognize different types of location, currently assumes URL
        self.mimetype = MimetypeService().get(multihash58, verbose) #TODO use a single service set at init

    def push(self, obj):
        """
        Add a Shard to a ContentHash -
        :return:
        """
        pass # Note could probably be defined on NameResolverFile class

    def content(self, verbose=False):
        # Returns the content - i.e. bytes
        #TODO-STREAMS future work to return a stream
        if not self.url:
            raise NoContentException()
        data = httpget(self.url)
        if verbose: print("Retrieved doc size=", len(data))
        return {'Content-type': self.mimetype,
            'data': data,
            }

    # def canonical - not needed as already in a canonical form
