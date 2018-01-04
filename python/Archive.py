import logging
from magneturi import bencode
import base64
import hashlib
import urllib.parse
from .NameResolver import NameResolverDir, NameResolverFile
from .miscutils import loads, dumps, httpget
from .config import config
from .Multihash import Multihash
from .Errors import CodingException

class AdvancedSearch(NameResolverDir):
    """
    Subclass of NameResolverDir to do an Archive advanced search.

    Note this might get broken up into appropriate class hierarchy as other IA interfaces build

    Attributes:

    Supports:
    metadata    JSON Output as it comes from Archive's advancedsearch
    """

    @classmethod
    def new(cls, namespace, *args, **kwargs):
        """
        Create a AdvancedSearch object, just pass on kwargs to Archive's advancedsearch API
        The existance of this is mostly because of the CORS issues with the archive.org/advancedsearch which (reasonably) blocks CORS but doesn't yet have a
        mode to ignore cookies in a CORS case. (based on discussions between Mitra & Sam)

        :param namespace:
        :param args:
        :param kwargs:
        :return:
        """
        verbose = kwargs.get("verbose")
        if verbose: del kwargs["verbose"]
        if verbose: logging.debug("AdvancedSearch for {0} {1}".format(args, kwargs))
        obj = super(AdvancedSearch, cls).new(namespace, *args, **kwargs)
        # args is ignored, there are none to advancedsearch
        obj.query = "https://archive.org/advancedsearch.php?" + ('&').join([ k+"="+v for (k,v) in kwargs.items()])
        #TODO-DETAILS may need to handle url escaping, i.e. some queries may be invalid till that is done
        if verbose: logging.debug("AdvancedSearch url={0}".format(obj.query))
        res = httpget(obj.query)
        obj.res = loads(res) #TODO-ERRORS handle error if cant find item for example
        obj._list = obj.res["response"]["docs"]  # TODO probably wrong, as prob needs to be NameResolver instances
        if verbose: logging.debug("AdvancedSearch found {0} items".format(len(obj._list)))
        return obj

    def metadata(self, verbose=False):
        """
        Pass metadata (i.e. what retrieved in AdancedSearcch) directly back to client
        This is based on assumption that if/when CORS issues are fixed then client will go direct to this API on archive.org
        """
        return {'Content-type': 'application/json',
                'data': self.res
                }


class ArchiveItem(NameResolverDir):
    """
    Subclass of NameResolverDir to do an Archive item metadata retrieval

    Note this might get broken up into appropriate class hierarchy as other IA interfaces build

    Attributes:
        itemid = itemid

    Supports: metadata
    """

    @classmethod
    def new(cls, namespace, itemid, *args, **kwargs):
        """
        Create a AdvancedSearch object, just pass on kwargs to Archive's advancedsearch API
        The existance of this is mostly because of the CORS issues with the archive.org/advancedsearch which (reasonably) blocks CORS but doesn't yet have a
        mode to ignore cookies in a CORS case. (based on discussions between Mitra & Sam)

        :param namespace:   "archiveid"
        :param itemid:      Archive item id
        :param name:
        :param optional *args: Name of file - case sensitive or none for the item
        :param kwargs:
        :return:            ArchiveItem or ArchiveFile instance.
        """
        verbose = kwargs.get("verbose")
        if verbose: del kwargs["verbose"]
        if verbose: logging.debug("ArchiveItem lookup for {0} {1} {2}".format(itemid, args, kwargs))
        obj = super(ArchiveItem, cls).new(namespace, itemid, *args, **kwargs)
        obj.itemid = itemid
        # kwargs is ignored, there are none to archive.org/metadata
        obj.query = "https://archive.org/metadata/{}".format(itemid)
        #TODO-DETAILS may need to handle url escaping, i.e. some queries may be invalid till that is done
        if verbose: logging.debug("Archive Metadata url={0}".format(obj.query))
        res = httpget(obj.query)
        obj._metadata = loads(res) #TODO-ERRORS handle error if cant find item for example
        obj.setmagnetlink(True)    # Set a modified magnet link suitable for WebTorrent
        name = name = args[0] if args else None # Get the name of the file if present
        if name: # Its a single file just cache that one
            f = [ f for f in obj._metadata["files"] if f["name"] == name ]
            if (not f): raise Error("Valid Archive item {} but no file called: {}".format(itemid, name))    #TODO change to islice
            return ArchiveFile.new(namespace, itemid, name, item=obj, metadata=f[0], verbose=verbose)
        else: # Its an item - cache all the files
            obj._list = [ ArchiveFile.new(namespace, itemid, f["name"], item=obj, metadata=f, verbose=verbose) for f in obj._metadata["files"]]
            if verbose: logging.debug("Archive Metadata found {0} files".format(len(obj._list)))
            return obj


    def metadata(self, verbose=False):
        """
        Pass metadata (i.e. what retrieved in AdancedSearcch) directly back to client
        This is based on assumption that if/when CORS issues are fixed then client will go direct to this API on archive.org
        """
        return {'Content-type': 'application/json',

                'data':
                    self._metadata
                }

    def setmagnetlink(self, wantmodified):
        """
        Set magnet link (note could easily be modified to return torrentdata or torrentfile if wanted)
        - assume that metadata already fetched but that _metadata.files not converted to _list yet (as that process  will use this data.
        :return:
        """
        if not self._metadata: raise CodingException(message="Must have fetched metadata before read torrentdata")
        ff = [ f for f in self._metadata["files"] if f.get("format") == "Archive BitTorrent" ]
        if not len(ff) == 1: raise CodingException(message='Should be exactly one "Archive BitTorrent" file')
        torrentfilemeta = ff[0]
        torrentfileurl = "{}{}/{}".format(config["archive"]["url_download"], self.itemid, torrentfilemeta["name"])
        torrentcontents = httpget(torrentfileurl, wantmime=False)
        self.torrentdata = bencode.bdecode(torrentcontents)  # Convert to a object
        assert (bencode.bencode(self.torrentdata) == torrentcontents)
        hash_contents = bencode.bencode(self.torrentdata['info'])
        digest = hashlib.sha1(hash_contents).digest()
        b32hash = base64.b32encode(digest)  # Get the hash of the torrent file
        # Now revise the data since IA torrents as of Dec2017 have issues

        if wantmodified:
            # The trackers at bt1 and bt2 are http, but they dont support webtorrent anyway so that doesnt matter.
            webtorrenttrackerlist = ['wss://tracker.btorrent.xyz', 'wss://tracker.openwebtorrent.com',
                                     'wss://tracker.fastcast.nz']
            self.torrentdata["announce-list"] += [[wtt] for wtt in webtorrenttrackerlist]
            # Note announce-list is never empty after this, so can ignore announce field
            #  Replace http with https (as cant call http from https) BUT still has cors issues
            # self.torrentdata["url-list"] = [ u.replace("http://","https://") for u in self.torrentdata["url-list"] ]
            self.torrentdata["url-list"] = [config["gateway"]["url_download"]]  # Has trailing slash
            externaltorrenturl = "{}{}".format(config["gateway"]["url_torrent"], self.itemid) # Intentionally no file name, we are modifying it
        else:
            externaltorrenturl = "{}{}/{}".format(config["archive"]["url_download"], self.itemid, torrentfilemeta["name"] )
        magnetlink = ''.join([
            'magnet:?xt=urn:btih:', b32hash.decode('ASCII'),
            ''.join(['&tr=' + urllib.parse.quote_plus(t[0]) for t in self.torrentdata['announce-list']]),
            ''.join(['&ws=' + urllib.parse.quote_plus(t) \
                     for t in self.torrentdata['url-list']]),
            '&xs=', urllib.parse.quote_plus(externaltorrenturl),
        ])
        self._metadata["metadata"]["magnetlink"] = magnetlink
        return

    def torrent(self, headers=True, verbose=False):
        """
        Output the torrent
        :return:
        """
        mimetype = "application/x-bittorrent"
        data = bencode.bencode(self.torrentdata)
        return {"Content-type": mimetype, "data": data} if headers else data

class ArchiveFile(NameResolverFile):
    """
    A file inside an item directory
    """
    @classmethod
    def new(cls, namespace, itemid, filename, *args, **kwargs):
        verbose = kwargs.get("verbose")
        if verbose: logging.debug("ArchiveFile: {}/{}".format(itemid, filename))
        obj = super(ArchiveFile, cls).new(namespace, itemid, filename, *args, **kwargs)
        obj.itemid = itemid
        obj.filename = filename
        obj._metadata = kwargs.get("metadata")   # This is the metadata included in files portion of parent's metadata query - note its likely to be a pointer into the parent's datastructure
        obj.parent = kwargs.get("item")
        if obj._metadata and obj._metadata.get("sha1"):
            obj.multihash = Multihash(sha1hex=obj._metadata["sha1"])
        else:
            obj.multihash = None
            logging.debug("No sha1 for file:".format(itemid, filename))
        # Currently remaining args an kwargs ignored
        cached = obj.cache_content(obj.archive_url, verbose)    # Setup for IPFS and contenthash {ipldhash}
        obj._metadata["magnetlink"] = "{}/{}".format(obj.parent._metadata["metadata"]["magnetlink"], filename)
        obj._metadata["ipfs"] = "ipfs:/ipfs/{}".format(cached["ipldhash"]) # Add to IPFS hash returned
        obj._metadata["contenthash"] = "contenthash:/contenthash/{}".format(obj.multihash.multihash58)
        # Comment out next line unless checking integrity
        #obj.check(verbose)
        return obj

    def check(self, verbose):
        (data, mimetype) = httpget(self.archive_url, wantmime=True)
        assert self.mimetype == mimetype, "mimetype mismatch on {}/{}".format(self.itemid, self.filename)
        self.multihash.check(data)

    def metadata(self, verbose=False):
        """
        Return metadata for file - note in most cases for a ArchiveFile its metadata is returned from its parent ArchiveItem
        :param verbose:
        :return:
        """
        return {'Content-type': 'application/json',
                'data': self._metadata
                }

    @property
    def archive_url(self):
        return "{}{}/{}".format(config["archive"]["url_download"], self.itemid, self._metadata["name"]) # Note similar code in torrentdata

    # NOT COMPLETE YET
    # @property
    #ef cachefilename(self):
    #    return "{}/{}/{}".format(config["cache"]["archiveid"],self.itemid, self._metadata["name"])

    def retrieve(self, _headers=None, verbose=False, **kwargs):
        (data, self.mimetype) = httpget(self.archive_url, wantmime=True, range=_headers.get("range"))
        return data

    def content(self, _headers=None, verbose=False, **kwargs):   #Equivalent to archive.org/downloads/xxx/yyy but gets around cors problems
        return {"Content-type": self.mimetype, "data": self.retrieve(_headers=_headers, verbose=verbose)}


