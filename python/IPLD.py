from .OutputFormat import OutputFormat

class IPLD(OutputFormat):
    pass

class IPLDdir(OutputFormat):
    """
    IPFS compatible Directory of files
    """
    pass

class IPLDfile(OutputFormat):
    """
    IPFS compatible file (with Shards)
    """
    pass
