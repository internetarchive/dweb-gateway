import logging
from datetime import datetime
from ._utils import _processurl
from python.miscutils import dumps, loads
from python.Archive import ArchiveItemNotFound
from python.config import config

logging.basicConfig(level=logging.DEBUG)    # Log to stderr

def test_archiveid():
    verbose=False
    if verbose: logging.debug("Starting test_archiveid")
    itemid = "commute"
    btih='XCMYARDAKNWYBERJHUSQR5RJG63JX46B'
    magnetlink='magnet:?xt=urn:btih:XCMYARDAKNWYBERJHUSQR5RJG63JX46B&tr=http%3A%2F%2Fbt1.archive.org%3A6969%2Fannounce&tr=http%3A%2F%2Fbt2.archive.org%3A6969%2Fannounce&tr=wss%3A%2F%2Ftracker.btorrent.xyz&tr=wss%3A%2F%2Ftracker.openwebtorrent.com&tr=wss%3A%2F%2Ftracker.fastcast.nz&ws=https%3A%2F%2Fgateway.dweb.me%2Fdownload%2Farchiveid%2F&xs=https%3A%2F%2Fgateway.dweb.me%2Ftorrent%2Farchiveid%2Fcommute'
    #res = _processurl("metadata/archiveid/{}".format(itemid), verbose)  # Simulate what the server would do with the URL
    res = _processurl("arc/archive.org/metadata/{}".format(itemid), verbose)  # Simulate what the server would do with the URL

    if verbose: logging.debug("test_archiveid metadata returned {0}".format(res))
    assert res["data"]["metadata"]["identifier"] == itemid
    assert res["data"]["metadata"]["magnetlink"] == magnetlink
    assert "ipfs:/ipfs" in res["data"]["metadata"]["thumbnaillinks"][0]
    assert itemid in res["data"]["metadata"]["thumbnaillinks"][1]
    if verbose: logging.debug("test_archiveid complete")
    res = _processurl("magnetlink/btih/{}".format(btih), verbose)
    if verbose: logging.debug("test_archiveid magnetlink returned {0}".format(res))
    assert res["data"] == magnetlink

def test_collectionsortorder():
    verbose=True
    itemid="prelinger"
    #collectionurl = "metadata/archiveid/{}"   # OLD FORM
    collectionurl = "arc/archive.org/metadata/{}"
    res = _processurl(collectionurl.format(itemid), verbose) # Simulate what the server would do with the URL
    assert res["data"]["collection_sort_order"] == "-downloads"

def test_leaf():
    verbose=False
    if verbose: logging.debug("Starting test_leaf")
    # Test it can respond to leaf requests
    item = "commute"
    # leafurl="leaf/archiveid" OLD FORM
    leafurl="arc/archive.org/leaf"
    res = _processurl(leafurl, verbose=verbose, key=item)  # Simulate what the server would do with the URL
    if verbose: logging.debug("{} returned {}".format(leafurl, res))
    leafurl="get/table/{}/domain".format(config["domains"]["metadata"])  #TODO-ARC
    res = _processurl(leafurl, verbose=verbose, key=item) # Should get value cached above
    if verbose: logging.debug("{} returned {}".format(leafurl, res))

def test_archiveerrs():
    verbose=True
    if verbose: logging.debug("Starting test_archiveid")
    itemid = "nosuchitematall"
    try:
        #res = _processurl("metadata/archiveid/{}".format(itemid), verbose)  # Simulate what the server would do with the URL
        res = _processurl("arc/archive.org/metadata/{}".format(itemid), verbose)  # Simulate what the server would do with the URL
    except ArchiveItemNotFound as e:
        pass    # Expecting an error

def test_search():
    verbose=True
    kwargs1={    # Taken from example home page
        'output': "json",
        'q': "mediatype:collection AND NOT noindex:true AND NOT collection:web AND NOT identifier:fav-* AND NOT identifier:what_cd AND NOT identifier:cd AND NOT identifier:vinyl AND NOT identifier:librarygenesis AND NOT identifier:bibalex AND NOT identifier:movies AND NOT identifier:audio AND NOT identifier:texts AND NOT identifier:software AND NOT identifier:image AND NOT identifier:data AND NOT identifier:web AND NOT identifier:additional_collections AND NOT identifier:animationandcartoons AND NOT identifier:artsandmusicvideos AND NOT identifier:audio_bookspoetry AND NOT identifier:audio_foreign AND NOT identifier:audio_music AND NOT identifier:audio_news AND NOT identifier:audio_podcast AND NOT identifier:audio_religion AND NOT identifier:audio_tech AND NOT identifier:computersandtechvideos AND NOT identifier:coverartarchive AND NOT identifier:culturalandacademicfilms AND NOT identifier:ephemera AND NOT identifier:gamevideos AND NOT identifier:inlibrary AND NOT identifier:moviesandfilms AND NOT identifier:newsandpublicaffairs AND NOT identifier:ourmedia AND NOT identifier:radioprograms AND NOT identifier:samples_only AND NOT identifier:spiritualityandreligion AND NOT identifier:stream_only AND NOT identifier:television AND NOT identifier:test_collection AND NOT identifier:usgovfilms AND NOT identifier:vlogs AND NOT identifier:youth_media",
        'rows': "75",
        'sort[]': "-downloads",
        'and[]':  ""
    }
    kwargs2={   # Take from example search
        'output': "json",
        'q': "prelinger",
        'rows': "75",
        'sort[]': "",
        'and[]': ""
    }
    #res = _processurl("metadata/advancedsearch", verbose, **kwargs2)  # Simulate what the server would do with the URL
    res = _processurl("arc/archive.org/advancedsearch", verbose, **kwargs2)  # Simulate what the server would do with the URL
    #logging.debug("XXX@65")
    logging.debug(res)
