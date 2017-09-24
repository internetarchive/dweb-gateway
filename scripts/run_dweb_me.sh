#!/bin/bash

PIPS="multihash py-dateutil redis base58 pynacl"
cd /usr/local/dweb_gateway
pip install --disable-pip-version-check -U $PIPS
[ -d data ] || mkdir data
if git commit -a -m "Changes made on server"
then
	git push
fi
git checkout deployed # Will run server branch
git pull
git merge origin/deployable
if git commit -a -m "merged"
then
	git push
fi
if [ ! -f data/idents_files_urls.sqlite.gz ]
then
	curl -L -o data/idents_files_urls_sqlite.gz https://archive.org/download/ia_papers_manifest_20170919/index/idents_files_urls.sqlite.gz
	gunzip data/idents_files_urls.sqlite.gz
fi
cd python
if ps -f | grep ServerGateway | grep -v grep
then
	echo "You need to kill that process above first"
else
    echo "Starting Server "
    python -m ServerGateway &
    ps -f | grep ServerGateway | grep -v grep
fi


