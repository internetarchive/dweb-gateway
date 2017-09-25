from python import HashStore

MULTIHASH = "testmultihash"
FIELD = "testfield"
VALUE = "testvalue"


def test_hash_store():
    hs = HashStore.HashStore()
    hs.hash_set(MULTIHASH, FIELD, VALUE)
    assert hs.hash_get(MULTIHASH, FIELD) == VALUE

def test_location_service():
    ls = HashStore.LocationService()
    ls.set(MULTIHASH, VALUE)
    ls.get(MULTIHASH)
