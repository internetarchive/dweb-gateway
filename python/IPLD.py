from .OutputFormat import OutputFormat
from .Multihash import Multihash
from .HashStore import IPLDHashService, IPLDService


class IPLD(OutputFormat):
    pass


class IPLDdir(OutputFormat):
    """
    IPFS compatible Directory of files
    """
    #TODO-IPLD implement building a IPLDdir from a list of files
    pass


class IPLDfile(OutputFormat):
    """
    IPFS compatible file (with Shards)
    """
    #TODO-IPLD implement building a IPLDfile by sharding a file, when have some examples from Kyle

    @classmethod
    def storeFromHash(self, multihash, ipldhash):
        """
        Store a postdata string, store
        Note - you can't do the obvious of parsing json, and then rewriting a sha of that postdata must not change
        :param multihash:   Object this IPLD represents
        :param ipldhash:    String
        :return:
        """
        IPLDHashService.set(multihash, ipldhash)    # Store the multihash for this data so can retrieve by that

    @classmethod
    def storeFromString(cls, multihash58, data):
        """
        Store a postdata string, store
        Note - you can't do the obvious of parsing json, and then rewriting a sha of that postdata must not change
        Also - its IPFS that knows how to match the hashes of the shards against URLs

        :param multihash58:   Object this IPLD represents
        :param data: String
        :return:
        """
        IPLDService.set(multihash58, data)
        cls.storeFromHash(multihash58, Multihash(data=data, code=Multihash.SHA2_256))    # Store the multihash for this data so can retrieve by that
        #TODO-IPFS store in LocationService as being in IPLDService, or add to places searched in contenthash constructor
