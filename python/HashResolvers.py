import logging
from .NameResolver import NameResolverFile
from .miscutils import loads, dumps, httpget
from .Errors import CodingException, NoContentException, ForbiddenException
from .HashStore import LocationService, MimetypeService
from .LocalResolver import LocalResolverFetch
from .Multihash import Multihash
from .DOI import DOIfile
from .Archive import ArchiveItem, ArchiveFile
from .config import config


class HashResolver(NameResolverFile):
    """
    Base class for Sha1Hex and ContentHash - used where we are instantiating something of unknown type from a hash of some form.

    Sha1Hex & ContentHash are classes for retrieval by a hash
    typically of form   sha1hex/1a2b3c for SHA1

    Implements name resolution of the ContentHash namespace, via a local store and any other internal archive method

    Future Work
    * Build way to preload the hashstore with the hashes and URLs from various parts of the Archive
    """
    namespace = None       # Defined in subclasses
    multihashfield = None  # Defined in subclasses
    archivefilemetadatafield = None # Defined in subclasses

    def __init__(self, namespace, hash, **kwargs):
        """
        Creates the object

        :param namespace:   "contenthash"
        :param hash:        Hash representing the object - format is specified by namespace
        :param kwargs:      Any other args to the URL, ignored for now.
        """
        """
        Pseudo-code
        Looks up the multihash in Location Service to find where can be retrieved from, does not retrieve it. 
        """
        verbose = kwargs.get("verbose")
        if verbose:
            logging.debug("{0}.__init__({1}, {2}, {3})".format(self.__class__.__name__, namespace, hash, kwargs))
        if namespace != self.namespace:  # Defined in subclasses
            raise CodingException(message="namespace != "+self.namespace)
        super(HashResolver, self).__init__(self, namespace, hash, **kwargs)  # Note ignores the name
        self.multihash = Multihash(**{self.multihashfield: hash})
        self.url = LocationService.get(self.multihash.multihash58, verbose)  #TODO-FUTURE recognize different types of location, currently assumes URL
        self.mimetype = MimetypeService.get(self.multihash.multihash58, verbose)    # Should be after DOIfile resolution, which will set mimetype in MimetypeService
        self._metadata = None   # Not resolved yet
        self._doifile = None   # Not resolved yet

    # noinspection PyMethodOverriding
    @classmethod
    def new(cls, namespace, hash, *args, **kwargs):
        """
        #TODO-SHA1HEX create a superclass once tested
        Called by ServerGateway to handle a URL - passed the parts of the remainder of the URL after the requested format,

        :param namespace:
        :param hash:            hash or next part of name within namespace
        :param args:            rest of path
        :param kwargs:
        :return:
        :raise NoContentException: if cant find content directly or via other classes (like DOIfile)
        """
        verbose = kwargs.get("verbose")
        if hash == HashFileEmpty.emptymeta[cls.archivefilemetadatafield]:
            return HashFileEmpty(verbose)   # Empty file
        ch = super(HashResolver, cls).new(namespace, hash, *args, **kwargs)    # By default (on NameResolver) calls cls() which goes to __init__
        if not ch.url:
            if verbose: logging.debug("No URL, looking on archive for {0}.{1}".format(namespace, hash))
            #!SEE-OTHERHASHES -this is where we look things up in the DOI.sql etc essentially cycle through some other classes, asking if they know the URL
            # ch = DOIfile(multihash=ch.multihash).url  # Will fill in url if known. Note will now return a DOIfile, not a Sha1Hex
            return ch.searcharchivefor(verbose=verbose)  # Will now be a ArchiveFile
        if ch.url.startswith("local:"):
            ch = LocalResolverFetch.new("rawfetch", hash, **kwargs)
        if not (ch and ch.url):
            raise NoContentException()
        return ch

    def push(self, obj):
        """
        Add a Shard to a ContentHash -
        :return:
        """
        pass  # Note could probably be defined on NameResolverFile class

    def retrieve(self, verbose=False, **kwargsx):
        """
        Fetch the content, dont pass to caller (typically called by NameResolver.content()

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
            return httpget(self.url)

    def searcharchivefor(self, multihash=None, verbose=False, **kwargs):
        # Note this only works on certain machines
        # And will return a ArchiveFile
        searchurl = "http://archive.org/services/dwhf.php?key=sha1&val={}".format((multihash or self.multihash).sha1hex)
        res = loads(httpget(searchurl))
        logging.info("XXX@searcharchivefor res={}".format(res))
        if res.get("error"):
            # {"error": "internal use only"}
            raise ForbiddenException(what="SHA1 search from machine unless its whitelisted by Aaron")
        if not res["hits"]["total"]:
            # {"key":"sha1","val":"88d4b0d91acd3c25139804afbf4aef4e675bef63","hits":{"total":0,"matches":[]}}
            raise NoContentException()
        # {"key": "sha1", "val": "88...2", "hits": {"total": 1, "matches": [{"identifier": ["<ITEMID>"],"name": ["<FILENAME>"]}]}}
        firstmatch = res["hits"]["matches"][0]
        logging.info("ArchiveFile.new({},{},{}".format("archiveid", firstmatch["identifier"][0], firstmatch["name"][0]))
        return ArchiveItem.new("archiveid", firstmatch["identifier"][0], firstmatch["name"][0], verbose=True)  # Note uses ArchiveItem because need to retrieve item level metadata as well

    def content(self, verbose=False, **kwargs):
        """
        :returns:   content - i.e. bytes
        """
        data = self.retrieve()
        if verbose: logging.debug("Retrieved doc size={}".format(len(data)))
        return  {'Content-type': self.mimetype,
                 'data': data,
                }

    def metadata(self, headers=True, verbose=False, **kwargs):
        """
        :param verbose:
        :param headers: true if caller wants HTTP response headers
        :return:
        """
        logging.info("XXX@HR.metadata m={}, u={}".format(self._metadata, self.url))
        if not self._metadata:
            try:
                if not self._doifile:
                    self._doifile = DOIfile(multihash=self.multihash, verbose=verbose)    # If not found, dont set url/metadata etc raises NoContentException
                self._metadata = self._metadata or (
                            self._doifile and self._doifile.metadata(headers=False, verbose=verbose))
            except NoContentException as e:
                pass    # Ignore absence of DOI file, try next
        if not self._metadata and self.url and self.url.startswith(config["archive"]["url_download"]):
            u = self.url[len(config["archive"]["url_download"]):].split('/')   # [ itemid, filename ]
            self._metadata = ArchiveItem.new("archiveid", *u).metadata(headers=False)  # Note will retun an ArchiveFile since passing the filename
        mimetype = 'application/json'   # Note this is the mimetype of the response, not the mimetype of the file
        return {"Content-type": mimetype, "data": self._metadata} if headers else self._metadata

    # def canonical - not needed as already in a canonical form


class Sha1Hex(HashResolver):
    """
    URL: `/xxx/sha1hex/Q...` (forwarded here by ServerGateway methods)
    """
    namespace = "sha1hex"
    multihashfield = "sha1hex"    # Field to Multihash.init
    archivefilemetadatafield = "sha1"


class ContentHash(HashResolver):
    """
    URL: `/xxx/contenthash/Q...` (forwarded here by ServerGateway methods)
    """
    namespace = "contenthash"
    multihashfield = "multihash58"    # Field to Multihash.init
    archivefilemetadatafield = "multihash58"    # Not quite true, really combined into URL in "contenthash" but this is for detecting emptyhash

class HashFileEmpty(HashResolver):
    # Catch special case of an empty file and deliver an empty file
    emptymeta = {  # Example from archive.org/metadata/AboutBan1935/AboutBan1935.asr.srt
        "name": "emptyfile.txt",
        "source": "original",
        "format": "Unknown",
        "size": "0",
        "md5": "d41d8cd98f00b204e9800998ecf8427e",
        "crc32": "00000000",
        "sha1": "da39a3ee5e6b4b0d3255bfef95601890afd80709",
        "contenthash": "contenthash:/contenthash/5dtpkBuw5TeS42SJSTt33HCE3ht4rC",
        "multihash58": "5dtpkBuw5TeS42SJSTt33HCE3ht4rC",
    }

    # noinspection PyMissingConstructor
    def __init__(self, verbose=False):
        # Intentionally not calling superclass's init.
        self.mimetype = "application/octet-stream"

    def retrieve(self, _headers=None, verbose=False, **kwargs):
        # Return a empty file
        return ''

    def metadata(self, headers=None, verbose=False, **kwargs):
        mimetype = 'application/json'   # Note this is the mimetype of the response, not the mimetype of the file
        return {"Content-type": mimetype, "data": self.emptymeta } if headers else self.emptymeta
