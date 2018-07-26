# encoding: utf-8
import json
import logging
from .miscutils import loads, dumps
from .Transport import Transport
from .config import config
import requests # HTTP requests
from .miscutils import httpget
from .Errors import IPFSException


class TransportIPFS(Transport):
    """
    Subclass of Transport.
    Implements the raw primitives via an http API to a local IPFS instance
    Only partially complete
    """

    # urlschemes = ['ipfs'] - subclasses as can handle all
    supportFunctions = ['store','fetch']

    def __init__(self, options=None, verbose=False):
        """
        Create a transport object (use "setup" instead)
        |Exceptions: TransportFileNotFound if dir invalid, IOError other OS error (e.g. cant make directory)

        :param dir:
        :param options:
        """
        self.options = options or {}
        pass

    def __repr__(self):
        return self.__class__.__name__ + " " + dumps(self.options)

    def supports(self, url, func):
        return url.startswith('ipfs:')         # Local can handle any kind of URL, since cached.

    #TODO-LOCAL - feed this back into ServerGateway.info
    def info(self, **options):
        return { "type": "ipfs", "options": self.options }

    def rawfetch(self, url=None, verbose=False, **options):
        """
        Fetch a block from IPFS
        Exception: TransportFileNotFound if file doesnt exist
        #TODO-STREAM make return stream to HTTP and so on

        :param url:
        :param multihash: a Multihash structure
        :param options:
        :return:
        """
        raise ToBeImplementedException(name="TransportIPFS.rawfetch")

    def pinggateway(self, ipldhash):
        """
        Pin to gateway or JS clients wont see it  TODO remove this when client relay working (waiting on IPFS)
        This next line is to get around bug in IPFS propogation
        See https://github.com/ipfs/js-ipfs/issues/1156
        Feb2018: Note this is waiting on a workaround by IPFS (David > Kyle > Lars )
        : param ipldhash    Hash of form z... or Q....  or array of ipldhash
        """
        if isinstance(ipldhash, (list,tuple,set)):
            for i in ipldhash:
                self.pinggateway(i)
        headers = { "Connection": "keep-alive"}
        ipfsgatewayurl = "https://ipfs.io/ipfs/{}".format(ipldhash)
        res = requests.head(ipfsgatewayurl, headers=headers);  # Going to ignore the result
        logging.debug("Transportipfs.pinggateway workaround for JS-IPFS issue #1156 - pin gateway for {}".format(ipfsgatewayurl))

    def announcedht(self, ipldhash):
        """
        Periodically tell URLstore to announce blocks or JS clients wont see it
        This next line is to get around bug in IPFS propogation
        : param ipldhash    Hash of form z... or Q....  or array of ipldhash
        """
        if isinstance(ipldhash, (list,tuple,set)):
            for i in ipldhash:
                self.announcedht(i)
        headers = { "Connection": "keep-alive"}
        ipfsurl = config["ipfs"]["url_dht_provide"]
        res = requests.get(ipfsurl, headers=headers, params={'arg': ipldhash})  # Ignoring result
        logging.debug("Transportipfs.announcedht for {}?arg={}".format(ipfsurl, ipldhash))   # Log whether verbose or not

    def rawstore(self, data=None, verbose=False, returns=None, pinggateway=True, mimetype=None, **options):
        """
        Store the data on IPFS
        Exception: TransportFileNotFound if file doesnt exist

        :param data: opaque data to store (currently must be bytes, not str)
        :param returns: Comma separated string if want result as a dict, support "url","contenthash"
        :raises: IPFSException if cant reach server
        :return: url of data e.g. ipfs:/ipfs/Qm123abc
        """
        assert (not returns), 'Not supporting "returns" parameter to TransportIPFS.store at this point'
        ipfsurl = config["ipfs"]["url_add_data"]
        if verbose: logging.debug("Posting IPFS to {0}".format(ipfsurl))
        headers = { "Connection": "keep-alive"}
        try:
            res = requests.post(ipfsurl, headers=headers, files={'file': ('', data, mimetype)}).json()
        #except ConnectionError as e:  # TODO - for some reason this never catches even though it reports "ConnectionError" as the class
        except requests.exceptions.ConnectionError as e:  # Alternative - too broad a catch but not expecting other errors
            pass
            raise IPFSException(message="Unable to post to local IPFS at {} it is probably not running or wedged".format(ipfsurl))
        logging.debug("IPFS result={}".format(res))
        ipldhash = res['Hash']
        if pinggateway:
            self.pinggateway(ipldhash)
        return "ipfs:/ipfs/{}".format(ipldhash)

    def store(self, data=None, urlfrom=None, verbose=False, mimetype=None, pinggateway=True, returns=None, **options):
        """
        Higher level store semantics

        :param data:
        :param urlfrom:     URL to fetch from for storage, allows optimisation (e.g. pass it a stream) or mapping in transport
        :param verbose:
        :param pinggateway:    True (default) to ping ipfs.io so that it knows where to find, (alternative is to allow browser to ping it on failure to retrieve)
        :param mimetype:
        :param options:
        :raises: IPFSException if cant reach server or doesnt return JSON
        :return:
        """
        assert (not returns), 'Not supporting "returns" parameter to TransportIPFS.store at this point'
        try:
            headers = { "Connection": "keep-alive"}
            if urlfrom and config["ipfs"].get("url_urlstore"):              # On a machine with urlstore and passed a url
                    ipfsurl = config["ipfs"]["url_urlstore"]
                    res = requests.get(ipfsurl, headers=headers, params={'arg': urlfrom}).json()
                    ipldhash = res['Key']
                    # Now pin to gateway or JS clients wont see it  TODO remove this when client relay working (waiting on IPFS)
                    # This next line is to get around bug in IPFS propogation
                    # See https://github.com/ipfs/js-ipfs/issues/1156
                    if pinggateway:
                        self.pinggateway(ipldhash)
                    url = "ipfs:/ipfs/{}".format(ipldhash)
            else:   # Need to store via "add"
                if not data or not mimetype and urlfrom:
                    (data, mimetype) = httpget(urlfrom, wantmime=True) # This is a fetch from somewhere else before putting to gateway
                if not isinstance(data, (str,bytes)):   # We've got data, but if its an object turn into JSON, (example is name/archiveid which passes metadata)
                    data = dumps(data)
                url = self.rawstore(data=data, verbose=verbose, returns=returns, mimetype=mimetype, pinggateway=pinggateway, **options) # IPFSException if down
            return url
        except (json.decoder.JSONDecodeError) as e:
            raise IPFSException(message="Bad format back from IPFS;"+str(e))
        except (requests.exceptions.ConnectionError) as e:
            raise IPFSException(message="IPFS refused connection;"+str(e))

