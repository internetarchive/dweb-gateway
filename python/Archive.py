# encoding: utf-8
import logging
from magneturi import bencode
import base64
import hashlib
import requests
import urllib.parse
from datetime import datetime
from .NameResolver import NameResolverDir, NameResolverFile
from .miscutils import loads, dumps, httpget
from .config import config
from .Multihash import Multihash
from .Errors import CodingException, MyBaseException, IPFSException
from .HashStore import MagnetLinkService, ThumbnailIPFSfromItemIdService, TitleService
from .TransportIPFS import TransportIPFS
from .LocalResolver import KeyValueTable

archiveconfig = {
    "staticnames": {    # Build static collection names here for fake collections that dont respond to search below
        # "additional-collections": "Additional Collections", # Looks like typo for additional_collections
    },
}

class ArchiveItemNotFound(MyBaseException):
    httperror = 404
    msg = "Archive item {itemid} not found"


class AdvancedSearch(NameResolverDir):
    """
    Subclass of NameResolverDir to do an Archive advanced search.

    Note this might get broken up into appropriate class hierarchy as other IA interfaces build
    Urls like /metadata/advancedsearch?x=y,a=b

    Attributes:

    Supports:
    metadata    JSON Output as it comes from Archive's advancedsearch

    Tests are in test/
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
        obj.query = "https://archive.org/advancedsearch.php?" + '&'.join([k + "=" + v for (k, v) in kwargs.items()])
        # TODO-DETAILS may need to handle url escaping, i.e. some queries may be invalid till that is done
        if verbose: logging.debug("AdvancedSearch url={0}".format(obj.query))
        res = httpget(obj.query)
        obj.res = loads(res)  # TODO unsure if there are any possible errors, and if so how to handle them.
        for doc in obj.res["response"]["docs"]:
            doc["thumbnaillinks"] = ArchiveItem.item2thumbnail(doc["identifier"], verbose)
            collection0id = doc["collection"][0] if isinstance(doc["collection"], (list, tuple, set)) else doc["collection"]
            doc["collection0title"] = cls.collectionTitle(collection0id, verbose)
            doc["collection0thumbnaillinks"] = ArchiveItem.item2thumbnail(collection0id, verbose)
        obj._list = obj.res["response"]["docs"]  # TODO probably wrong, as prob needs to be NameResolver instances
        if verbose: logging.debug("AdvancedSearch found {0} items".format(len(obj._list)))
        return obj

    def metadata(self, headers=True, verbose=False, **kwargs):
        """
        Pass metadata (i.e. what retrieved in AdancedSearcch) directly back to client
        This is based on assumption that if/when CORS issues are fixed then client will go direct to this API on archive.org
        """
        mimetype = 'application/json'
        # noinspection PyUnresolvedReferences
        return {"Content-type": mimetype, "data": self.res} if headers else self.res

    @classmethod
    def collectionTitle(cls, itemid, verbose=False):
        if itemid.startswith('fav-'):
            return itemid[4:] + " favorites"
        if itemid in archiveconfig["staticnames"]:
            return archiveconfig["staticnames"][itemid]
        cached = TitleService.archiveidget(itemid, verbose)
        if cached:
            return cached
        query = "https://archive.org/advancedsearch.php?" + '&'.join([k + "=" + v for (k, v) in {'q': 'identifier:'+itemid, 'fl': 'title', 'output': 'json'}.items()])
        try:
            title = loads(httpget(query))["response"]["docs"][0]["title"]
            TitleService.archiveidset(itemid, title, verbose)
        except Exception as e:
            logging.error("Couldnt find collection title for {}, err={}".format(itemid, e))
            title = ""
        return title

# noinspection PyUnresolvedReferences
class ArchiveItem(NameResolverDir):
    """
    Subclass of NameResolverDir to do an Archive item metadata retrieval

    Note this might get broken up into appropriate class hierarchy as other IA interfaces build

    Attributes:
        itemid = itemid
        _thumbnail = list of urls of thumbnail (access via thumbnail())

    Supports: metadata
    """

    # noinspection PyMethodOverriding
    @classmethod
    def new(cls, namespace, itemid, *args, **kwargs):
        """
        Create a AdvancedSearch object, just pass on kwargs to Archive's advancedsearch API
        The existence of this is mostly because of the CORS issues with the archive.org/advancedsearch which (reasonably) blocks CORS but doesn't yet have a
        mode to ignore cookies in a CORS case. (based on discussions between Mitra & Sam)

        :param namespace:   "archiveid"
        :param itemid:      Archive item id
        :param args:       *optional - Name of file - case sensitive or none for the item
        :param kwargs:      {wanttorrent}
        :return:            ArchiveItem or ArchiveFile instance.
        :raises:        ArchiteItemNotFound if itemid invalid
        """
        verbose = kwargs.get("verbose")
        if verbose: del kwargs["verbose"]
        transport = kwargs.get("transport")
        if verbose: logging.debug("ArchiveItem lookup for {0} {1} {2}".format(itemid, args, kwargs))
        obj = super(ArchiveItem, cls).new(namespace, itemid, *args, **kwargs)
        obj.itemid = itemid
        # kwargs is ignored, there are none to archive.org/metadata
        obj.query = "https://archive.org/metadata/{}".format(itemid)
        # TODO-DETAILS may need to handle url escaping, i.e. some queries may be invalid till that is done
        if verbose: logging.debug("Archive Metadata url={0}".format(obj.query))
        res = httpget(obj.query)
        obj._metadata = loads(res)
        if not obj._metadata:  # metadata retrieval failed, itemid probably false
            raise ArchiveItemNotFound(itemid=itemid)
        obj.setmagnetlink(wantmodified=True, wanttorrent=kwargs.get("wanttorrent", False), verbose=verbose)  # Set a modified magnet link suitable for WebTorrent
        if not obj._metadata["metadata"].get("thumbnaillinks"):  # Set thumbnaillinks if not done already - can be slow as loads to IPFS
            obj._metadata["metadata"]["thumbnaillinks"] = obj.item2thumbnail(obj.itemid, verbose)
        name = "/".join(args) if args else None  # Get the name of the file if present
        if name:  # Its a single file just cache that one
            if name.startswith(".____padding_file"):    # Webtorrent convention
                return ArchiveFilePadding(verbose=verbose)
            else:
                f = [f for f in obj._metadata["files"] if f["name"] == name]
                if not f: raise Exception("Valid Archive item {} but no file called: {}".format(itemid, name))    # TODO change to islice
                return ArchiveFile.new(namespace, itemid, name, item=obj, metadata=f[0], verbose=verbose)
        else:  # Its an item - cache all the files
            obj._list = [ArchiveFile.new(namespace, itemid, f["name"], item=obj, metadata=f, transport=transport,
                                         verbose=verbose) for f in obj._metadata["files"]]
            if verbose: logging.debug("Archive Metadata found {0} files".format(len(obj._list)))
            return obj

    def metadata(self, headers=True, verbose=False, **kwargs):
        """
        Pass metadata (i.e. what retrieved in AdvancedSearch) directly back to client
        This is based on assumption that if/when CORS issues are fixed then client will go direct to this API on archive.org
        """
        obj._metadata["collection_titles"] = {k: AdvancedSearch.collectionTitle(k, verbose) for k in
                                              (obj._metadata["metadata"]["collection"]
                                               if isinstance(obj._metadata["metadata"]["collection"], (list, tuple, set))
                                               else [ obj._metadata["metadata"]["collection"]])}
        mimetype = 'application/json'
        return {"Content-type": mimetype, "data": self._metadata} if headers else self._metadata

    # noinspection PyUnresolvedReferences
    def setmagnetlink(self, wantmodified=True, wanttorrent=False, verbose=False):
        """
        Set magnet link (note could easily be modified to return torrentdata or torrentfile if wanted)
        - assume that metadata already fetched but that _metadata.files not converted to _list yet (as that process  will use this data.
        :return:
        """
        if not self._metadata:
            raise CodingException(message="Must have fetched metadata before read torrentdata")
        magnetlink = self._metadata["metadata"].get("magnetlink")  # First check the metadata
        if not magnetlink or wanttorrent:  # Skip if its already set.
            magnetlink = MagnetLinkService.archiveidget(self.itemid, verbose)  # Look for cached version
            if not magnetlink or wanttorrent:  # If not cached then build new one
                ff = [f for f in self._metadata["files"] if f.get("format") == "Archive BitTorrent"]  # Should be one or none
                if len(ff):
                    if len(ff) > 1: raise CodingException(message='Should be exactly one "Archive BitTorrent" file')
                    torrentfilemeta = ff[0]
                    torrentfileurl = "{}{}/{}".format(config["archive"]["url_download"], self.itemid, torrentfilemeta["name"])
                    try:
                        torrentcontents = httpget(torrentfileurl, wantmime=False)
                    except requests.exceptions.HTTPError as e:
                        logging.warning("Inaccessible torrent at {}, {}".format(torrentfileurl, e))
                        return  # Its ok if cant get a torrent
                    try:
                    # noinspection PyAttributeOutsideInit
                        self.torrentdata = bencode.bdecode(torrentcontents)  # Convert to a object
                    except bencode.DecodingException as e:
                        # Probably a magneturi.bencode.DecodingException - there are lots of bad torrents, mostly skipped cos files too big (according to Aaron Ximm)
                        logging.warning("Bad Torrent file at: {}".format(torrentfileurl))
                        return  # Dont need to throw an error - we'll just skip it
                    assert (bencode.bencode(self.torrentdata) == torrentcontents)
                    hash_contents = bencode.bencode(self.torrentdata['info'])
                    digest = hashlib.sha1(hash_contents).digest()
                    b32hash = base64.b32encode(digest)  # Get the hash of the torrent file
                    b32hashascii = b32hash.decode('ASCII')
                    # Now possible revise the data since IA torrents as of Dec2017 have issues, this doesnt change the hash.

                    if wantmodified:  # Normally we want the torrent file modified to support WebTorrent and not use HTTP URLs
                        # The trackers at bt1 and bt2 are http, but they dont support webtorrent anyway so that doesnt matter.
                        webtorrenttrackerlist = ['wss://tracker.btorrent.xyz', 'wss://tracker.openwebtorrent.com',
                                                 'wss://tracker.fastcast.nz']
                        self.torrentdata["announce-list"] += [[wtt] for wtt in webtorrenttrackerlist]
                        # Note announce-list is never empty after this, so can ignore announce field
                        #  Replace http with https (as cant call http from https) BUT still has cors issues
                        # self.torrentdata["url-list"] = [ u.replace("http://","https://") for u in self.torrentdata["url-list"] ]
                        self.torrentdata["url-list"] = [config["gateway"]["url_download"]]  # Has trailing slash
                        externaltorrenturl = "{}{}".format(config["gateway"]["url_torrent"], self.itemid)  # Intentionally no file name, we are modifying it
                    else:
                        externaltorrenturl = "{}{}/{}".format(config["archive"]["url_download"], self.itemid, torrentfilemeta["name"])
                    magnetlink = ''.join([
                        'magnet:?xt=urn:btih:', b32hashascii,
                        ''.join(['&tr=' + urllib.parse.quote_plus(t[0]) for t in self.torrentdata['announce-list']]),
                        ''.join(['&ws=' + urllib.parse.quote_plus(t)
                                 for t in self.torrentdata['url-list']]),
                        '&xs=', urllib.parse.quote_plus(externaltorrenturl),
                    ])
                    MagnetLinkService.archiveidset(self.itemid, magnetlink, verbose)  # Cache it
                    if verbose: logging.info("New magnetlink for item: {}, {}".format(self.itemid, magnetlink))
                    # We should probably extract the b32hashascii from the magnetlink if we already have one
                    MagnetLinkService.btihset(b32hashascii, magnetlink, verbose)  # Cache mapping from torrenthash to magnetlink
            if magnetlink:
                self._metadata["metadata"]["magnetlink"] = magnetlink  # Store on metadata if have one
        if verbose: logging.info("Magnetlink for {} = {}".format(self.itemid, magnetlink))

    def torrent(self, headers=True, verbose=False):
        """
        Output the torrent
        :return:
        """
        mimetype = "application/x-bittorrent"
        data = bencode.bencode(self.torrentdata)   # Set in ArchiveItem.new > setmagnetlink
        return {"Content-type": mimetype, "data": data} if headers else data

    def leaf(self, headers=True, verbose=False):
        """
        Resolve names to a Lead (a pointer to a metadata record)

        :param headers:
        :param verbose:
        :raises: IPFSException if cant reach IPFS
        :return:
        """
        # TODO-DOMAIN - push metadata to IPFS, save IPFS hash
        # TODO-DOMAIN - create Name record from IPFS hash & contenthash
        # TODO-DOMAIN - store Name record on local nameservice (set)
        # TODO-DOMAIN - return Name record to caller
        metadata = self.metadata(headers=False, verbose=verbose)
        # Store in IPFS, note cant use urlstore on IPFS as metadata is mutable
        try:
            ipfsurl = TransportIPFS().store(data=metadata, verbose=verbose, mimetype="application/json")
        except Exception as e:
            raise IPFSException(message=e)
        # TODO-DOMAIN probably encapsulate construction of name once all tested
        pkeymetadatadomain = config["domains"]["metadata"]
        server = "https://gateway.dweb.me"
        #server = "http://localhost:4244"  # TODO-DOMAIN just for testing
        leaf = {
            # expires:   # Not needed, a later dated version is sufficient.
            "fullname": "/arc/archive.org/metadata/{}".format(self.itemid),
            "signatures": [],
            "table": "leaf",
            "urls": [ipfsurl, "{}/metadata/archiveid/{}".format(server, self.itemid)]  # Where to get the content
        }
        datenow = datetime.utcnow().isoformat()
        signable = dumps({"date": datenow, "signed": {k: leaf.get(k) for k in ["urls", "fullname", "expires"]}})  # TODO-DOMAIN-DOC matches SignatureMixin.call in Domain.js
        keypair = None  # TODO-DOMAIN need keypair, which might mean porting the old library.
        signature = "FAKEFAKEFAKE"  # TODO-DOMAIN obviously remove this fake signature and sign "signable"
        pubkeyexport = "FAKEFAKEFAKE"  # TODO-DOMAIN obviously remove this fake signature
        leaf["signatures"].append({"date": datenow, "signature": signature, "signedby": pubkeyexport})
        # TODO-DOMAIN now have encapsulated leaf
        # Store the domain in the http domain server, its also always going to be retrievable from this gateway, we cant write to YJS, but a client can copy it TODO-DOMAIN
        # Next two lines would be if adding to HTTP on different machine, instead assuming this machine *is* the KeyValueTable we can go direct.
        # tableurl = "{}/get/table/{}/domains".format(server, pkeymetadatadomain)
        # TransportHTTP().set(tableurl, self.itemid, dumps(leaf), verbose)  # TODO-DOMAIN need to write TransportHTTP
        KeyValueTable.new("table", pkeymetadatadomain, "domain", verbose=verbose)\
            .set(headers=False, verbose=verbose, data=[{"key": self.itemid, "value": dumps(leaf)}])
        mimetype = 'application/json'
        data = {self.itemid: dumps(leaf)}
        return {"Content-type": mimetype, "data": data} if headers else data

    @classmethod
    def item2thumbnail(cls, itemid, verbose=False):
        """
        Set the thumbnail field if not set and return list of urls
        :return:    Array of links to thumbnail - usually IPFS, then HTTP via gateway
        """
        archive_servicesimgurl = "{}{}".format(config["archive"]["url_servicesimg"], itemid)  # Note similar code in torrentdata
        archive_servicesimgurl_cors = "{}{}".format(config["gateway"]["url_servicesimg"], itemid)  # Note similar code in torrentdata
        thumbnailipfsurl = ThumbnailIPFSfromItemIdService.get(itemid)
        if not thumbnailipfsurl:  # Dont have IPFS URL
            if verbose: logging.debug("Retrieving thumbnail for {}".format(itemid))
            # Store to IPFS and if still reqd then ping the ipfs.io gateway
            thumbnailipfsurl = TransportIPFS().store(urlfrom=archive_servicesimgurl, verbose=verbose,
                                                     mimetype="image/PNG")
            ThumbnailIPFSfromItemIdService.set(itemid, thumbnailipfsurl)
        return [thumbnailipfsurl, archive_servicesimgurl_cors]

    def thumbnail(self, headers=True, verbose=False):
        (data, mimetype) = httpget("{}{}".format(config["archive"]["url_servicesimg"], self.itemid), wantmime=True)
        return {"Content-type": mimetype, "data": data} if headers else data

# noinspection PyProtectedMember
class ArchiveFile(NameResolverFile):
    """
    A file inside an item directory
    """

    # noinspection PyMethodOverriding
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
            logging.debug("No sha1 for file:{}/{}".format(itemid, filename))
        if obj.parent._metadata["metadata"].get("magnetlink"):
            obj._metadata["magnetlink"] = "{}/{}".format(obj.parent._metadata["metadata"]["magnetlink"], filename)
        if obj.multihash:  # For the _files.xml there is no SHA1 and if didn't fetch to cache for IPFS then we cant set it
            obj._metadata["contenthash"] = "contenthash:/contenthash/{}".format(obj.multihash.multihash58)
        # Comment out next line unless checking integrity
        # obj.check(verbose)
        return obj

    def cache_content(self, transport, verbose):
        # Currently remaining args an kwargs ignored
        if not self.filename.endswith("_files.xml"):  # Dont waste energy saving stuff about _files.xml as it doesnt have a sha1 for timing reasons (contains sha1's of files).
            cached = super(ArchiveFile, self).cache_content(self.archive_url, transport, verbose)  # Setup for IPFS and contenthash returns {ipldhash}
            if cached.get("ipldhash") is not None:
                self._metadata["ipfs"] = "ipfs:/ipfs/{}".format(cached["ipldhash"])  # Add to IPFS hash returned

    def check(self, verbose):
        (data, mimetype) = httpget(self.archive_url, wantmime=True)
        assert self.mimetype == mimetype, "mimetype mismatch on {}/{}".format(self.itemid, self.filename)
        self.multihash.check(data)

    def metadata(self, headers=True, verbose=False, **kwargs):
        """
        Return metadata for file - note in most cases for a ArchiveFile its metadata is returned from its parent ArchiveItem
        :param verbose:
        :param headers: true if should return encapsulated in suitable headers for returning to http
        :return:
        """
        transport = kwargs.get("transport")  # None or list of transports
        self.cache_content(transport, verbose);               # Done on ArchiveFile rather than on new() because its too slow to do unless we need it.
        mimetype = 'application/json'
        return {"Content-type": mimetype, "data": self._metadata} if headers else self._metadata

    @property
    def archive_url(self):
        return "{}{}/{}".format(config["archive"]["url_download"], self.itemid, self._metadata["name"])  # Note similar code in torrentdata

    # NOT COMPLETE YET
    # @property
    # ef cachefilename(self):
    #    return "{}/{}/{}".format(config["cache"]["archiveid"],self.itemid, self._metadata["name"])

    # noinspection PyAttributeOutsideInit
    def retrieve(self, _headers=None, verbose=False, **kwargs):
        (data, self.mimetype) = httpget(self.archive_url, wantmime=True, range=_headers.get("range"))
        return data

    def content(self, _headers=None, verbose=False, **kwargs):   # Equivalent to archive.org/downloads/xxx/yyy but gets around cors problems
        (data, self.mimetype) = httpget(self.archive_url, wantmime=True, range=_headers.get("range"))
        return {"Content-type": self.mimetype, "data": data}


class ArchiveFilePadding(ArchiveFile):
    # Catch special case of ".____padding_file/nnn" and deliver a range of 0 bytes.
    # This is supposed to be a bittorrent convention, and Archive.org uses it to pad files out to block boundaries, so that new files can be loaded from whole blocks
    # It also makes it much easier to edit a torrent and rebuild new from old.

    # noinspection PyMissingConstructor
    def __init__(self, verbose=False):
        # Intentionally not calling superclass's init.
        self.mimetype = "application/octet-stream"

    def retrieve(self, _headers=None, verbose=False, **kwargs):
        # Return a string of nulls of a length specified by the range header
        # TODO better error handling
        _range = _headers.get("range")
        logging.debug("XXX@255 {}".format(_range))  # bytes=32976781-33501068
        rr = _range[6:].split('-')
        rangelength = int(rr[1]) - int(rr[0]) + 1
        logging.debug("XXX@261 {} bytes".format(rangelength))  # bytes=32976781-33501068
        return '\0' * rangelength
