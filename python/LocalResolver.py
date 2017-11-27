import logging
from .TransportLocal import TransportLocal
from .NameResolver import NameResolverFile
from .HashStore import LocationService
from .Multihash import Multihash
from .miscutils import loads, dumps

class LocalResolver(NameResolverFile):
    """
    Subclass of NameResolverFile to resolve hashes locally

    Attributes:
    _contenthash    Multihash of content

    Supports
    contenthash     via NameResolver default
    """

    @classmethod
    def new(cls, namespace, *args, **kwargs):  # Used by Gateway
        if kwargs.get("verbose"):
            logging.debug("{0}.new namespace={1} args={2} kwargs={3}"
                                  .format(cls.__name__, namespace, args, kwargs))
        return super(LocalResolver, cls).new(namespace, *args, **kwargs)    # Calls __init__() by default

    @staticmethod
    def transport(verbose=False):
        return TransportLocal(options={"local": {"dir": ".cache"}},
                       verbose=verbose)  # TODO-LOCAL move to options at higher level

class LocalResolverStore(LocalResolver):

    @classmethod
    def new(cls, namespace, *args, **kwargs):  # Used by Gateway
        verbose = kwargs.get("verbose")
        obj = super(LocalResolverStore, cls).new(namespace, *args, **kwargs)    # Calls __init__() by default
        res = cls.transport(verbose=verbose).rawstore(data=kwargs["data"], returns="contenthash,url")
        obj._contenthash = res["contenthash"] # Returned via contenthash() in NameResolveer
        obj.url = res["url"]    #TODO-LOCAL this is going to be wrong its currently local:/rawfetch/Q...
        LocationService.set(obj._contenthash.multihash58, obj.url, verbose=verbose)    # Let LocationService know we have it locally
        return obj



class LocalResolverFetch(LocalResolver):
    @classmethod
    def new(cls, namespace, *args, **kwargs):  # Used by Gateway
        verbose = kwargs.get("verbose")
        obj = super(LocalResolverFetch, cls).new(namespace, *args, **kwargs) # Calls __init__() by default
        obj._contenthash = Multihash(multihash58=args[0])
        # Not looking up URL in LocationService yet, will look up if needed
        # Not fetching data, will be retrieved by content() method etc
        obj.url = cls.transport(verbose).url(multihash=obj._contenthash)
        return obj

    @property
    def mimetype(self):
        return "application/octet-stream"   # By default we don't know what it is #TODO-LOCAL look up in MimetypeService just in case ...

    def retrieve(self, verbose=False):
        return self.transport(verbose=verbose).rawfetch(multihash=self._contenthash)

class LocalResolverAdd(LocalResolver):

    @classmethod
    def new(cls, namespace, url, *args, data=None, **kwargs):  # Used by Gateway
        verbose = kwargs.get("verbose")
        obj = super(LocalResolverAdd, cls).new(namespace, *args, **kwargs)  # Calls __init__() by default
        if isinstance(data, (str, bytes)): # Assume its JSON
            data = loads(data)    # HTTP just delivers bytes
        cls.transport(verbose=verbose).rawadd(url, data)
        return obj

class LocalResolverList(LocalResolver):

    @classmethod
    def new(cls, namespace, hash, *args, data=None, **kwargs):  # Used by Gateway
        verbose = kwargs.get("verbose")
        obj = super(LocalResolverList, cls).new(namespace, hash, *args, **kwargs)  # Calls __init__() by default
        obj._contenthash = Multihash(multihash58=hash)
        return obj

    def metadata(self, verbose=False):
        return { "Content-type": "application/json",
                 "data": self.transport(verbose=verbose).rawlist(self._contenthash.multihash58, verbose=verbose)
               }

