import logging
from datetime import datetime
from ._utils import _processurl
from python.miscutils import dumps, loads

logging.basicConfig(level=logging.DEBUG)    # Log to stderr

def test_archiveid():
    verbose=True
    if verbose: logging.debug("Starting test_archiveid")
    itemid = "commute"
    res = _processurl("metadata/archiveid/{}".format(itemid), verbose)  # Simulate what the server would do with the URL
    if verbose: logging.debug("test_archiveid metadata returned {0}".format(res))
    assert res["data"]["metadata"]["identifier"] == itemid
    if verbose: logging.debug("test_archiveid complete")
