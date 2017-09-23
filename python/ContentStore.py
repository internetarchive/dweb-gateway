
class ContentStore(HashStore):
Store and retrieve content by its hash.
Could use REDIS or just store in a file -  see rawstore and rawfetch in https://github.com/mitra42/dweb/blob/master/dweb/TransportLocal.py for an example
* rawstore(bytes) => multihash
* rawfetch(multihash) => bytes
* Consumes: multihash; hashstore

Notes: The names are for compatability with a separate client library project.
For now this could use the hashstore or it could use the file system (have code for this)

