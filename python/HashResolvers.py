import logging
from .NameResolver import NameResolverFile
from .miscutils import httpget
from .Errors import CodingException, NoContentException
from .HashStore import LocationService, MimetypeService
from .LocalResolver import LocalResolver
from .Multihash import Multihash
from .DOI import DOIfile

class HashResolver(NameResolverFile):
    """
    Base class for Sha1Hex and ContentHash - used where we are instantiating something of unknown type from a hash of some form.

    Sha1Hex & ContentHash are classes for retrieval by a hash
    typically of form   sha1hex/1a2b3c for SHA1

    Implements name resolution of the ContentHash namespace, via a local store and any other internal archive method

    Future Work
    * Build way to preload the hashstore with the hashes and URLs from various parts of the Archive
    """
    namespace=None      # Defined in subclasses
    multihashfield=None # Defined in subclasses

    def __init__(self, namespace, hash, **kwargs):
        """
        Creates the object

        :param namespace:   "contenthash"
        :param hash:        Hash representing the object - format is specified by namespace
        :param kwargs:      Any other args to the URL, ignored for now.
        """
        """
        Pseudo-code
        Looks up the multihash in Location Service to find where can be retrieved from.
        """
        verbose=kwargs.get("verbose")
        if verbose:
            logging.debug("{0}.__init__({1}, {2}, {3})".format(self.__class__.__name__, namespace, hash, kwargs))
        if namespace != self.namespace: # Defined in subclasses
            raise CodingException(message="namespace != "+self.namespace)
        super(HashResolver, self).__init__(self, namespace, hash, **kwargs) # Note ignores the name
        self.multihash = Multihash(**{self.multihashfield: hash})
        self.url = LocationService.get(self.multihash.multihash58, verbose) #TODO-FUTURE recognize different types of location, currently assumes URL
        self.mimetype = MimetypeService.get(self.multihash.multihash58, verbose)    # Should be after DOIfile resolution, which will set mimetype in MimetypeService
        self._metadata = None   # Not resolved yet
        self._doifile = None   # Not resolved yet


    @classmethod
    def new(cls, namespace, hash, *args, **kwargs):
        """
        #TODO-SHA1HEX create a superclass once tested
        Called by ServerGateway to handle a URL - passed the parts of the remainder of the URL after the requested format,

        :param namespace:
        :param args:
        :param kwargs:
        :return:
        :raise NoContentException: if cant find content directly or via other classes (like DOIfile)
        """
        verbose=kwargs.get("verbose")
        ch = super(HashResolver, cls).new(namespace, hash, *args, **kwargs)    # By default (on NameResolver) calls cls() which goes to __init__
        if not ch.url:
            if verbose: logging.debug("No URL, looking for DOI file for {0}.{1}".format(namespace,hash))   
            #!SEE-OTHERHASHES -this is where we look things up in the DOI.sql etc essentially cycle through some other classes, asking if they know the URL
            ch = DOIfile(multihash=ch.multihash).url  # Will fill in url if known. Note will now return a DOIfile, not a Sha1Hex
        if ch.url.startswith("local:"):
            ch = LocalResolver.new("rawfetch", hash, **kwargs)
        if not (ch and ch.url):
            raise NoContentException()
        return ch

    def push(self, obj):
        """
        Add a Shard to a ContentHash -
        :return:
        """
        pass  # Note could probably be defined on NameResolverFile class

    def retrieve(self, verbose=False):
        """
        :returns:   content - i.e. bytes
        """
        # TODO-STREAMS future work to return a stream
        if not self.url:
            raise NoContentException()
        if self.url.startswith("local:"):
            u = self.url.split('/')
            if u[1] == "rawfetch":
                assert(False)
                #TODO-LOCAL hook to LocalResolver/rawfetch when it is tested
            else:
                raise CodingException(message="unsupported for local: {0}".format(self.url))

        else:
            return httpget(self.url)

    def content(self, verbose=False):
        """
        :returns:   content - i.e. bytes
        """
        # TODO-STREAMS future work to return a stream
        if not self.url:
            raise NoContentException()
        if self.url.startswith("local:"):
            raise CodingException(message="Shouldnt get here, should convert to LocalResolver in HashResolver.new: {0}".format(self.url))
            """
            u = self.url.split('/')
            if u[1] == "rawfetch":
                assert(False) # hook to LocalResolver/rawfetch if need this
            else:
                raise CodingException(message="unsupported for local: {0}".format(self.url))
            """
        else:
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

class Sha1Hex(HashResolver):
    """
    URL: `/xxx/contenthash/Q...` (forwarded here by ServerGateway methods)
    """
    namespace="sha1hex"
    multihashfield="sha1hex"    # Field to Multihash.init

class ContentHash(HashResolver):
    """
    URL: `/xxx/contenthash/Q...` (forwarded here by ServerGateway methods)
    """
    namespace="contenthash"
    multihashfield="multihash58"    # Field to Multihash.init
