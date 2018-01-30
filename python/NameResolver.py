import logging
import requests
from .Errors import ToBeImplementedException, NoContentException
from .Multihash import Multihash
from .HashStore import LocationService, MimetypeService, IPLDHashService
from .config import config
from .miscutils import httpget


class NameResolver(object):
    """
    The NameResolver group of classes manage recognizing a name, and connecting it to resources
    we have at the Archive.

    These are base classes for specific name resolvers like DOI

    it specifies a set of methods we expect to be able to do on a subclass,
    and may have default code for some of them based on assumptions about the data structure of subclasses.

    Each subclass of NameResolver must support:
    content()   Generate an output to return to a browser. (Can be a dict, array or string, later will add Streams) (?? Not sure if should implement content for dirs)

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

    def __init__(self, namespace, *args, **kwargs):  # Careful if change, note its the default __init__ for NameResolverDir, NameResolverFile, NameResolverSearch etc
        self._list = []

    @classmethod
    def new(cls, namespace, *args, **kwargs):
        """
        Default creation of new obj, returns None if not found (to allow multiple attempts to instantiate)

        :param namespace:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            return cls(namespace, *args, **kwargs)
        except NoContentException:
            return None

    def retrieve(self, _headers=None, verbose=False, **kwargs):
        """

        :return:
        """
        raise ToBeImplementedException(name=self.__class__.__name__+".retrieve()")

    def content(self, _headers=None, verbose=False, **kwargs):
        """
        Return the content, by default its just the result of self.retrieve() which must be defined in superclass
        Requires mimetype to be set in subclass

        :param verbose:
        :return:
        """
        return {"Content-type": self.mimetype, "data": self.retrieve(_headers=_headers)}

    def metadata(self, verbose=False):
        """

        :return:
        """
        raise ToBeImplementedException(name=self.__class__.__name__+".metadata()")

    def contenthash(self, verbose=False):
        """
        By default contenthash is the hash of the content.

        :return:
        """
        if not self._contenthash:
            self._contenthash = Multihash(data=self.content(), code=Multihash.SHA2_256)
        return  {'Content-type': 'text/plain',
                'data': self._contenthash.multihash58
                }

    def contenturl(self, verbose=False):
        """
        By default contenthash is the hash of the content.

        :return:
        """
        if not self._contenthash:
            self._contenthash = Multihash(data=self.content(), code=Multihash.SHA2_256)
        return {'Content-type': 'text/plain',
                'data': "https://gateway.dweb.me/content/rawfetch/"+self._contenthash.multihash58,   # TODO parameterise server name, maybe store from incoming URL
                }

    def push(self, obj):
        """
        Add a NameResolverShard to a NameResolverFile or a NameResolverFile to a NameResolverDir - in both cases on _list field
        Doesnt check class of object added to allow for variety of nested constructs.

        :param obj: NameResolverShard, NameResolverFile, or NameResolverDir
        :return:
        """
        self._list.append(obj)

    @classmethod
    def canonical(cls, namespace, *args, **kwargs):
        """
        If this method isn't subclassed, then its already a canonical form so return with slashes

        :param cls:
        :param namespace:
        :param [args]:    List of arguments to URL
        :return:        Concatenated args with / by default (subclasses will override)
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
    def files(self):
        return self._list


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
    shardsize = 256000  # A default for shard size, TODO-IPLD determine best size, subclasses can overwrite, or ignore for things like video.

    def shards(self):
        """
        Return an iterator that returns each of the NameResolverShard in the file's _list attribute.
        * Each time called, should:
            * read next `shardsize` bytes from content (either from a specific byterange, or by reading from an open stream)
            * Pass that through multihash58 service to get a base58 multihash
            * Return that multihash, plus metadata (size may be all required)
            * Store the mapping between that multihash, and location (inc byterange) in locationstore
        * May Need to cache the structure, but since the IPLD that calls this will be cached, that might not be needed.
        """
        raise ToBeImplementedException(name="NameResolverFile.shards")
        pass

    def cache_content(self, url, transport, verbose):
        """
        Retrieve content from a URL, cache it in various places especially IPFS and set tables so can be retrieved by contenthash

        Requires multihash to be set prior to this, if required it could be set from the retrieved data

        :param url:         URL - typically inside archive.org of contents
        :param transport:   Either None (for all) or a list of transports to cache for.
        :param verbose:
        :return:
        """
        ipldhash = self.multihash and IPLDHashService.get(self.multihash.multihash58)    # May be None, we don't know it
        if ipldhash:
            self.mimetype = MimetypeService.get(self.multihash.multihash58, verbose=verbose)
            ipldhash = IPLDHashService.get(self.multihash.multihash58, verbose=verbose)
        else:
            if not transport or "IPFS" in transport:
                (data, self.mimetype) = httpget(url, wantmime=True)
                #TODO could check sha1 here, but would be slow
                if not self.multihash:
                    if verbose: logging.debug("Computing SHA1 hash of url {}".format(url))
                    self.multihash = Multihash(data=data, code=Multihash.SHA1)
                    ipldhash = self.multihash and IPLDHashService.get(self.multihash.multihash58) # Try again now have hash
                MimetypeService.set(self.multihash.multihash58, self.mimetype, verbose=verbose)
                if not ipldhash:    # We might have got it now especially for _files.xml if unchanged-
                    #TODO move this to TransportIPFS when python implementation of IPFS done
                    ipfsurl = config["ipfs"]["url_add_data"]
                    if verbose: logging.debug("Posting IPFS to {0}".format(ipfsurl))
                    res = requests.post(ipfsurl, files={'file': ('', data, self.mimetype)}).json()
                    logging.debug("IPFS result={}".format(res))
                    ipldhash = res['Hash']
                    IPLDHashService.set(self.multihash.multihash58, ipldhash)
                    if verbose: logging.debug("ipfs pushed to: {}".format(ipldhash))
                    #This next line is to get around bug in IPFS propogation
                    #See https://github.com/ipfs/js-ipfs/issues/1156
                    ipfsgatewayurl = "https://ipfs.io/ipfs/{}".format(ipldhash)
                    res = requests.head(ipfsgatewayurl); # Going to ignore the result
                    logging.debug("XXX@202 - ran priming process on ipfs.io to work around JS-IPFS issue #1156")
        if self.multihash:
            LocationService.set(self.multihash.multihash58, url, verbose=verbose)
        return {"ipldhash": ipldhash}


class NameResolverShard(NameResolver):
    """
    Represents a single shard returned by a NameResolverFile.shards() iterator
    Holds enough info to do a byte-range retrieval of just those bytes from a server,
    And a multihash that could be retrieved by IPFS for just this shard.
    """
    pass


class NameResolverSearchItem(NameResolver):
    """
    Represents each element in a search
    """
    pass


class NameResolverSearch(NameResolver):
    """
    Represents the results of a search
    """
    pass
