#!/bin/bash

#cd /Users/mitra/git/luminutes/server
git commit -a -m "Local changes"
git checkout deployed # Will run server branch
git pull
git merge deployable
git push



