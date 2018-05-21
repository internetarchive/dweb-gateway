#!/bin/bash

set -x
cd /usr/local/dweb-gateway
#pip install --disable-pip-version-check -U $PIPS
pip3 -q install --disable-pip-version-check -U -r python/requirements.txt
[ -d data ] || mkdir data
# First push whatever branch we are on
git status | grep 'nothing to commit' || git commit -a -m "Changes made on server"
git status | grep 'git push' && git push

# Now switch to deployed branch - we'll probably be on it already 
git checkout deployed # Will run server branch
git pull

# Now merge the origin of deployable
git merge origin/deployable

# And pt 
git status | grep 'nothing to commit' || git commit -a -m "Merged deployable into deployed on server"
git status | grep 'git push' && git push

if [ ! -f data/idents_files_urls.sqlite ]
then
	curl -L -o data/idents_files_urls.sqlite.gz https://archive.org/download/ia_papers_manifest_20170919/index/idents_files_urls.sqlite.gz
	gunzip data/idents_files_urls.sqlite.gz
fi

sudo supervisorctl restart dweb-gateway


