# encoding: utf-8
import logging
from .miscutils import dumps # Use our own version of dumps - more compact and handles datetime etc
from json import loads      # Not our own loads since dumps is JSON compliant
from sys import version as python_version
from cgi import parse_header, parse_multipart
#from Dweb import Dweb      # Import Dweb library (wont use for Academic project
#TODO-API needs writing up
import html
from http import HTTPStatus
from .config import config

"""
This file is intended to be Application independent , i.e. not dependent on Dweb Library
"""

if python_version.startswith('3'):
    from urllib.parse import parse_qs, parse_qsl, urlparse, unquote
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn
else:   # Python 2
    from urlparse import parse_qs, parse_qsl, urlparse        # See https://docs.python.org/2/library/urlparse.html
    from urllib import unquote
    from SocketServer import ThreadingMixIn
    import threading
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
            # See https://docs.python.org/2/library/basehttpserver.html for docs on how servers work
            # also /System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/BaseHTTPServer.py for good error code list

import traceback

from .Errors import MyBaseException, ToBeImplementedException, TransportFileNotFound
#from Transport import TransportBlockNotFound, TransportFileNotFound
#from TransportHTTP import TransportHTTP

class HTTPdispatcherException(MyBaseException):
    httperror = 501     # Unimplemented
    msg = "HTTP request {req} not recognized"

class HTTPargrequiredException(MyBaseException):
    httperror = 400     # UnimplementedAccess
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
    defaultipandport = { "ipandport": ('localhost', 8080) }
    expectedExceptions = () # List any exceptions that you "expect" (and dont want stacktraces for)

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
        logging.info("Server starting on {0}:{1}:{2}".format(cls.ipandport[0], cls.ipandport[1], cls.options or ""))
        ThreadedHTTPServer(cls.ipandport, cls).serve_forever()  # OR Start http server
        logging.error("Server exited") # It never should

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
            logging.info("dispatcher: {0}".format(self.path)) # Always log URLs in
            o = urlparse(self.path)             # Parsed URL {path:"/foo/aaa/bbb", query: "bbb?x=ccc,y=ddd"}

            # Get url args, remove HTTP quote (e.g. %20=' '), ignore leading / and anything before it. Will always be at least one item (empty after /)
            args = [ unquote(u) for u in o.path.split('/')][1:]
            cmd = args.pop(0)                   # foo
            #kwargs = dict(parse_qsl(o.query))  # { baz: bbb, bar: aaa }
            kwargs = {}
            for (k,b) in parse_qsl(o.query):
                a = kwargs.get(k)
                kwargs[k] = b if (a is None) else a+[b] if (isinstance(a,list)) else [a,b]
            if cmd == "":
                cmd = config["httpserver"]["root_path"];
                # Drop through and parse that command
            if cmd == "favicon.ico":    # May general case this for a set of top level links e.g. robots.txt
                self.send_response(301)
                self.send_header('Location',config["httpserver"]["favicon_url"])
                self.end_headers()
            elif cmd in config["ignoreurls"]:  # Looks like hacking or ignorable e.g. robots.txt, note this just ignores /arc/archive.org/xyz
                raise TransportFileNotFound(file=o.path)
            else:
                kwargs.update(postvars)

                cmds = [self.command + "_" + cmd, cmd, self.command + "_" + cmd.replace(".","_"), cmd.replace(".","_")]
                try:
                    func = next(getattr(self, c, None) for c in cmds if getattr(self, c, None))
                except StopIteration:
                    func = None
                #func = getattr(self, self.command + "_" + cmd, None) or getattr(self, cmd, None) # self.POST_foo or self.foo (should be a method)
                if not func or (self.onlyexposed and not func.exposed):
                    raise HTTPdispatcherException(req=cmd)  # Will be caught in except
                res = func(*args, **kwargs)
                # Function should return

                # Send the content-type
                self.send_response(200)  # Send an ok response
                contenttype = res.get("Content-type","application/octet-stream")
                self.send_header('Content-type', contenttype)
                if self.headers.get('Origin'):  # Handle CORS (Cross-Origin)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    # self.send_header('Access-Control-Allow-Origin', self.headers['Origin'])  # '*' didnt work
                data = res.get("data","")
                if data or isinstance(data, (list, tuple, dict)): # Allow empty arrays toreturn as [] or empty dict as {}
                    if isinstance(data, (dict, list, tuple)):    # Turn it into JSON
                        data = dumps(data)        # Does our own version to handle classes like datetime
                    #elif hasattr(data, "dumps"):                # Unclear if this is used except maybe in TransportDist_Peer
                    #    raise ToBeImplementedException(message="Just checking if this is used anywhere, dont think so")
                    #    data = dumps(data)            # And maype this should be data.dumps()
                    if isinstance(data, str):
                        #logging.debug("converting to utf-8")
                        if python_version.startswith('2'): # Python3 should be unicode, need to be careful if convert
                            if contenttype.startswith('text') or contenttype in ('application/json',): # Only convert types we know are strings that could be unicode
                                data = data.encode("utf-8") # Needed to make sure any unicode in data converted to utf8 BUT wont work for intended binary -- its still a string
                        if python_version.startswith('3'):
                            data = bytes(data,"utf-8")  # In Python3 requests wont work on strings, have to convert to bytes explicitly
                    if not isinstance(data, (bytes, str)):
                        #logging.debug(data)
                        # Raise an exception - will not honor the status already sent, but this shouldnt happen as coding
                        # error in the dispatched function if it returns anything else
                        raise ToBeImplementedException(name=self.__class__.__name__+"._dispatch for return data "+data.__class__.__name__)
                self.send_header('content-length', str(len(data)) if data else 0)
                self.end_headers()
                if data:
                    self.wfile.write(data)                   # Write content of result if applicable
                                                            # Thows BrokenPipeError if browser has gone away
            #self.wfile.close()
        except BrokenPipeError as e:
            logging.error("Broken Pipe Error (browser probably gave up waiting) url={}".format(self.path))
            # Don't send error as the browser has gone away
        except Exception as e:         # Gentle errors, entry in log is sufficient (note line is app specific)
            # TypeError Message will be like "sandbox() takes exactly 3 arguments (2 given)" or whatever exception returned by function
            httperror = e.httperror if hasattr(e, "httperror") else 500
            if not (self.expectedExceptions and isinstance(e, self.expectedExceptions)):  # Unexpected error
                logging.error("Sending Unexpected Error {0}:".format(httperror), exc_info=True)
            else:
                logging.info("Sending Error {0}:{1}".format(httperror, str(e)))
            #if self.headers.get('Origin'):  # Handle CORS (Cross-Origin)
                #self.send_header('Access-Control-Allow-Origin', '*')  # '*' didnt work
                # self.send_header('Access-Control-Allow-Origin', self.headers['Origin'])  # '*' didnt work
            self.send_error(httperror, str(e))    # Send an error response


    def do_GET(self):
        #logging.debug(self.headers)
        self._dispatch()

    def do_OPTIONS(self):
        #logging.info("Options request")
        self.send_response(200)
        self.send_header('Access-Control-Allow-Methods', "POST,GET,OPTIONS")
        self.send_header('Access-Control-Allow-Headers', self.headers['Access-Control-Request-Headers'])    # Allow anythihg, but '*' doesnt work
        self.send_header('content-length','0')
        self.send_header('Content-Type','text/plain')
        if self.headers.get('Origin'):
            self.send_header('Access-Control-Allow-Origin', '*')    # '*' didnt work
            # self.send_header('Access-Control-Allow-Origin', self.headers['Origin'])    # '*' didnt work
        self.end_headers()

    def do_POST(self):
        """
        Handle a HTTP POST - reads data in a variety of common formats and passes to _dispatch

        :return:
        """
        try:
            #logging.debug(self.headers)
            ctype, pdict = parse_header(self.headers['content-type'])
            #logging.debug("Contenttype={0}, dict={1}".format(ctype, pdict))
            if ctype == 'multipart/form-data':
                postvars = parse_multipart(self.rfile, pdict)
            elif ctype == 'application/x-www-form-urlencoded':
                # This route is taken by browsers using jquery as no easy wayto uploadwith octet-stream
                # If its just singular like data="foo" then return single values else (unusual) lists
                length = int(self.headers['content-length'])
                postvars = { p: (q[0] if (isinstance(q, list) and len(q)==1) else q) for p,q in parse_qs(
                    self.rfile.read(length),
                    keep_blank_values=1).items() }  # In Python2 this was iteritems, I think items will work in both cases.
            elif ctype in ('application/octet-stream', 'text/plain'):  # Block sends this
                length = int(self.headers['content-length'])
                postvars = {"data": self.rfile.read(length)}
            elif ctype == 'application/json':
                length = int(self.headers['content-length'])
                postvars = {"data": loads(self.rfile.read(length))}
            else:
                postvars = {}
            self._dispatch(**postvars)
        except Exception as e:
        #except ZeroDivisionError as e:  # Uncomment this to actually throw exception (since it wont be caught here)
            # Return error to user, should have been logged already
            httperror = e.httperror if hasattr(e, "httperror") else 500
            self.send_error(httperror, str(e))  # Send an error response

    def send_error(self, code, message=None, explain=None):
        """
        THIS IS A COPY OF superclass's send_error with cors header added
        """
        """Send and log an error reply.

        Arguments are
        * code:    an HTTP error code
                   3 digits
        * message: a simple optional 1 line reason phrase.
                   *( HTAB / SP / VCHAR / %x80-FF )
                   defaults to short entry matching the response code
        * explain: a detailed message defaults to the long entry
                   matching the response code.

        This sends an error response (so it must be called before any
        output has been generated), logs the error, and finally sends
        a piece of HTML explaining the error to the user.

        """

        try:
            shortmsg, longmsg = self.responses[code]
        except KeyError:
            shortmsg, longmsg = '???', '???'
        if message is None:
            message = shortmsg
        if explain is None:
            explain = longmsg
        self.log_error("code %d, message %s", code, message)
        self.send_response(code, message)
        self.send_header('Connection', 'close')

        # Message body is omitted for cases described in:
        #  - RFC7230: 3.3. 1xx, 204(No Content), 304(Not Modified)
        #  - RFC7231: 6.3.6. 205(Reset Content)
        body = None
        if (code >= 200 and
            code not in (HTTPStatus.NO_CONTENT,
                         HTTPStatus.RESET_CONTENT,
                         HTTPStatus.NOT_MODIFIED)):
            # HTML encode to prevent Cross Site Scripting attacks
            # (see bug #1100201)
            content = (self.error_message_format % {
                'code': code,
                'message': html.escape(message, quote=False),
                'explain': html.escape(explain, quote=False)
            })
            body = content.encode('UTF-8', 'replace')
            self.send_header("Content-Type", self.error_content_type)
            self.send_header('Content-Length', int(len(body)))
            self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        if self.command != 'HEAD' and body:
            self.wfile.write(body)


def exposed(func):
    def wrapped(*args, **kwargs):
        result = func(*args, **kwargs)
        return result

    wrapped.exposed = True
    return wrapped
