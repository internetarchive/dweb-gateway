#!/bin/bash

cd /usr/local/dweb_gateway
pip install --disable-pip-version-check -u base58 pynacl
git commit -a -m "Changes made on server"
git checkout deployed # Will run server branch
git pull
git merge deployable
git push
echo "Starting Server "
python -m python.ServerGateway &
ps -f | grep ServerGateway | grep -v grep


