# encoding: utf-8
from miscutils import dumps # Use our own version of dumps - more compact and handles datetime etc
from json import loads      # Not our own loads since dumps is JSON compliant
from sys import version as python_version
from cgi import parse_header, parse_multipart
import urllib
import BaseHTTPServer       # See https://docs.python.org/2/library/basehttpserver.html for docs on how servers work
                            # also /System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/BaseHTTPServer.py for good error code list
#from Dweb import Dweb      # Import Dweb library (wont use for Academic project
#TODO-API needs writing up

"""
This file is intended to be Application independent , i.e. not dependent on Dweb Library
"""
#TODO-PYTHON3 - this file needs review for Python2/3 compatability

#TODO-HTTPSERVER - this needs modifying to match the two-stage server process in the README.MD

if python_version.startswith('3'):
    from urllib.parse import parse_qs, parse_qs, urlparse
    from http.server import BaseHTTPRequestHandler
else:   # Python 2
    from urlparse import parse_qs, parse_qsl, urlparse        # See https://docs.python.org/2/library/urlparse.html
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from SocketServer import ThreadingMixIn
    import threading

import traceback

from Errors import MyBaseException, ToBeImplementedException
#from Transport import TransportBlockNotFound, TransportFileNotFound
#from TransportHTTP import TransportHTTP

class HTTPdispatcherException(MyBaseException):
    httperror = 501     # Unimplemented
    msg = "HTTP request {req} not recognized"

class HTTPargrequiredException(MyBaseException):
    httperror = 400     # Unimplemented
    msg = "HTTP request {req} requires {arg}"

class DWEBMalformedURLException(MyBaseException):
    httperror = 400
    msg = "Malformed URL {path}"

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

class MyHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    Generic HTTPRequestHandler, extends BaseHTTPRequestHandler, to make it easier to use
    """
    # Carefull - do not define __init__ as it is run for each incoming request.
    # TODO-STREAMS add support for longer (streamed) files on both upload and download, allow a stream to be passed back from the subclasses routines.

    """
    Simple (standard) HTTPdispatcher,
    Subclasses should define "exposed" as a list of exposed methods
    """
    exposed = []
    protocol_version = "HTTP/1.1"
    onlyexposed = False  # Dont Limit to @exposed functions (override in subclass if using @exposed)
    defaultipandport = { "ipandport": (u'localhost', 8080) }
    expectedExceptions = [] # List any exceptions that you "expect" (and dont want stacktraces for)

    @classmethod
    def serve_forever(cls, ipandport=None, verbose=False, **options):
        """
        Start a server,
        ERR: socket.error if address(port) in use.

        :param ipandport: Ip and port to listen on, else use defaultipandport
        :param verbose: If want debugging
        :param options: Stored on class for access by handlers
        :return: Never returns
        """
        cls.ipandport = ipandport or cls.defaultipandport
        cls.verbose = verbose
        cls.options = options
        #HTTPServer(cls.ipandport, cls).serve_forever()  # Start http server
        ThreadedHTTPServer(cls.ipandport, cls).serve_forever()  # OR Start http server
        print("Server exited") # It never should

    def _dispatch(self, **postvars):
        """
        HTTP dispatcher (replaced a more complex version Sept 2017
        URLS of form GET /foo/bar/baz?a=b,c=d
        Are passed to foo(bar,baz,a=b,c=d) which mirrors Python argument conventions i.e.  if def foo(bar,baz,**kwargs) then foo(aaa,bbb) == foo(baz=bbb, bar=aaa)
        POST will pass a dictionary, if its just a body text or json it will be passed with a single value { date: content data }
        In case of conflict, postvars overwrite args in the query string, but you shouldn't be getting both in most cases.

        :param vars:
        :return:
        """
        # In documentation, assuming call with /foo/aaa/bbb?x=ccc,y=ddd
        try:
            httpverbose=True
            if httpverbose: print("dispatcher",self.path)
            o = urlparse(self.path)             # Parsed URL {path:"/foo/aaa/bbb", query: "bbb?x=ccc,y=ddd"}

            # Get url args, remove HTTP quote (e.g. %20=' '), ignore leading / and anything before it. Will always be at least one item (empty after /)
            args = [ urllib.unquote(u) for u in o.path.split('/')][1:]
            cmd = args.pop(0)                   # foo
            kwargs = dict(parse_qsl(o.query))  # { baz: bbb, bar: aaa }
            kwargs.update(postvars)
            func = getattr(self, cmd, None) # self.foo (should be a method)
            if not func or (self.onlyexposed and not func.exposed):
                raise HTTPdispatcherException(req=cmd)  # Will be caught in except
            res = func(*args, **kwargs)
            # Function should return

            # Send the content-type
            self.send_response(200)  # Send an ok response
            self.send_header('Content-type', res.get("Content-type","application/octet-stream"))
            if self.headers.get('Origin'):  # Handle CORS (Cross-Origin)
                self.send_header('Access-Control-Allow-Origin', self.headers['Origin'])  # '*' didnt work
            data = res.get("data","")
            print "XXX@dispatch118",len(data)
            if data or isinstance(data, (list, tuple)): # Allow empty arrays toreturn as []
                if isinstance(data, (dict, list, tuple)):    # Turn it into JSON
                    data = dumps(data)        # Does our own version to handle classes like datetime
                #elif hasattr(data, "dumps"):                # Unclear if this is used except maybe in TransportDist_Peer
                #    raise ToBeImplementedException(message="Just checking if this is used anywhere, dont think so")
                #    data = dumps(data)            # And maype this should be data.dumps()
                if not isinstance(data, basestring):
                    print(data)
                    # Raise an exception - will not honor the status already sent, but this shouldnt happen as coding
                    # error in the dispatched function if it returns anything else
                    raise ToBeImplementedException(name=self.__class__.__name__+"._dispatch for return data "+data.__class__.__name__)
                if isinstance(data, unicode):
                    print "XXX converting to unicode"
                    data = data.encode("utf-8") # Needed to make sure any unicode in data converted to utf8 BUT wont work for intended binary
            self.send_header('content-length', str(len(data)) if data else 0)
            self.end_headers()
            print "XXX@dispatch134",len(data)
            if data:
                self.wfile.write(data)                   # Write content of result if applicable
            #self.wfile.close()

        except Exception as e:         # Gentle errors, entry in log is sufficient (note line is app specific)
            # TypeError Message will be like "sandbox() takes exactly 3 arguments (2 given)" or whatever exception returned by function
            httperror = e.httperror if hasattr(e, "httperror") else 500
            if not (self.expectedExceptions and isinstance(e, self.expectedExceptions)):  # Unexpected error
                traceback.print_exc(limit=None)  # unfortunately only prints to try above so may need to raise?
            print("Sending error",httperror,str(e))
            self.send_error(httperror, str(e))    # Send an error response


    def do_GET(self):
        #print "XXX@do_GET:145";
        self._dispatch()

    def do_OPTIONS(self):
        print("Options request")
        self.send_response(200)
        self.send_header('Access-Control-Allow-Methods', "POST,GET,OPTIONS")
        self.send_header('Access-Control-Allow-Headers', self.headers['Access-Control-Request-Headers'])    # Allow anythihg, but '*' doesnt work
        self.send_header('content-length','0')
        self.send_header('Content-Type','text/plain')
        if self.headers.get('Origin'):
            self.send_header('Access-Control-Allow-Origin', self.headers['Origin'])    # '*' didnt work
        self.end_headers()

    def do_POST(self):
        """
        Handle a HTTP POST - reads data in a variety of common formats and passes to _dispatch

        :return:
        """
        try:
            verbose = True
            if verbose: print(self.headers)
            ctype, pdict = parse_header(self.headers['content-type'])
            if verbose: print(ctype, pdict)
            if ctype == 'multipart/form-data':
                postvars = parse_multipart(self.rfile, pdict)
            elif ctype == 'application/x-www-form-urlencoded':
                # This route is taken by browsers using jquery as no easy wayto uploadwith octet-stream
                # If its just singular like data="foo" then return single values else (unusual) lists
                length = int(self.headers['content-length'])
                postvars = { p: (q[0] if (isinstance(q, list) and len(q)==1) else q) for p,q in parse_qs(
                    self.rfile.read(length),
                    keep_blank_values=1).iteritems() }
            elif ctype in ('application/octet-stream', 'text/plain'):  # Block sends this
                length = int(self.headers['content-length'])
                postvars = {"data": self.rfile.read(length)}
            elif ctype == 'application/json':
                length = int(self.headers['content-length'])
                postvars = {"data": loads(self.rfile.read(length))}
            else:
                postvars = {}
            self._dispatch(**postvars)
        #except Exception as e:
        except ZeroDivisionError as e:  # Uncomment this to actually throw exception
            httperror = e.httperror if hasattr(e, "httperror") else 500
            self.send_error(httperror, str(e))  # Send an error response


def exposed(func):
    def wrapped(*args, **kwargs):
        result = func(*args, **kwargs)
        return result

    wrapped.exposed = True
    return wrapped
