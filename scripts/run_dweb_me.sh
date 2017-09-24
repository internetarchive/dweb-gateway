#!/bin/bash

PIPS="py-dateutil redis base58 pynacl multihssh"
cd /usr/local/dweb_gateway
pip install --disable-pip-version-check -U $PIPS
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
cd python
if ps -f | grep ServerHTTP | grep -v grep
then
	echo "You need to kill that process above first"
else
    echo "Starting Server "
    python -m ServerGateway &
    ps -f | grep ServerHTTP | grep -v grep
fi


