# encoding: utf-8
# from sys import version as python_version
import logging
from .config import config
from .miscutils import mergeoptions
from .ServerBase import MyHTTPRequestHandler, exposed, HTTPdispatcherException
from .DOI import DOI
from .Errors import ToBeImplementedException, NoContentException, SearchException, TransportFileNotFound, ForbiddenException
# !SEE-OTHERNAMESPACE add new namespaces here and see other #!SEE-OTHERNAMESPACE
from .HashResolvers import ContentHash, Sha1Hex
from .LocalResolver import LocalResolverStore, LocalResolverFetch, LocalResolverList, LocalResolverAdd
from .Archive import AdvancedSearch, ArchiveItem, ArchiveItemNotFound
from .Btih import BtihResolver
from .LocalResolver import KeyValueTable
import json

"""
For documentation on this project see https://docs.google.com/document/d/1FO6Tdjz7A1yi4ABcd8vDz4vofRDUOrKapi3sESavIcc/edit# 
"""


# noinspection PyUnusedLocal,PyUnusedLocal
class DwebGatewayHTTPRequestHandler(MyHTTPRequestHandler):
    """
    Routes queries to handlers based on the first part of the URL for the output format,
    that routine will create an object by calling the constructor for the Namespace, and
    then do whatever is needed to generate the output format (typically calling a method on the created
    object, or invoking a constructor for that format.)

    GET '/outputformat/namespace/namespace_dependent_string?aaa=bbb,ccc=ddd'`

    Services exposed as "outputformat":
    /info           Returns data structure describing gateway
    /content        Return the content as interpreted for the namespace.
    /contenthash    Return the hash of the content

    outputformat:  Format wanted e.g. [IPLD](#IPLD) or [nameresolution](#nameresolution)
    namespace: is a extensible descriptor for name spaces e.g. "doi"
    namespace-dependent-string: is a string, that may contain additional "/" dependent on the namespace.
    aaa=bbb,ccc=ddd are optional arguments to the name space resolver.
    _headers contains a dictionary of HTTP headers, especially "range"

    Pseudo Code for each service
    * lookup namespace in a config table to get a class
    * Call constuctor on that class
    * obj = ConfigTable[namespace](namespace, namespace_dependent_string, aaa=bbb, ccc=ddd)
    * And convert to wanted output format by either
    * call a method on the class,  DOI(namespace, *args, **kwargs).contenthash()
    * or a constructor on another class passing the first e.g.  IPLD(DOI(namespace, *args, **kwargs)).content()
    * Encapsulate result as a dict to return via Server superclass
    *   { Content-type: result.contenttype, data: result.content() }

    Notes:
    *The namespace is passed to the specific constructor since a single name resolver might implement multiple namespaces.

    Future Work:
    #TODO-STREAM Expand the ServerBase classes to support streams as a return from these routines
    """
    defaulthttpoptions = {"ipandport": ('0.0.0.0', 4244)}   # Was localhost, but need it to answer on all ports
    onlyexposed = True          # Only allow calls to @exposed methods
    expectedExceptions = (NoContentException, ArchiveItemNotFound, HTTPdispatcherException, TransportFileNotFound, ForbiddenException)     # List any exceptions that you "expect" (and don't want stacktraces for)

    namespaceclasses = {    # Map namespace names to classes each of which has a constructor that can be passed the URL arguments.
        # !SEE-OTHERNAMESPACE add new namespaces here and see other !SEE-OTHERNAMESPACE here and in clients
        "advancedsearch": AdvancedSearch,
        "archiveid": ArchiveItem,
        "doi": DOI,
        "contenthash": ContentHash,
        "sha1hex": Sha1Hex,
        "rawstore": LocalResolverStore,
        "rawfetch": LocalResolverFetch,
        "rawlist": LocalResolverList,
        "rawadd": LocalResolverAdd,
        "btih": BtihResolver,
        "table": KeyValueTable,         # Probably still support under TODO-ARC or make it /table/xxx/...since could be keys or get
    }

    _voidreturn = {'Content-type': 'application/octet-stream', 'data': None}

    # noinspection PyPep8Naming
    @classmethod
    def DwebGatewayHTTPServeForever(cls, httpoptions=None, verbose=False):
        """
        One instance of this will be created for each request, so don't override __init__()
        Initiate with something like: DwebGatewayHTTPRequestHandler.serve_forever()


        :return: Never Returns
        """
        httpoptions = mergeoptions(cls.defaulthttpoptions, httpoptions or {})  # Deepcopy to merge options
        logging.info("Starting server with options={0}".format(httpoptions))
        # any code needed once (not per thread) goes here.
        cls.serve_forever(ipandport=httpoptions["ipandport"], verbose=verbose)  # Uses defaultipandport

    @exposed  # Exposes this function for outside use
    def sandbox(self, foo, bar, **kwargs):
        # Changeable, just for testing HTTP etc, feel free to play with in your branch, and expect it to be overwritten on master branch.
        logging.debug("foo={} bar={}, kwargs={}".format(foo, bar, kwargs))
        return {'Content-type': 'application/json',
                'data': {"FOO": foo, "BAR": bar, "kwargs": kwargs}
                }

    # noinspection PyPep8
    @exposed
    def info(self, **kwargs):  # http://.../info
        """
        Return info about this server
        The content of this may change, make sure to retain the "type" field.

        ConsumedBy:
            "type" consumed by status function TransportHTTP (in Dweb client library)
        Consumes:
        """
        return {'Content-type': 'application/json',
                'data': {"type": "gateway",
                         "services": []}     # A list of names of services supported below  (not currently consumed anywhere)
               }

    @exposed
    def contenthash(self, namespace, *args, **kwargs):
        verbose = kwargs.get("verbose")
        namespaceclass = self.namespaceclasses.get(namespace)
        if namespaceclass:  # Old style e.g. contenthash/rawstore
            return self.namespaceclasses[namespace].new(namespace, *args, **kwargs).contenthash(verbose=verbose)
        else:  # New style e.g. contenthash/Q123 //TODO-ARC complete this and replace cases of above
            # /contenthash/foo => content/contenthash
            return ContentHash.new("contenthash", namespace, *args, **kwargs).content(verbose=verbose, _headers=self.headers)  # { Content-Type: xxx; data: "bytes" }

    @exposed
    def contenturl(self, namespace, *args, **kwargs):
        verbose = kwargs.get("verbose")
        return self.namespaceclasses[namespace].new(namespace, *args, **kwargs).contenturl(verbose=verbose)

    @exposed
    def void(self, namespace, *args, **kwargs):
        self.namespaceclasses[namespace].new(namespace, *args, **kwargs)
        return self._voidreturn

    ###### A group for handling Key Value Stores #########
    @exposed
    def set(self, namespace, *args, verbose=False, **kwargs):
        verbose = kwargs.get("verbose")
        self.namespaceclasses[namespace].new(namespace, *args, verbose=verbose, **kwargs).set(verbose=verbose, **kwargs)
        return self._voidreturn

    @exposed
    def get(self, namespace, *args, verbose=False, **kwargs):
        verbose = kwargs.get("verbose")  # Also passed on to get in kwargs
        return self.namespaceclasses[namespace].new(namespace, *args, verbose=verbose, **kwargs).get(headers=True, verbose=verbose, **kwargs)

    @exposed
    def delete(self, namespace, *args, verbose=False, **kwargs):
        verbose = kwargs.get("verbose")  # Also passed on to get in kwargs
        self.namespaceclasses[namespace].new(namespace, *args, verbose=verbose, **kwargs).delete(headers=True, verbose=verbose, **kwargs)
        return self._voidreturn

    @exposed
    def keys(self, namespace, *args, verbose=False, **kwargs):
        verbose = kwargs.get("verbose")  # Also passed on to get in kwargs
        return self.namespaceclasses[namespace].new(namespace, *args, verbose=verbose, **kwargs).keys(headers=True, verbose=verbose, **kwargs)

    @exposed
    def getall(self, namespace, *args, verbose=False, **kwargs):
        verbose = kwargs.get("verbose")  # Also passed on to get in kwargs
        return self.namespaceclasses[namespace].new(namespace, *args, verbose=verbose, **kwargs).getall(headers=True, verbose=verbose, **kwargs)

    #### A group that breaks the naming convention####
    # urls of form https://dweb.me/archive.org/details/foo, conceptually to be moved to dweb.archive.org/details/foo
    # Its unclear if we use this - normally mapping /arc/archive.org/details ->  bootloader via nginx on dweb.archive.org or dweb.me
    # noinspection PyUnusedLocal
    @exposed
    def archive_org(self, *args, **kwargs):
        filename = config["directories"]["bootloader"]
        # noinspection PyUnusedLocal
        try:
            # if verbose: logging.debug("Opening {0}".format(filename))
            with open(filename, 'rb') as file:
                content = file.read()
            # if verbose: logging.debug("Opened")
        except IOError as e:
            raise TransportFileNotFound(file=filename)
        return {'Content-type': 'text/html', 'data': content}

    @exposed
    def arc(self, arg1, *args, **kwargs):
        """
        Handle a name of the form /arg/archive.org/aaa/bbb
        See page 7 or Mitra's black notebook - not intended as a useful location for docs, but will be copied here !
        /arc/archive.org
        /arc/archive.org/serve => content/archiveid
        /arc/archive.org/download => content/archiveid
        /arc/archive.org/metadata => metadata/archiveid
        /arc/archive.org/advancedsearch => metadata/advancedsearch
        /arc/archive.org/details => html file, but this should be done by nginx

        :param arg1: Must be "archive.org"
        :param args: Remainder of path
        :return:
        """
        verbose = kwargs.get("verbose")
        if arg1 == "archive.org":
            arg2 = args[0]
            args = list(args[1:])
            if (arg2 == "download") or (arg2 == "serve"):
                return ArchiveItem.new("archiveid", *args, **kwargs).content(verbose=verbose, _headers=self.headers)   # { Content-Type: xxx; data: "bytes" }
            if arg2 == "advancedsearch":
                try:
                    return AdvancedSearch.new("advancedsearch", *args, **kwargs).metadata(headers=True, **kwargs)  # { Content-Type: xxx; data: "bytes" }
                except json.decoder.JSONDecodeError:
                    raise SearchException(search=kwargs)
            if arg2 == "leaf":  # This needs to catch the special case of /arc/archive.org/leaf?key=xyz
                args = list(args)
                if kwargs.get("key"):
                    args.append(kwargs["key"])  # Push key into place normally held by itemid in URL of archiveid/xyz
                    del kwargs["key"]
                return ArchiveItem.new("archiveid", *args, **kwargs).leaf(headers=True, **kwargs)    # ERR: ArchiveItemNotFound if invalid id
            if arg2 == "services" and args[0] == "img":
                args.pop(0)
                arg2 = "thumbnail"
            if arg2 in ["torrent", "metadata", "thumbnail"]:
                if arg2 == "torrent":
                    # Need to pass these to new
                    kwargs["transport"] = "WEBTORRENT"
                    kwargs["wanttorrent"] = True
                obj = ArchiveItem.new("archiveid", *args, **kwargs)
                func = getattr(obj, arg2, None)
                return func(headers=True, **kwargs)
            if arg2 == "details" or arg2 == "search":
                raise ToBeImplementedException(name="forwarding to details html for name /arc/%s/%s which should be intercepted by nginx first".format(arg1, '/'.join(args)))
            if arg2 in config["ignoreurls"]:    # Looks like hacking or ignorable e.g. robots.txt, note this just ignores /arc/archive.org/xyz
                raise TransportFileNotFound(file="/arc/{}/{}/{}".format(arg1, arg2, '/'.join(args)))
            raise ToBeImplementedException(name="name /arc/{}/{}/{}".format(arg1, arg2, '/'.join(args)))
        raise ToBeImplementedException(name="name /arc/{}/{}".format(arg1, '/'.join(args)))

    def _namedclass(self, namespace, *args, **kwargs):
        namespaceclass = self.namespaceclasses[namespace]  # e.g. doi=>DOI, sha1hex => Sha1Hex
        output = kwargs.get("output")
        if output and output in ["metadata", "magnetlink", "archiveid", "torrent"]:
            # Supports:
            # btih:zzzz?output=magnetlink - get a Webtorrent magnetlink only currently supported by btih - could (easily) be supported on ArchiveFile, ArchiveItem
            # btih:zzzz?output=archiveid - get the archiveid, only currently supported by btih - could (easily) be supported on ArchiveFile, ArchiveItem
            # btih:zzzz?output=torrent - get a torrentfile, only currently supported by btih - could (easily) be supported on ArchiveFile, ArchiveItem
            obj = namespaceclass.new(namespace, *args, **kwargs)
            func = getattr(obj, output, None)
            if func:
                return func(headers=True, **kwargs)
            else:
                raise ToBeImplementedException(name="{}/{}?{}".format(namespace, "/".join(args), kwargs))
        elif output:
            raise ToBeImplementedException(name="{}/{}?{}".format(namespace, "/".join(args), kwargs))
        else:  # Default to returning content
            return namespaceclass.new(namespace, *args, **kwargs).content(verbose=kwargs.get("verbose"), _headers=self.headers)

    @exposed
    def doi(self, *args, **kwargs):
        return self._namedclass("doi", *args, **kwargs)

    @exposed
    def sha1hex(self, *args, **kwargs):
        return self._namedclass("sha1hex", *args, **kwargs)

    @exposed
    def btih(self, *args, **kwargs):  # /btih/xxxxx or /btih/xxxxx?output=magnetlink
        return self._namedclass("btih", *args, **kwargs)

    # Legacy support ############
    @exposed
    def leaf(self, namespace, *args, **kwargs):
        assert namespace == "archiveid", "Legacy mode only recognizing /leaf/archiveid/foo"
        return self.arc("archive.org", "leaf", *args, **kwargs)

    # Create one of these for each output format, by default parse name and create object, then either
    # call a method on it, or create an output class.
    @exposed
    def metadata(self, namespace, *args, **kwargs):
        if namespace == "archiveid":
            logging.debug("Accessing legacy URL - needs rewriting to use /arc/archive.org/{}/{} {}".format(namespace, '/'.join(args), kwargs))
            return self.arc("archive.org", "metadata", *args, **kwargs)
        if namespace == "advancedsearch":
            logging.debug("Accessing legacy URL - needs rewriting to use /arc/archive.org/{}/{} {}".format(namespace, '/'.join(args), kwargs))
            return self.arc("archive.org", "advancedsearch", *args, **kwargs)
        if namespace not in ["sha1hex", "contenthash", "doi", "rawlist"]:
            logging.debug("Accessing unsupported legacy URL - needs implementing metadata/{}/{} {}".format(namespace, '/'.join(args), kwargs))
            raise ToBeImplementedException(name="metadata/{}/{} {}".format(namespace, '/'.join(args), kwargs))
        # legacy supporting metadata/xxx
        return self.namespaceclasses[namespace].new(namespace, *args, **kwargs).metadata(headers=True, **kwargs)   # { Content-Type: xxx; data: "bytes" }

    @exposed
    def content(self, namespace, *args, **kwargs):
        if namespace == "archiveid":
            logging.debug("Accessing legacy URL - needs rewriting to use /arc/archive.org/{}/{} {}".format(namespace, '/'.join(args), kwargs))
            return self.arc("archive.org", "download", *args, **kwargs)  # TODO-PERMS check what self.arc does with this
        else:
            logging.debug("Accessing unsupported legacy URL - needs implementing content/{}/{} {}".format(namespace, '/'.join(args), kwargs))
            verbose = kwargs.get("verbose")
            return self.namespaceclasses[namespace].new(namespace, *args, **kwargs).content(verbose=verbose, _headers=self.headers)   # { Content-Type: xxx; data: "bytes" }

    @exposed
    def download(self, namespace, *args, **kwargs):
        # Synonym for "content" to match Archive API
        return self.content(namespace, *args, **kwargs)   # Note extra "self" as argument is intentional - needed since content is @exposed

    @exposed
    def thumbnail(self, namespace, *args, **kwargs):
        # Get a thumbnail image - required because https://archive.org/services/img/<itemid> has CORS issues
        if namespace == "archiveid":
            return self.arc("archive.org", "thumbnail", *args, **kwargs)
        raise ToBeImplementedException(name="{}/{}/{}?{}".format("thumbnail", namespace, "/".join(args), kwargs))

    @exposed
    def torrent(self, namespace, *args, **kwargs):
        # Get a thumbnail image - required because https://archive.org/services/img/<itemid> has CORS issues
        if namespace == "archiveid":
            return self.arc("archive.org", "torrent", *args, **kwargs)
        raise ToBeImplementedException(name="{}/{}/{}?{}".format("torrent", namespace, "/".join(args), kwargs))

    # End of Legacy ##########


if __name__ == "__main__":
    logging.basicConfig(**config["logging"])
    DwebGatewayHTTPRequestHandler.DwebGatewayHTTPServeForever({'ipandport': ('0.0.0.0', 4244)}, verbose=True)  # Run local gateway

