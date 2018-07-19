import logging
from .NameResolver import NameResolverDir
from .Errors import CodingException, ToBeImplementedException, NoContentException
from .HashStore import MagnetLinkService
from .miscutils import httpget, loads
from .config import config
from .Archive import ArchiveItem
from magneturi import bencode


class BtihResolver(NameResolverDir):
    """
    Resolve BitTorrent Hashes
    Fields:
    btih                # BitTorrent hash - in ascii B32 format

    This could also easily be extended to
    Support "magnetlink" as the thing being looked for (and return btih and other outputs)
    Support outputs of itemid, metadata (of item)

    """
    namespace="btih"      # Defined in subclasses

    def __init__(self, namespace, hash, **kwargs):
        """
        Creates the object

        :param namespace:   "btih"
        :param hash:        Hash representing the object - format is specified by namespace
        :param kwargs:      Any other args to the URL, ignored for now.
        """
        verbose=kwargs.get("verbose")
        if verbose:
            logging.debug("{0}.__init__({1}, {2}, {3})".format(self.__class__.__name__, namespace, hash, kwargs))
        if namespace != self.namespace: # Checked though should be determined by ServerGateway mapping
            raise CodingException(message="namespace != "+self.namespace)
        super(BtihResolver, self).__init__(self, namespace, hash, **kwargs) # Note ignores the namespace
        self.btih = hash    # Ascii B32 version of hash

    @classmethod
    def new(cls, namespace, hash, *args, **kwargs):
        """
        Called by ServerGateway to handle a URL - passed the parts of the remainder of the URL after the requested format,

        :param namespace:
        :param args:
        :param kwargs:
        :return:
        :raise NoContentException: if cant find content directly or via other classes (like DOIfile)
        """
        verbose=kwargs.get("verbose")
        ch = super(BtihResolver, cls).new(namespace, hash, *args, **kwargs)    # By default (on NameResolver) calls cls() which goes to __init__
        return ch

    def itemid(self, verbose=False, **kwargs):
        searchurl = config["archive"]["url_btihsearch"] + self.btih
        searchres = loads(httpget(searchurl))
        if not searchres["response"]["numFound"]:
            return None
        return searchres["response"]["docs"][0]["identifier"]

    def retrieve(self, verbose=False, **kwargs):
        """
        Fetch the content, dont pass to caller (typically called by NameResolver.content()
        TODO - if needed can retrieve the torrent file here - look at HashStore for example of getting from self.url

        :returns:   content - i.e. bytes
        """
        raise ToBeImplementedException("btih retrieve")

    def content(self, verbose=False, **kwargs):
        """
        :returns:   content - i.e. bytes
        """
        data = self.retrieve()
        if verbose: logging.debug("Retrieved doc size={}".format(len(data)))
        return {'Content-type': self.mimetype,
            'data': data,
            }

    def metadata(self, headers=True, verbose=False, **kwargs):
        """
        :param verbose:
        :return:
        """
        raise ToBeImplementedException(name="btih.metadata()")

    def magnetlink(self, verbose=False, headers=False, **kwargs):
        magnetlink = MagnetLinkService.btihget(self.btih)
        data = magnetlink or "" # Current paths mean we should have it, but if not we'll return "" as we have no way of doing that lookup
        return {"Content-type": "text/plain", "data": data} if headers else data

    def torrenturl(self, verbose=False):
        itemid = self.itemid(verbose=verbose)
        if not itemid:
            raise NoContentException()
        return "https://archive.org/download/{}/{}_archive.torrent".format(itemid, itemid)

    def torrent(self, verbose=False, headers=False, **kwargs):
        torrenturl = self.torrenturl(verbose=verbose)   # NoContentException if not found
        data = bencode.bencode(ArchiveItem.modifiedtorrent(self.itemid(), wantmodified=True, verbose=verbose))
        mimetype = "application/x-bittorrent"
        return {"Content-type": mimetype, "data": data} if headers else data

