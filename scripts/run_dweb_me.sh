#!/bin/bash

cd /usr/local/dweb_gateway
pip install --disable-pip-version-check -u base58 pynacl
git commit -a -m "Local changes"
git checkout deployed # Will run server branch
git pull
git merge deployable
git push
python -m python.ServerGateway


