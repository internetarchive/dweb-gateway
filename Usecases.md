# dweb-gateway - Use Cases
A decentralized web gateway for open academic papers on the Internet Archive

An outline of Use Cases for the gateway

## Important editing notes
* Names might not be consistent below as it gets edited and code built.
* Please edit to match names in the code as you notice conflicts.

## Other Info Links

* [Main README](./README.md)
* [Use Cases](./Usecases.md) << You are here
* [Classes](./Classes.md)
* [Data for the project - sqlite etc](https://archive.org/download/ia_papers_manifest_20170919)
* [Proposal for meta data](./MetaData.md) - first draft - deleted needs recreating
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

Note the data is multivalue i.e. a DOI represents an academic paper, which may be present in the archive in 
various forms and formats. (e.g. PDF, Doc; Final; Preprint). 

See [Information flow diagram](./Academic Docs IPFS gateway.pdf)

Please see the main [README](./README.md) for the overall structure and [Classes](./Classes.md) for the class overview.

## Use Case examples

### Retrieving a document starting with DOI


-#TODO: Copy the use case from [google doc with previous architecture version](https://docs.google.com/document/d/1FO6Tdjz7A1yi4ABcd8vDz4vofRDUOrKapi3sESavIcc/edit#)
with edits to match current names etc in Microservices below. Below is draft

##### Retrieval of file by content hash
* IPFS Gateway
    * Receives a request by contenthash
    * Requests GET //gateway.dweb.me/ipldfile/contenthash/Qm.....
* Gateway Server/Service gateway.dweb.doi
    * Calls ContentHash(Qm...)
* ContentHash(Qm...)  
    * (ContentHash is subclass of NameResolverFile)
    * Locates file in the sqlite 
    * Loads meta-data for that file
* Gateway Server
    * Passes ContentHash object to ipldfile(CH)
    * IPLDfile calls CH.shards() as an iterator on CH to read each shard
* ContentHash.shards()
    * Is an iterator that iterates over shards (or chunks) of the file. For each shard:
    * It reads a chunk of bytes from the file (using a byterange in a HTTP call)
    * It hashes those bytes
    * Stores the hash and the URL + Byterange in the location service
    * Returns the metadata & hash to IPLDfile
* IPLDfile 
    * Comines the return into the IPLD variant for shards, 
    * and adds metadata, especially the contenthash 
    * returns to NameServer
* Gateway Server > IPFS > client
    * Calls IPLDfile.content() to get the ipld file to return to IPFS Gateway
* IPFS Gateway
    * Pins the hash of the IPLD and each of the shards, and returns to client

##### File retrieval
* iPFS Client
    * Having retrieved the IPLDfile, iterates over the shards
    * For each shard it tries to retrieve the hash
* IPFS Gateway node
    * Recognizes the shard, and calls gateway.dweb.me/content/multihash/Q...
* Gateway server
    * Routes to multihash("multihash", Q...)
* Multihash("multihash", Q...)
    * Looks up the multihash in the location service
    * Disovers the location is a URL + Byterange
* Gateway server 
    * Calls content method on multihash
* Multihash.content()
    * Retrieves the bytes (from elsewhere in Archive) and returns to Gateway Server
* Gateway Server > IPFS Gateway > Client
