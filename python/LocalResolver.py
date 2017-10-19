import logging
from .TransportLocal import TransportLocal
from .NameResolver import NameResolverFile
from .HashStore import LocationService
from .Multihash import Multihash

class LocalResolver(NameResolverFile):
    """
    Subclass of NameResolverFile to resolve hashes locally

    Attributes:
    _contenthash    Multihash of content

    Supports
    contenthash     via NameResolver default
    """

    @staticmethod
    def transport(verbose=False):
        return TransportLocal(options={"local": {"dir": ".cache"}},
                       verbose=verbose)  # TODO-LOCAL move to options at higher level

    @classmethod
    def new(cls, namespace, *args, **kwargs):  # Used by Gateway
        verbose = kwargs.get("verbose")
        if verbose: logging.debug("LocalResolver.new namespace={0} args={1} kwargs={2}".format(namespace, args, kwargs))
        obj = super(LocalResolver, cls).new(namespace, *args, **kwargs)
        if namespace == "rawstore":
            res = cls.transport(verbose=verbose).rawstore(data=kwargs["data"], returns="contenthash,url")
            obj._contenthash = res["contenthash"] # Returned via contenthash() in NameResolveer
            obj.url = res["url"]    #TODO-LOCAL this is going to be wrong its currently local:/rawfetch/Q...
            LocationService.set(obj._contenthash.multihash58, obj.url, verbose=verbose)    # Let LocationService know we have it locally
            return obj
        elif namespace == "rawfetch":
            obj._contenthash = Multihash(multihash58=args[0])
            # Not looking up URL in LocationService yet, will look up if needed
            # Not fetching data, will be retrieved by content() method etc
            obj.url = cls.transport(verbose).url(multihash=obj._contenthash)
            return obj
        else:
            raise ToBeImplementedException(name="TransportLocal.new/{0}".format(namespace))

    @property
    def mimetype(self):
        return "application/octet-stream"   # By default we don't know what it is #TODO-LOCAL look up in MimetypeService just in case ...

    def retrieve(self, verbose=False):
        return self.transport(verbose=verbose).rawfetch(multihash=self._contenthash)
