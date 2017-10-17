import logging
from .NameResolver import NameResolverFile
from .miscutils import httpget
from .Errors import CodingException, NoContentException
from .HashStore import LocationService, MimetypeService
from .Multihash import Multihash
from .DOI import DOIfile

class Sha1Hex(NameResolverFile):
    """
    Sha1Hex is a class for retrieval by Sha1Hex hash - based on ContentHash
    typically of form   sha1hex/1a2b3c for SHA1
    URL: `/xxx/contenthash/Q...` (forwarded here by ServerGateway methods)

    Implements name resolution of the ContentHash namespace, via a local store and any other internal archive method

    Future Work
    * Build way to preload the hashstore with the hashes and URLs from various parts of the Archive
    """

    def __init__(self, namespace, sha1_hex, **kwargs):
        """
        Creates the object

        :param namespace:   "contenthash"
        :param sha1_hex:   Base58 representation of multihash (could be sha256 or sha1, we may not have both)
        :param kwargs:      Any other args to the URL, ignored for now.
        """
        """
        Pseudo-code
        Looks up the multihash in Location Service to find where can be retrieved from.
        """
        super(Sha1Hex, self).__init__(self, namespace, sha1_hex, **kwargs)
        verbose=kwargs.get("verbose")
        if namespace != "sha1hex":
            raise CodingException(message="namespace != sha1hex")
        self.multihash = Multihash(sha1_hex=sha1_hex)   #TODO-SHA1HEX note ContentHash does this and next line wrong
        self.url = LocationService.get(self.multihash.multihash58, verbose) #TODO-FUTURE recognize different types of location, currently assumes URL
        self.mimetype = MimetypeService.get(self.multihash.multihash58, verbose)    # Should be after DOIfile resolution, which will set mimetype in MimetypeService
        self._metadata = None   # Not resolved yet
        self._doifile = None   # Not resolved yet

    @classmethod
    def new(cls, namespace, sha1_hex, *args, **kwargs):
        """
        #TODO-SHA1HEX create a superclass once tested
        Called by ServerGateway to handle a URL - passed the parts of the remainder of the URL after the requested format,

        :param namespace:
        :param args:
        :param kwargs:
        :return:
        """
        ch = super(Sha1Hex, cls).new(namespace, sha1_hex, *args, **kwargs)    # By default calls cls() which goes to __init__
        if not ch.url:
            ch = DOIfile(multihash=ch.multihash).url  # Will fill in url if known. Note will now return a DOIfile, not a Sha1Hex
            pass  # TODO-this is where we look things up in the DOI.sql etc essentially cycle through some other classes, asking if they know the URL
        if not ch.url:
            raise NoContentException()
        return ch

    def push(self, obj):
        """
        Add a Shard to a ContentHash -
        :return:
        """
        pass  # Note could probably be defined on NameResolverFile class

    def content(self, verbose=False):
        """
        :returns:   content - i.e. bytes
        """
        # TODO-STREAMS future work to return a stream
        if not self.url:
            raise NoContentException()
        data = httpget(self.url)
        if verbose: logging.debug("Retrieved doc size=", len(data))
        return {'Content-type': self.mimetype,
            'data': data,
            }

    def metadata(self, verbose=False):
        """
        :param verbose:
        :return:
        """
        if not self._metadata:
            if not self._doifile:
                self._doifile = DOIfile(multihash=self.multihash, verbose=verbose)    # If not found, dont set url/metadata etc
            self._metadata = self._metadata or (self._doifile and self._doifile.metadata(verbose=verbose))
        return self._metadata
    # def canonical - not needed as already in a canonical form
