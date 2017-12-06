# DWEB HTTPS API

This doc describes the API exposed by the Internet Archive's DWEB server.

Note this server is experimental, it could change without notice. 
Before using it for anything critical please contact mitra@archive.org.

## Overview

The URLs have a consistent structure, except for a few odd cases. See ____ 
```
https://dweb.me/outputtype/itemtype/itempath
```
Where:

* dweb.me is the HTTPS server. Any other server running this code should give the same output.
* outputtype: is the type of result requested e.g. metadata or content
* itemtype: is the kind of item being inquired about e.g. doi, contenthash

The outputtype and itemtype are in most cases orthogonal, i.e. any outputtype SHOULD work with any itemtype. 
In practice some combinations don't make any sense. 

## Output Types

* content: Return the file itself
* contenthash: Return the hash of the content, suitable for a contenthash/xyz request
* contenturl: Return a URL that could be used to retrieve the content  
* metadata: Return a JSON with metadata about the file
* void: Return emptiness

### Not yet working, but reserved for future development
* iplddir: Return an IPFS data structure for the files (not yet working)
* ipldstore: Store the IPLD provided in the Post data (Not currently used, and possibly should be an item type)
* storeipldhash: Save a hash that could be used in IPFS to retrieve the IPLD (dont believe its used)
 
## Item Types

* contenthash: The hash of a content, in base58 multihash form typically Q123abc or z123abc depending on which hash is used,
  it returns files from the Archive.org and will be expanded to cover more collections over time.
* doi: Document Object Identifier e.g. 10.1234/abc-def. The standard identifier of Academic papers.
* sha1hex: Sha1 expressed as a hex string e.g. a1b2c3
* rawstore: The data - provided with a POST is to be stored
* rawfetch: Equivalent to contenthash except only retrieves from a local data store (so is faster)
* rawadd: Adds a JSON data structure to a named list e.g. rawadd/Q123
* rawlist: Returns an array of data structures added to a list with rawadd

(Note this set is mapped in ServerGateway.py to the classes that serve them)


## Odd cases

* info - returns a JSON describing the server - format will change except that always contains { type: "gateway" }
