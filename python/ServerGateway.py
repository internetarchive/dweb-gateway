# encoding: utf-8
#from Errors import _print
from .miscutils import mergeoptions
from sys import version as python_version
if python_version.startswith('3'):
    pass
else:
    pass
from .ServerBase import MyHTTPRequestHandler, exposed
from .DOI import DOI
from .ContentHash import ContentHash
from .IPLD import IPLDdir

"""
For documentation on this project see https://docs.google.com/document/d/1FO6Tdjz7A1yi4ABcd8vDz4vofRDUOrKapi3sESavIcc/edit# 
"""

#TODO-PYTHON3 - whole file needsporting to Python2/3 compatability
#TODO-LOG setup generic logger and move all print calls to use it

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
    namespace: is a extensible descripter for name spaces e.g. "doi"
    namespace-dependent-string: is a string, that may contain additional "/" dependent on the namespace.
    aaa=bbb,ccc=ddd are optional arguments to the name space resolver.

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
    *The namespace is passed to the specific constuctor since a single name resolver might implement multiple namespaces.

    Future Work:
    #TODO-STREAM Expand the ServerBase classes to support streams as a return from these routines
    """



    defaulthttpoptions = { "ipandport": ('localhost', 4244) }
    onlyexposed = True          # Only allow calls to @exposed methods
    expectedExceptions = []     # List any exceptions that you "expect" (and dont want stacktraces for)

    namespaceclasses = {    # Map namespace names to classes each of which has a constructor that can be passed the URL arguments.
        "doi": DOI,
        "contenthash": ContentHash,
    }



    @classmethod
    def DwebGatewayHTTPServeForever(cls, httpoptions=None, verbose=False):
        """
        One instance of this will be created for each request, so don't override __init__()
        Initiate with something like: DwebGatewayHTTPRequestHandler.serve_forever()


        :return: Never Returns
        """
        httpoptions = mergeoptions(cls.defaulthttpoptions, httpoptions or {}) # Deepcopy to merge options
        if verbose: print("Starting server with options=", httpoptions)
        #any code needed once (not per thread) goes here.
        cls.serve_forever(ipandport=httpoptions["ipandport"], verbose=verbose)    # Uses defaultipandport

    @exposed    # Exposes this function for outside use
    def sandbox(self, foo, bar, **kwargs):
        # Changeable, just for testing HTTP etc, feel free to play with in your branch, and expect it to be overwritten on master branch.
        print("foo=",foo,"bar=",bar, kwargs)
        return { 'Content-type': 'application/json',
                 'data': { "FOO": foo, "BAR": bar, "kwargs": kwargs}
               }

    @exposed
    def info(self, **kwargs):   # http://.../info
        """
        Return info about this server
        The content of this may change, make sure to retain the "type" field.

        ConsumedBy:
            "type" consumed by status function TransportHTTP (in Dweb client library)
        Consumes:
        """
        return { 'Content-type': 'application/json',
                 'data': { "type": "gateway",
                           "services": [ ]}     # A list of names of services supported below  (not currently consumed anywhere)
               }

    # Create one of these for each output format, by default parse name and create object, then either
    # call a method on it, or create an output class.
    @exposed
    def content(self, namespace, *args, **kwargs):
        verbose = kwargs.get("verbose")
        return self.namespaceclasses[namespace](namespace, *args, **kwargs).content(verbose=verbose)   # { Content-Type: xxx; data: "bytes" }

    @exposed
    def contenthash(self, namespace, *args, **kwargs):
        verbose = kwargs.get("verbose")
        return self.namespaceclasses[namespace](namespace, *args, **kwargs).contenthash(verbose=verbose)

    # Now complex ones where have to create a class to handle conversion e.g. IPLDdirs

    @exposed
    def iplddir(self, namespace, *args, **kwargs):
        obj = self.namespaceclasses[namespace](namespace, *args, **kwargs)
        i = IPLDdir(obj)
        return i.content()

    def POST_storeipld(self, namespace, *args, **kwargs):
        data = kwargs["data"]
        del kwargs["data"]
        obj = self.namespaceclasses[namespace](namespace, *args, **kwargs)
        #TODO-XXXX Mitra has got to here.

if __name__ == "__main__":
    DwebGatewayHTTPRequestHandler.DwebGatewayHTTPServeForever({'ipandport': ('localhost',4244)}) # Run local gateway

