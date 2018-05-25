# NGINX configuration

These files are to support tracking changes to nginx,

For now just being tracked manually, i.e. editing here wont change anything but can add any changes back to git by ...
```bash
cd /usr/local/dweb-gateway/nginx 
cp /etc/nginx/sites-enabled/* .
git commit -a
git push 
```

TODO - this could use some support in the install scripts etc, 


## SUMMARY
* https://dweb.me (secure server) proxypass http://dweb.me (research server)
* http://dweb.me/ -> https://dweb.me/
* http://dweb.archive.org/aaa/xxx -> gateway /arc/archive.org/aaa/xxx
* https://{gateway.dweb.me, dweb.me}/ -> https://dweb.archive.org  - exact URL only
* https://{gateway.dweb.me, dweb.me}/ proxypass localhost:4244 (gateway python)
* https://{gateway.dweb.me, dweb.me, dweb.archive.org}/examples -> file
* http://dweb.archive.org/{details,search} -> bootloader
* https://{gateway.dweb.me, dweb.me}/arc/archive.org/{details,search} -> bootloader
* https://{dweb.me, gateway.dweb.me, dweb.archive.org}/{ws,wss} proxypass localhost:4002 (websockets for IPFS) - not yet working
##

The main differences between the different domains are ... 

* dweb.archive.org answers on http, because its the end-point of a proxypass from https://dweb.archive.org (another machine)
* dweb.me forces http by redirecting to https
* gateway.dweb.me provides access to the python server for any URL at http://gateway.dweb.me:80 
* dweb.me and gateway.dweb.me forward exact root URL to '/' to https://dweb.archive.org/
* dweb.archive.org forwards /{details, search}; dweb.me & gateway.dweb.me forward /arc/archive.org/{details,search} to bootstrap.html


## URLS of interest
dweb.archive.org|dweb.me or gateway.dweb.me|Action
----------------|--------------------------|------
/|/|Archive home page via bootloader
/search?q=xyz|/arc/archive.org/search/q=xyz|search page via bootloader
/details/foo|/arc/archive.org/details/foo|details page via bootloader
/ipfs/Q1234|/ipfs/Q1234|IPFS result
/metadata/foo|/arc/archive.org/metadata/foo|cache and return metadata JSON
/leaf/foo|/arc/archive.org/leaf/foo|cache and return leaf record JSON (for naming)
/download/foo/bar|/arc/archive.org/download/foo|return file bar from item foo
n/a|/add,list,store etc|access gateway functionality
