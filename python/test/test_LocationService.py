from python.HashStore import HashStore, LocationService

MULTIHASH = "testmultihash"
FIELD = "testfield"
VALUE = "testvalue"


def test_hash_store():
    HashStore.hash_set(MULTIHASH, FIELD, VALUE)
    assert HashStore.hash_get(MULTIHASH, FIELD) == VALUE

def test_location_service():
    LocationService.set(MULTIHASH, VALUE)
    LocationService.get(MULTIHASH)
