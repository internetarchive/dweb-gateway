"""
This is a place to put miscellaneous utilities, not specific to this project
"""
import json # Note dont "from json import dumps" as clashes with overdefined dumps below
from base58 import b58encode
from datetime import datetime
import nacl.encoding
from util_multihash import encode, SHA2_256
from Errors import ToBeImplementedException

#TODO-PYTHON3 - file needs reviewing for Python2/3 compatability

def mergeoptions(a, b):
    """
    Deep merge options dictionaries
     - note this might not (yet) handle Arrays correctly but handles nested dictionaries

    :param a,b: Dictionaries
    :returns: Deep copied merge of the dictionaries
    """
    c = a.copy()
    for key in b:
        val = b[key]
        if isinstance(val, dict) and a.get(key, None):
            c[key] = mergeoptions(a[key], b[key])
        else:
            c[key] = b[key]
    return c

def dumps(obj):    #TODO-BACKPORT FROM GATEWAY TO DWEB - moved from Transport to miscutils
    """
    Convert arbitrary data into a JSON string that can be deterministically hashed or compared.
    Must be valid for loading with json.loads (unless change all calls to that).
    Exception: UnicodeDecodeError if data is binary

    :param data:    Any
    :return: JSON string that can be deterministically hashed or compared
    """
    # ensure_ascii = False was set otherwise if try and read binary content, and embed as "data" in StructuredBlock then complains
    # if it cant convert it to UTF8. (This was an example for the Wrenchicon), but loads couldnt handle return anyway.
    # sort_keys = True so that dict always returned same way so can be hashed
    # separators = (,:) gets the most compact representation
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), default=json_default)


def json_default(obj): #TODO-BACKPORT FROM GATEWAY TO DWEB - moved from Transport to miscutils
    """
    Default JSON serialiser especially for handling datetime, can add handling for other special cases here

    :param obj: Anything json dumps can't serialize
    :return: string for extended types
    """
    if isinstance(obj, (datetime,)):    # Using isinstance rather than hasattr because __getattr__ always returns true
    #if hasattr(obj,"isoformat"):  # Especially for datetime
        return obj.isoformat()
    try:
        return obj.dumps()          # See if the object has its own dumps
    except Exception as e:
        raise TypeError("Type %s not serializable (%s %s)" % (obj.__class__.__name__, e.__class__.__name__, e))

def sha256(data): #TODO-BACKPORT FROM GATEWAY TO DWEB - moved from KeyPair to miscutils
    """
    data:       String or Buffer containing string of arbitrary length
    returns:    32 byte Uint8Array with SHA256 hash
    """
    return nacl.hash.sha256(data, encoder=nacl.encoding.RawEncoder)

def multihashsha256_58(data):    #TODO-BACKPORT FROM GATEWAY TO DWEB - moved from KeyPair to miscutils
    """
    Base58 of a Multihash of a Sha2_256 of data - as used by IPFS

    :param data:    String or binary type
    :return:        string of base58 sha256 hash
    """
    return b58encode(bytes(encode(data, SHA2_256))))

def multihash(sha1=None, sha256=None):
    """
    TODO: convert sha1 or sha256 into multihash (look at "encode" in multihasha256_58 for the last few lines where it builds one from a bytearray.
    """
    raise ToBeImplementedException(name="multihash")


