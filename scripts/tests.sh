#!/usr/bin/env bash

# This is just a quick test set until proper Python tests are built

#python -m python.ServerGateway &

set -x
curl http://localhost:4244/info
echo # Terminate response

echo # Ensure blank line at end of return


curl http://localhost:4244/content/doi/10.1234/abcd-1234
echo # Terminate response

echo # Ensure blank line at end of return


curl http://localhost:4244/contenthash/doi/10.1234/abcd-1234
echo # Terminate response
