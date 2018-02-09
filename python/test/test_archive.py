import logging
from datetime import datetime
from ._utils import _processurl
from python.miscutils import dumps, loads

logging.basicConfig(level=logging.DEBUG)    # Log to stderr

def test_archiveid():
    verbose=True
    if verbose: logging.debug("Starting test_archiveid")
    itemid = "commute"
    btih='XCMYARDAKNWYBERJHUSQR5RJG63JX46B'
    magnetlink='magnet:?xt=urn:btih:XCMYARDAKNWYBERJHUSQR5RJG63JX46B&tr=http%3A%2F%2Fbt1.archive.org%3A6969%2Fannounce&tr=http%3A%2F%2Fbt2.archive.org%3A6969%2Fannounce&tr=wss%3A%2F%2Ftracker.btorrent.xyz&tr=wss%3A%2F%2Ftracker.openwebtorrent.com&tr=wss%3A%2F%2Ftracker.fastcast.nz&ws=https%3A%2F%2Fgateway.dweb.me%2Fdownload%2Farchiveid%2F&xs=https%3A%2F%2Fgateway.dweb.me%2Ftorrent%2Farchiveid%2Fcommute'
    res = _processurl("metadata/archiveid/{}".format(itemid), verbose)  # Simulate what the server would do with the URL
    if verbose: logging.debug("test_archiveid metadata returned {0}".format(res))
    assert res["data"]["metadata"]["identifier"] == itemid
    assert res["data"]["metadata"]["magnetlink"] == magnetlink
    if verbose: logging.debug("test_archiveid complete")
    res = _processurl("magnetlink/btih/{}".format(btih), verbose)
    if verbose: logging.debug("test_archiveid magnetlink returned {0}".format(res))
    assert res["data"] == magnetlink


def test_name():
    verbose=True
    if verbose: logging.debug("Starting test_name")
    # Test it can respond to name requests
    item = "commute"
    nameurl="name/archiveid".format(item)
    res = _processurl(nameurl, verbose=verbose, key=item)  # Simulate what the server would do with the URL
    if verbose: logging.debug("{} returned {}".format(nameurl, res))
