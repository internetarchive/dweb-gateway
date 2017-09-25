#!/usr/bin/env bash

# This is just a quick test set until proper Python tests are built

#python -m python.ServerGateway &

set -x
curl https://gateway.dweb.me/info
echo; echo # Terminate response and blank line
curl https://gateway.dweb.me/content/doi/10.1001/jama.2009.1064?verbose=True
echo; echo # Terminate response and blank line

# Fetch the sha1 multihash from above
curl -D- -o /dev/null https://gateway.dweb.me/content/contenthash/5dr1gqVNt1mPzCL2tMRSMnJpWsJ5Qs?verbose=True
echo; echo # Terminate response and blank line

echo "Now trying errors"
#curl https://gateway.dweb.me/INVALIDCOMMAND
#curl https://gateway.dweb.me/content/doi/10.INVALIDPUB/jama.2009.1064?verbose=True
#curl https://gateway.dweb.me/content/doi/10.1001/INVALIDDOC.2009.1064?verbose=True
