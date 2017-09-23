# dweb_gateway - Classes
A decentralized web gateway for open academic papers on the Internet Archive

## Important editing notes
* Names might not be consistent below as it gets edited and code built.
* Please edit to match names in the code as you notice conflicts.
* A lot of this file will be moved into actual code as the skeleton gets built, just leaving summaries here.

## Other Info Links

* [Main README](./README.md)
* [Use Cases](./Usecases.md)
* [Classes](./Classes.md)  << You are here
* [Data for the project - sqlite etc](https://archive.org/download/ia_papers_manifest_20170919)
* [Proposal for meta data](./MetaData.md) - first draft.
* [google doc with previous architecture version](https://docs.google.com/document/d/1FO6Tdjz7A1yi4ABcd8vDz4vofRDUOrKapi3sESavIcc/edit#) - #TODO: UseCase from there needs porting here}*
* [google doc with IPFS integration comments](https://docs.google.com/document/d/1kqETK1kmvbdgApCMQEfmajBdHzqiNTB-TSbJDePj0hM/edit#heading=h.roqqzmshx7ww) #TODO: Needs revision ot match this.
* [google doc with top level overview of Dweb project](https://docs.google.com/document/d/1-lI352gV_ma5ObAO02XwwyQHhqbC8GnAaysuxgR2dQo/edit) - best place for links to other resources & docs.
* [gateway.dweb.me](https://gateway.dweb.me) points at the server - which should be running the "deployed" branch. 
* [Gitter chat area](https://gitter.im/ArchiveExperiments/Lobby)
So for example: curl https://gateway.dweb.me/info

## Overview

This gateway sits between a decentralized web server running locally 
(in this case an Go-IPFS server) and the Archive. 
It will expose a set of services to the server. 

The data is stored in a sqlite database that matches DOI's to hashes of the files we know of, 
and the URLs to retrieve them. 

Note its multivalue i.e. a DOI represents an academic paper, which may be present in the archive in 
various forms and formats. (e.g. PDF, Doc; Final; Preprint). 

See [Information flow diagram](./Academic Docs IPFS gateway.pdf)

Especially see main [README](./README.md) and [Use Cases](./UseCases.md)

## Structure high level

Those services will be built from a set of microservices which may or may not be exposed.

All calls to the gateway will come through a server that routes to individual services.

Server URLs have a consistent form 
/outputformat/namespace/namespace-dependent-string

Where:
* outputformat:  Extensible format wanted e.g. [IPLD](#IPLD) or [nameresolution](#nameresolution)
* namespace: is a extensible descripter for name spaces e.g. "doi"
* namespace-dependent-string: is a string, that may contain additional "/" dependent on the namespace.

This is implemented as a pair of steps 
- first the name is passed to a class representing the name space, 
and then the object is passed to a class for the outputformat that can interpret it,
and then a "content" method is called to output something for the client.

See [HTTPServer](httpserver) for how this is processed in an extensible form.

## Microservices

### Summary

* HTTP Server: Routes queries to handlers based on first part of the URL, pretty generic (code done, needs pushing)
* Name Resolvers: A group of classes that recognize names and connect to internal resources
    * NameResolver: Superclass of each Name resolution class
    * NameResolverItem: Superclass to represent a file in a NameResolver
    * NameResolverShard: Superclass to represent a shard of a NameResolverItem
    * DOIResolver: A NameResolver that knows about DOI's
    * DOIResolverFile: A NameResolverItem that knows about files in a DOI
    * ContentHash: A NameResolverItem that knows about hashes of content
* GatewayOutput: A group of classes handling converting data for output
    * IPLD: Superclass for different ways to build IPFS specific IPLDs
    * IPLDfiles: Handles IPLD that contain a list of other files
    * IPLDshards: Handles IPLD that contain a list of shards of a single file
* Storage and Retrieval: A group of classes and services that store in DB or disk.
    * Hashstore: Superclass for a generic hash store to be built on top of REDIS
    * LocationService: A hashstore mapping multihash => location
    * ContentStore: Maps multihash <=> bytes. Might be on disk or REDIS
* Services Misc
    * Multihash58: Convert hashes to base58 multihash, and SHA content.


###<a name="#httpserver"></a> HTTP Server 
Routes queries to handlers based on the first part of the URL for the output format,
and the remainder of the URL for the name.
`GET '/outputformat/namespace/namespace_dependent_string?aaa=bbb,ccc=ddd'`

* outputformat:  Format wanted e.g. [IPLD](#IPLD) or [nameresolution](#nameresolution)
* namespace: is a extensible descripter for name spaces e.g. "doi"
* namespace-dependent-string: is a string, that may contain additional "/" dependent on the namespace.
* aaa=bbb,ccc=ddd are optional arguments to the name space resolver.

##### PseudoCode
* lookup namespace in a config table to get a class
* Call constuctor on that class
    * obj = ConfigTable[namespace](namespace, namespace_dependent_string, aaa=bbb, ccc=ddd)
* And convert to wanted output format.
    * res = OutputTable[]
    * result = obj.outputformat() # Returns object of class GatewayFormat<outputformat>
* Encapsulate result as a dict to return via Server superclass
```
{ Content-type: result.contenttype, data: result.content() }
```

##### Notes
* I'm pretty sure a dict or Array in `data` will be turned into JSON with appropriate Content-type,
and if not then that can be done. 

* Note that the namespace is passed to the specific constuctor since a single name resolver might 
implement multiple namespaces.

* Will need to maintain a table of name's to resolvers which all implement the same interface

##### Future Work
Support streams as the "data" field, and process appropriately.

## Name Resolvers
The NameResolver group of classes manage recognizing a name, and connecting it to resources 
we have at the Archive.

###<a name="nameresolver"></a>NameResolver superclass

The NameResolver class is superclass of each name resolution, 
it specifies a set of methods we expect to be able to do on a subclass,
and may have default code based on assumptions about the data structure of subclasses. 

Logically it can represent one or multiple files.

#####Attributes including:
* subfiles: List of files in this Name Resolver 
* metadata fields for the entire content. 

#####Has methods including:
* NameResolver(namespace, *args, **kwargs)  # Standard footprint of constructor.
* push(NameResolverItem) # Add a item to the shards or subfiles list depending on type
* files() => Iterator    # Iterate over the subfiles, returning NameResolverItem

###<a name="nameresolveritem"></a>NameResolverItem superclass

* Superclass for items in a NameResolver, for example a subclass would be specific PDFs containing 
a DOI.
* It contains enough information to allow for retrieval of the file e.g. HTTP URL, or server and path. Also can have byterange, 
* And meta-data such as date, size
* shardsize:    Attribute specifying the size of shards, default to 250k but we might change that. 

Key method:
* shards()  Return an iterator that returns each of the shards in the file. 
    * Each time called, should:
        * read next `shardsize` bytes from content (either from a specific byterange, or by reading from an open stream)
        * Pass that through multihash58 service to get a base58 multihash
        * Return that multihash, plus metadata (size may be all required)
        * Store the mapping between that multihash, and location (inc byterange) in locationstore
    * May Need to cache the structure, but since the IPLD that calls this will be cached, that might not be needed.

###<a name="nameresolveritem"></a>NameResolverShard superclass

* Superclass for references to Shards in a NameResolverItem
* Returned by the shards() iterator in NameResovlerItem


###<a name="doiresolver"></a>DOI Resolver

Implements name resolution of the DOI namespace, via a sqlite database (provided by Brian)

* URL: `/xxx/doi/10.pub_id/pub_specific_id` (forwarded here by HTTPServer)
* `DOIResolver(self, "doi", pub_id, pub_specific_id, **kwargs)`  
* param: pub_id: ID of publisher as assigned by doi.org - always 10.nnnn
* Param: pub_specific_id: ID assigned by publisher, case insensitive, a-z0-9 and some punc
* Consumes: Sqlite database from Brian *ACTION* need db from Brian
* Consumes: location_store; 
* Consumed by: Name Resolver Service

Resolves a DOI specific name such as 10.nnn/zzzz, 

Brian says: The names are somewhat non-canonical, so first step should be to canonicalize. 
(this will require looking in the sqlite to figure out what are common formats)
Brian says its a long-tail, the vast majority of correct DOI appear to be case insensitive alphanumeric with some allowed punctuation 
(Brian to supply list, or you can analyze the sqlite)

####Pseudo-code

* Canonicalize pub_specific_id (lowercase, strip chars)
* Look up in sqlite to find the [hash, location]* of the file (no need to retrieve it)
* Convert hashes to multihashes
* For each multihash: location_store(multihash, location)
* Build a json with file and metadata in [nameresolution](#nameresolution) format.

#### Later project

* Build way to preload the hashstore with the hashes and URLs from the sqlite

###<a name="doiresolverfile"></a>DOIResolverFile 
* Subclasses NameResolverItem
* Holds meta-data from the sqllite database

###ContentHash
Subclass of NameResolverItem

* ContentHash(namespace, multihash58)
* Param namespace: Should be "multihash"
* Param multihash58: Base58 Multihash of sha1, or sha256 (may support others later)

Looks up the multihash in Location Service to find where can be retrieved from.

## Gateway Outputs
The Gateway Output group of classes manage producing derived content for sending back to requesters.

###GatewayOutput superclass
Superclass of IPLD. Nothing useful defined here currently, but might be! 

Each subclass must implement:
* content():  Return content suitable for returning via the HTTP Server
* contenttype: String suitable for Content-Type HTTP field, e.g. "application/json"

##### Future Work
Support streams as a return content type, both here and in server base class.

###IPLD superlass
Subclass of GatewayOutput; Superclass for IPLDdir and IPLDshards

This is a format specified by IPFS, 
see [IPLD spec](https://github.com/ipld/specs/tree/master/ipld)

Note there are two principal variants of IPLD from our perspective, 
one provides a list of files (like a directory listing), 
the other provides a list of shards, that together create the desired file. 

Note that structurally this is similar, but not identical to the data held in the DOIResolver format. 
There will be a mapping required especially as the IPLD spec is incomplete and subject to new version 
which is overdue and probably (Kyle to confirm) doesn't accurately match how IPLDs exist in current
IPFS code (based on the various variations I see). 

Potential mapping:

* Convert Python dates or ISOStrings into the (undefined) format in IPFS, (its unclear
why a standard like ISO wasn't used by IPFS) See [IPLD#46](https://github.com/ipld/specs/issues/46)
* Possibly replacing links - its unclear in the spec if IPLD wants a string like /ipfs/Q... or just the multhash.
* Possibly removing fields we don't want to expose (e.g. the URL)

Methods:
* multihash58(): returns the hash of the results of content() using the multihash58 service.



###IPLDfiles
Subclass of IPLD where we want to return a directory, or a list of choices 
- for example each of the PDF's & other files available for a specific DOI
* IPLDfiles(NameResolver) *{Expand}* load IPLD with meta-data from NR and iterate through it loading own list.
* content() - *{Expand}* Return internal data structure as a JSON

###IPLDshards
Subclass of IPLD where we want to return a list of subfiles, that are the shards that together
make up the result. 
* IPLDshards(NameResolverItem) *{Expand}* load IPLD with meta-data from NR and iterate through it loading own list.
* content() - *{Expand}* Return internal data structure as a JSON

The constructor is potentially complex.
* Read metadata from NR and store in appropriate format (esp format of RawHash not yet defined)
* Loop through an iterator on the NR which will return shards.
* Write each of them to the IPLDshards' data structure.
* Then write result of content() to the Content_store getting back a multihash (called ipldhash)
* Store ipldhash to location_store with pointer to the Content_store.
* And locationstore_push(contenthash, { ipld: ipldhash }) so that contenthash maps to ipldhash


## Storage and Retrieval
Services for writing and reading to disk or database. 
They are intentionally separated out so that in future the location of storage could change, 
for example metadata could be stored with Archive:item or with WayBack:CDX

Preferably these will be implemented as classes, and interface doc below changed a little.

### Hashstore
Stores and retrieves meta data for hashes, NOTE the hash is NOT the hash of the metadata, and metadata is mutable.
* Not exposed as a URL (can do internally if reqd)
* hash_store(multihash, field, value)    # Replace the data in hash
* hash_push(multihash, field, value)     # Append data to anything already there (use a REDIS RPUSH)
* hash_delete(multihash, field)          # Delete anything stored (probably not required).
* hash_get(multihash, field)             # Return python obj relating to field (list, or string)
* param multihash: Base58 string of self describing hash: e.g. SHA256 is "Qm..." and SHA1 is "5..."
* param field: Field to store data in.

* Consumes: REDIS
* ConsumedBy: *TBC*

The fields allow essentially for independent indexes. 

It should be a simple shim around REDIS, note will have to combine multihash and field to get a redis "key" as if we 
used multihash as the key, and field is one field of a Redis dict type, then we won't be able to "push" to it. 

Note we can assume that this is used in a consistent fashion, e.g. won't do hash_store then hash_push which would be invalid.

### Location Service
Maps hashes to locations
* location_push(multihash, location)
* location_get(multihash) => NameResolverItem
* Consumes: Hashstore
* ConsumedBy: DOI Name Resolver

The multihash represents a file or a part of a file. Build upon hashstore. 
It is split out because this could be a useful service on its own.

### Content Store
Store and retrieve content by its hash.
* rawstore(bytes) => multihash    
* rawfetch(multihash) => bytes 
* Consumes: multihash; hashstore

Notes: The names are for compatability with a separate client library project. 
For now this could use the hashstore or it could use the file system (have code for this)

## Services
Any services not bound to any class, group of classes

### Multihash58
Convert file or hash to multihash in base58

* multihash58(sha256=None, sha1=None, file=None)  
* param file: If present, convert to a sha256  
* param sha1, sha256: Sha's in these formats,  
* returns [multihash](#multihash), a base58 self-describing version of the SHA  

Note Mitra has code that does this.

####Future Work

In the future this is likely to be stored on the metadata of the item. 

## Actions - this will be moved to Issues


### Prior to hackathon

* Mitra ask Brian about non-canonical formats likely to see and canonical form
* Mitra to edit [Academic Documents Archive](https://docs.google.com/document/d/1FO6Tdjz7A1yi4ABcd8vDz4vofRDUOrKapi3sESavIcc/edit#) into here
