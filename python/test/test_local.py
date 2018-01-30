import logging
from datetime import datetime
from ._utils import _processurl
from python.miscutils import dumps, loads

logging.basicConfig(level=logging.DEBUG)    # Log to stderr

CONTENTMULTIHASH = "5dqpnTaoMSJPpsHna58ZJHcrcJeAjW"
BASESTRING="A quick brown fox"
SHA1BASESTRING="5drjPwBymU5TC4YNFK5aXXpwpFFbww" # Sha1 of above


def test_local():
    verbose=True
    res = _processurl("contenthash/rawstore", verbose, data=BASESTRING.encode('utf-8'))  # Simulate what the server would do with the URL
    if verbose: logging.debug("test_local store returned {0}".format(res))
    contenthash = res["data"]
    res = _processurl("content/rawfetch/{0}".format(contenthash), verbose)  # Simulate what the server would do with the URL
    if verbose: logging.debug("test_local content/rawfetch/{0} returned {1}".format(contenthash, res))
    assert res["data"].decode('utf-8') == BASESTRING
    res = _processurl("content/contenthash/{0}".format(contenthash), verbose)  # Simulate what the server would do with the URL
    if verbose: logging.debug("test_local content/contenthash/{0} returned {1}".format(contenthash, res))

def test_list():
    verbose = True
    date =  datetime.utcnow().isoformat()
    adddict = { "urls": [ CONTENTMULTIHASH ], "date": date, "signature": "XXYYYZZZ", "signedby": [ SHA1BASESTRING ], "verbose": verbose }
    res = _processurl("void/rawadd/"+SHA1BASESTRING, verbose, data=dumps(adddict))
    if verbose: logging.debug("test_list {0}".format(res))
    res = _processurl("metadata/rawlist/{0}".format(SHA1BASESTRING), verbose, data=dumps(adddict))
    if verbose: logging.debug("rawlist returned {0}".format(res))
    assert res["data"][-1]["date"] == date

def test_keyvaluetable():
    verbose=True
    database = "Q123456789"
    table = "mytesttable"
    res = _processurl("set/table/{}/{}".format(database, table), data=dumps([{"key": "aaa", "value": "AAA"}, {"key": "bbb", "value": "BBB"}]), verbose=verbose)
    res = _processurl("get/table/{}/{}".format(database, table), key="aaa", verbose=verbose)
    assert res["data"]["aaa"] == "AAA"
    res = _processurl("get/table/{}/{}".format(database, table), key=["aaa","bbb"], verbose=verbose)
    assert res["data"]["aaa"] == "AAA" and res["data"]["bbb"] == "BBB"
    res = _processurl("delete/table/{}/{}".format(database, table), key="aaa", verbose=verbose)
    res = _processurl("get/table/{}/{}".format(database, table), key="aaa", verbose=verbose)
    assert res["data"]["aaa"] is None
    res = _processurl("keys/table/{}/{}".format(database, table), verbose=verbose)
    assert len(res["data"]) == 2
    res = _processurl("getall/table/{}/{}".format(database, table), verbose=verbose)
    assert res["data"]["aaa"] is None and res["data"]["bbb"] == "BBB"
