# dweb_gateway
A decentralized web gateway for open academic papers on the Internet Archive

## Important editing notes
* Names might not be consistent below as it gets edited and code built.
* Please edit to match names in the code as you notice conflicts.
* A lot of this file will be moved into actual code as the skeleton gets built, just leaving summaries here.

## Other Info Links

* [Main README](./README.md) << You are here
* [Use Cases](./Usecases.md)
* [Classes](./Classes.md)
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

See [UseCases](./Usecases.md) amd [Classes](./Classes.md) for expansion of this

## Installation

This should work, someone please confirm on a clean(er) machine and remove this comment.
```
git clone http://github.com/ArchiveLabs/dweb_gateway.cid
cd dweb_gateway
pip install --disable-pip-version-check -u base58 pynacl
python -m python.ServerGateway
curl http://localhost:4244/info
curl http://localhost:4244/contenthash/doi/10.1234/abcdef
```