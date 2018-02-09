# encoding: utf-8
import logging
#from .Errors import TransportFileNotFound
from .miscutils import loads, dumps
from .Transport import Transport
from .config import config
import requests # HTTP requests
from urllib.parse import quote



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

    def rawstore(self, data=None, verbose=False, returns=None, mimetype=None, **options):
        """
        Store the data on IPFS
        Exception: TransportFileNotFound if file doesnt exist

        :param data: opaque data to store (currently must be bytes, not str)
        :param returns: Comma separated string if want result as a dict, support "url","contenthash"
        :return: url of data e.g. ipfs:/ipfs/Qm123abc
        """
        console.assert (not returns), 'Not supporting "returns" parameter to TransportIPFS.store at this point'
        ipfsurl = config["ipfs"]["url_add_data"]
        if verbose: logging.debug("Posting IPFS to {0}".format(ipfsurl))
        res = requests.post(ipfsurl, files={'file': ('', data, mimetype)}).json()
        logging.debug("IPFS result={}".format(res))
        ipldhash = res['Hash']
        return "ipfs:/ipfs/{}".format(ipldhash)

    def store(self, data=None, urlfrom=None, verbose=False, mimetype=None, returns=None, **options):
        """
        Higher level store semantics

        :param data:
        :param urlfrom:     URL to fetch from for storage, allows optimisation (e.g. pass it a stream) or mapping in transport
        :param verbose:
        :param mimetype:
        :param options:
        :return:
        """
        console.assert (not returns), 'Not supporting "returns" parameter to TransportIPFS.store at this point'
        if urlfrom and config["ipfs"].get("url_urlstore"):              # On a machine with urlstore and passed a url
                ipfsurl = config["ipfs"]["url_urlstore"]
                res = requests.get(ipfsurl, params={'arg': urlfrom}).json() #TODO-URLSTORE ask kyle what this is
                ipldhash = res['Key']
                return "ipfs:/ipfs/{}".format(ipldhash)
        else:   # Need to store via "add"
            if not data or not mimetype:
                (data, mimetype) = httpget(urlfrom, wantmime=True)
            if not isinstance(data, str):   # We've got data, but if its an object turn into JSON, (example is name/archiveid which passes metadata)
                data = dumps(data)
            return this.rawstore(data=data, verbose=verbose, returns=returns, mimetype, **options)

