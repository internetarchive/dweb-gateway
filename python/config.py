config = {
    "archive": {
        "url_download": "https://archive.org/download/",
    },
    "ipfs": {
        "url_add_data": "http://localhost:5001/api/v0/add", # FOr use on gateway or if run "ipfs daemon" on test machine
        # "url_add_data": "https://ipfs.dweb.me/api/v0/add",  # note Kyle was using localhost:5001/api/v0/add which wont resolve externally.
        # "url_add_url": "http://localhost:5001/api/v0/add",  #TODO-IPFS move uses of url_add_data to urladd when its working
        "url_urlstore": "http://localhost:5001/api/v0/urlstore",    # FOr use on gateway or if run "ipfs daemon" on test machine
    },
    "gateway": {
        "url_download": "https://gateway.dweb.me/download/archiveid/",
        "url_torrent": "https://gateway.dweb.me/torrent/archiveid/",
    }
}

