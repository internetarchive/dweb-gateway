from python.Multihash import Multihash
import logging
from ._utils import _processurl

DOIURL = "metadata/doi/10.1001/jama.2009.1064"
CONTENTMULTIHASH = "5dqpnTaoMSJPpsHna58ZJHcrcJeAjW"
PDF_SHA1HEX="02efe2abec13a309916c6860de5ad8a8a096fe5d"
#CONTENTHASHURL = "content/contenthash/" + CONTENTMULTIHASH # OLD STYLE
CONTENTHASHURL = "contenthash/" + CONTENTMULTIHASH
#SHA1HEXMETADATAURL = "metadata/sha1hex/"+PDF_SHA1HEX # OLD STYLE
#SHA1HEXCONTENTURL = "content/sha1hex/"+PDF_SHA1HEX # OLD STYLE
SHA1HEXCONTENTURL = "sha1hex/" + PDF_SHA1HEX
CONTENTSIZE = 262438
QBF="The Quick Brown Fox"
BASESTRING="A quick brown fox"
SHA1BASESTRING="5drjPwBymU5TC4YNFK5aXXpwpFFbww" # Sha1 of above


logging.basicConfig(level=logging.DEBUG)    # Log to stderr

def test_doi_resolve():
    verbose=False   # True to debug
    res = _processurl(DOIURL, verbose)
    assert res["Content-type"] == "application/json"
    #assert res["data"]["files"][0]["sha1hex"] == PDF_SHA1HEX, "Would check sha1hex, but not returning now do multihash58"
    assert res["data"]["files"][0]["multihash58"] == CONTENTMULTIHASH


def test_contenthash_resolve():
    verbose=False   # True to debug
    res = _processurl(CONTENTHASHURL, verbose)  # Simulate what the server would do with the URL
    assert res["Content-type"] == "application/pdf", "Check retrieved content of expected type"
    assert len(res["data"]) == CONTENTSIZE, "Check retrieved content of expected length"
    multihash = Multihash(data=res["data"], code=Multihash.SHA1)
    assert multihash.multihash58 == CONTENTMULTIHASH, "Check retrieved content has same multihash58_sha1 as we expect"
    assert multihash.sha1hex == PDF_SHA1HEX, "Check retrieved content has same hex sha1 as we expect"

def test_sha1hexcontent_resolve():
    verbose = False  # True to debug
    res = _processurl(SHA1HEXCONTENTURL, verbose)  # Simulate what the server would do with the URL
    assert res["Content-type"] == "application/pdf", "Check retrieved content of expected type"
    assert len(res["data"]) == CONTENTSIZE, "Check retrieved content of expected length"
    multihash = Multihash(data=res["data"], code=Multihash.SHA1)
    assert multihash.multihash58 == CONTENTMULTIHASH, "Check retrieved content has same multihash58_sha1 as we expect"
    assert multihash.sha1hex == PDF_SHA1HEX, "Check retrieved content has same hex sha1 as we expect"

def test_sha1hexmetadata_resolve():
    verbose = False  # True to debug
    res = _processurl("sha1hex/"+PDF_SHA1HEX, verbose, output="metadata")  # Simulate what the server would do with the URL
    if verbose: logging.debug("test_sha1hexmetadata_resolve {0}".format(res))
    assert res["Content-type"] == "application/json", "Check retrieved content of expected type"
    assert res["data"]["metadata"]["size_bytes"] == CONTENTSIZE
    assert res["data"]["metadata"]["multihash58"] == CONTENTMULTIHASH, "Expecting multihash58 of sha1"

