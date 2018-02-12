import socket

config = {
    "archive": {
        "url_download": "https://archive.org/download/",
    },
    "ipfs": {
        "url_add_data": "http://localhost:5001/api/v0/add", # FOr use on gateway or if run "ipfs daemon" on test machine
        # "url_add_data": "https://ipfs.dweb.me/api/v0/add",  # note Kyle was using localhost:5001/api/v0/add which wont resolve externally.
        # "url_add_url": "http://localhost:5001/api/v0/add",  #TODO-IPFS move uses of url_add_data to urladd when its working
        #"url_urlstore": "http://localhost:5001/api/v0/urlstore/add",    # FOr use on gateway or if run "ipfs daemon" on test machine
    },
    "gateway": {
        "url_download": "https://gateway.dweb.me/download/archiveid/",
        "url_torrent": "https://gateway.dweb.me/torrent/archiveid/",
    },
    "domains": {
        "metadata": 'NACL%20VERIFY%3Ah9MB6YOnYEgby-ZRkFKzY3rPDGzzGZ8piGNwi9ltBf0%3D',
    }
}

if socket.gethostname() in ["wwwb-dev0.fnf.archive.org"]:
    config["ipfs"]["url_urlstore"] = "http://localhost:5001/api/v0/urlstore/add" # Only runs in beta on archive.org research machine
