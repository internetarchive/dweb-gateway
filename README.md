
# dweb-gateway
A decentralized web gateway for open academic papers on the Internet Archive

## Important editing notes
* Names might not be consistent below as it gets edited and code built.
* Please edit to match names in the code as you notice conflicts.
* A lot of this file will be moved into actual code as the skeleton gets built, just leaving summaries here.

## Other Info Links

* [Main README](./README.md) << You are here
* [Use Cases](./Usecases.md)
* [Classes](./Classes.md)
* [HTTP API](./HTTPAPI.md)
* [Extending](./Extending.md)
* [Data for the project - sqlite etc](https://archive.org/download/ia_papers_manifest_20170919)
* [Proposal for meta data](./MetaData.md) - first draft - looks like got deleted :-(
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

See [UseCases](./Usecases.md) and [Classes](./Classes.md) for expansion of this

See [HTTPS API](./HTTPSAPI.md) for the API exposed by the URLs.

## Installation

This should work, someone please confirm on a clean(er) machine and remove this comment.

You'll first need REDIS & Supervisor to be installed
### On a Mac
```bash
brew install redis
brew services start redis
brew install supervisor
```

### On a Linux

Supervisor install details are in: [https://pastebin.com/ctEKvcZt] and [http://supervisord.org/installing.html]
  
Its unclear to me how to install REDIS, its been on every machine I've used.

### Python gateway: 
#### Installation
```bash
# Note it uses the #deployable branch, #master may have more experimental features. 
cd /usr/local   # On our servers its always in /usr/local/dweb-gateway and there may be dependencies on this
git clone http://github.com/internetarchive/dweb-gateway.git

```
Run this complex install script, if it fails then check the configuration at top and rerun. It will:

* Do the pip install (its all python3)
* Updates from the repo#deployable (and pushes back any locally made changes) to #deployed
* Pulls a sqlite file that isn’t actually used any more (it was for academic docs in the first iteration of the gateway)
* Checks the NGINX files map what I expect and (if run as `install.sh NGINX`) copies them over if you have permissions
* Restarts service via supervisorctl, it does NOT setup supervisor 

There are zero guarrantees that changing the config will not cause it to fail! 
```bash
cd dweb-gateway
scripts/install.sh 
```
In addition 
* Check and copy etc_supervisor_conf.d_dweb.conf to /etc/supervisor/conf.d/dweb.conf or server-specific location
* Check and copy etc_ferm_input_nginx to /etc/ferm/input/nginx or server specific location

#### Update
`cd /usr/local/dweb-gateway; scripts/install.sh` 
should update from the repo and restart

#### Restart
`supervisorctl restart dweb:dweb-gateway`

### Gun, Webtorrent Seeder; Webtorrent-tracker
#### Installation
They are all in the dweb-transport repo so ... 
```bash
cd /usr/local # There are probably dependencies on this location
git clone http://github.com/internetarchive/dweb-transport.git
npm install
# Supervisorctl, nginx and ferm should have been setup above.
supervisorctl start dweb:dweb-gun
supervisorctl start dweb:dweb-seeder
supervisorctl start dweb:dweb-tracker
```
#### Update
```bash
cd /usr/local/dweb-transport
git pull
npm update
supervisorctl restart dweb:*
sleep 10    # Give it time to start and not quickly exit
supervisorctl status
```

#### Restart
`supervisorctl restart dweb:*` will restart these, and the python gateway and IPFS 
or restart `dweb:dweb-gun` or `dweb:dweb-seeder` or `dweb:dweb-tracker` individually.

### IPFS
### Installation
Was done by Protocol labs and I’m not 100% sure the full set of things done to setup the repo in a slightly non-standard way,

In particular I know there is a command that have to be run once to enable the ‘urlstore’ functionality

And there may be something needed to enable WebSockets connections (they are enabled in the gateway’s nginx files)

There is a cron task running every 10 minutes that calls one of the scripts and works around a IPFS problem that should be fixed at some point, but not necessarily soon.
```
3,13,23,33,43,53 * * * * python3 /usr/local/dweb-gateway/cron_ipfs.py
```

### Update 
```bash
ipfs update install latest
supervisorctl restart dweb:dweb-ipfs
```
Should work, but there have been issues with IPFS's update process in the past with non-automatic revisions of the IPFS repo. 

### Restart
```
supervisorctl restart dweb:dweb-ipfs
```

### dweb.archive.org UI
```bash
cd /usr/local && git clone http://github.com/internetarchive/dweb-archive.git
cd /usr/local/dweb-archive && npm install
```