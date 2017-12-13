# encoding: utf-8
from datetime import datetime
import logging

from .miscutils import dumps, loads
from .Errors import ToBeImplementedException, MyBaseException, IntentionallyUnimplementedException

class TransportBlockNotFound(MyBaseException):
    httperror = 404
    msg = "{url} not found"

class TransportURLNotFound(MyBaseException):
    httperror = 404
    msg = "{url}, {options} not found"

class TransportFileNotFound(MyBaseException):
    httperror = 404
    msg = "{file} not found"

class TransportPathNotFound(MyBaseException):
    httperror = 404
    msg = "{path} not found for obj {url}"

class TransportUnrecognizedCommand(MyBaseException):
    httperror = 500
    msg = "Class {classname} doesnt have a command {command}"


class Transport(object):
    """
    Setup the resource and open any P2P connections etc required to be done just once.
    In almost all cases this will call the constructor of the subclass
    Should return a new Promise that resolves to a instance of the subclass

    :param obj transportoptions: Data structure required by underlying transport layer (format determined by that layer)
    :param boolean verbose: True for debugging output
    :param options: Data structure stored on the .options field of the instance returned.
    :resolve Transport: Instance of subclass of Transport
    """

    def __init__(self, options, verbose):
        """
        :param options:
        """
        raise ToBeImplementedException(name=cls.__name__+".__init__")

    @classmethod
    def setup(cls, options, verbose):
        """
        Called to deliver a transport instance of a particular class

        :param options: Options to subclasses init method
        :return: None
        """
        raise ToBeImplementedException(name=cls.__name__+".setup")


    def _lettertoclass(self, abbrev):
        #TODO-BACKPORTING - check if really needed after finish port (was needed on server)
        from letter2class import LetterToClass
        return LetterToClass.get(abbrev, None)

    def supports(self, url): #TODO-API
        """
        Determine if this transport supports a certain set of URLs

        :param url: String or parsed URL
        :return:    True if this protocol supports these URLs
        """
        if not url: return True   # Can handle default URLs
        if isinstance(url, basestring):
            url = urlparse(url)   # For efficiency, only parse once.
        if not url.scheme: raise CodingException(message="url passed with no scheme (part before :): "+url)
        return url.scheme in self.urlschemes  #Lower case, NO trailing : (unlike JS)


    def url(self, data):
        """
         Return an identifier for the data without storing

         :param string|Buffer data   arbitrary data
         :return string              valid id to retrieve data via rawfetch
         """
        raise ToBeImplementedException(name=cls.__name__+".url")

    def info(self, **options):  #TODO-API
        raise ToBeImplementedException(name=cls.__name__+".info")

    def rawstore(self, data=None, verbose=False, **options):
        raise ToBeImplementedException(name=cls.__name__+".rawstore")

    def store(self, command=None, cls=None, url=None, path=None, data=None, verbose=False, **options):
        raise ToBeImplementedException(message="Backporting - unsure if needed - match JS Dweb");  # TODO-BACKPORTING
        #store(command, cls, url, path, data, options) = fetch(cls, url, path, options).command(data|data._data, options)
        #store(url, data)
        if not isinstance(data, basestring):
            data = data._getdata()
        if command:
            # TODO not so sure about this production, document any uses here if there are any
            obj = self.fetch(command=None, cls=None, url=url, path=path, verbose=verbose, **options)
            return obj.command(data=data, verbose=False, **options)
        else:
            return self.rawstore(data=data, verbose=verbose, **options)

    def rawfetch(self, url=None, verbose=False, **options):
        """
        Fetch data from a url and return as a (binary) string

        :param url:
        :param options: { ignorecache if shouldnt use any cached value (mostly in testing);
        :return: str
        """
        raise ToBeImplementedException(name=cls.__name__+".rawfetch")

    def fetch(self, command=None, cls=None, url=None, path=None, verbose=False, **options):
        """
        More comprehensive fetch function, can be sublassed either by the objects being fetched or the transport.
        Exceptions: TransportPathNotFound, TransportUnrecognizedCommand

        :param command: Command to be performed on the retrieved data (e.g. content, or size)
        :param cls:     Class of object being returned, if None will return a str
        :param url:    Hash of object to retrieve
        :param path:    Path within object represented by url
        :param verbose:
        :param options: Passed to command, NOT passed to subcalls as for example mucks up sb.__init__ by dirtying - this might be reconsidered
        :return:
        """
        if verbose: logging.debug("Transport.fetch command={0} cls={1} url={2} path={3} options={4}".format(command, cls, url, path, options))
        #TODO-BACKPORTING see if needed after full port - hint it was used in ServerHTTP but not on client side
        if cls:
            if isinstance(cls, basestring):  # Handle abbreviations for cls
                cls = self._lettertoclass(cls)
            obj = cls(url=url, verbose=verbose).fetch(verbose=verbose)
            # Can't pass **options to cls as disrupt sb.__init__ by causing dirty
            # Not passing **options to fetch, but probably could
        else:
            obj = self.rawfetch(url, verbose=verbose)   # Not passing **options, probably could but not used
        #if verbose: logging.debug("Transport.fetch obj={0}".format(obj))
        if path:
            obj = obj.path(path, verbose=verbose)   # Not passing **options as ignored, but probably could
            #TODO handle not found exception
            if not obj:
                raise TransportPathNotFound(path=path, url=url)
        if not command:
            return obj
        else:
            if not cls:
                raise TransportUnrecognizedCommand(command=command, classname="None")
            func = getattr(obj, command, None)
            if not func:
                raise TransportUnrecognizedCommand(command=command, classname=cls.__name__)
            return func(verbose=verbose, **options)

    def rawadd(self, url, sig, verbose=False, subdir=None, **options):
        raise ToBeImplementedException(name=cls.__name__+".rawadd")

    def add(self, urls=None, date=None, signature=None, signedby=None, verbose=False, obj=None, **options ):
        #TODO-BACKPORTING check if still needed after Backport - not used in JS
        #add(dataurl, sig, date, keyurl)
        if (obj and not url):
            url = obj._url
        return self.rawadd(urls=urls, date=date, signature=signature, signedby=signedby, verbose=verbose, **options)  # TODO would be better to store object

    def rawlist(self, url=None, verbose=False, **options):
        raise ToBeImplementedException(name=cls.__name__+".rawlist")

    def list(self, command=None, cls=None, url=None, path=None, verbose=False, **options):
        """

        :param command: if found:  list.commnd(list(cls, url, path)
        :param cls: if found (cls(l) for l in list(url)
        :param url:    Hash of list to look up - usually url of private key of signer
        :param path:    Ignored for now, unclear how applies
        :param verbose:
        :param options:
        :return:
        """
        raise ToBeImplementedException("Backporting - unsure if needed - match JS Dweb"); #TODO-BACKPORTING

        res = rawlist(url, verbose=verbose, **options)
        if cls:
            if isinstance(cls, basestring): # Handle abbreviations for cls
                cls = self._lettertoclass(cls)
            res = [ cls(l) for l in res ]
        if command:
            func = getattr(CommonList, command, None)   #TODO May not work, might have to turn res into CommonList first
            if not func:
                raise TransportUnrecognizedCommand(command=command, classname=cls.__name__)
            res = func(res, verbose=verbose, **options)
        return res

    def rawreverse(self, url=None, verbose=False, **options):
        raise ToBeImplementedException(name=cls.__name__+".rawreverse")


    def reverse(self, command=None, cls=None, url=None, path=None, verbose=False, **options):
        """

        :param command: if found:  reverse.commnd(list(cls, url, path)
        :param cls: if found (cls(l) for l in reverse(url)
        :param url:    Hash of reverse to look up - usually url of data signed
        :param path:    Ignored for now, unclear how applies
        :param verbose:
        :param options:
        :return:
        """
        raise ToBeImplementedException(message="Backporting - unsure if needed - match JS Dweb"); #TODO-BACKPORTING

        res = rawreverse(url, verbose=verbose, **options)
        if cls:
            if isinstance(cls, basestring): # Handle abbreviations for cls
                cls = self._lettertoclass(cls)
            res = [ cls(l) for l in res ]
        if command:
            func = getattr(self, command, None)
            if not func:
                raise TransportUnrecognizedCommand(command=command, classname=cls.__name__)
            res = func(res, verbose=verbose, **options)
        return res

    #TODO-BACKPORT add listmonitor
