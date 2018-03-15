import socket
import logging

config = {
    "archive": {
        "url_download": "https://archive.org/download/",
        "url_servicesimg": "https://archive.org/services/img/",
    },
    "ipfs": {
        "url_add_data": "http://localhost:5001/api/v0/add", # FOr use on gateway or if run "ipfs daemon" on test machine
        # "url_add_data": "https://ipfs.dweb.me/api/v0/add",  # note Kyle was using localhost:5001/api/v0/add which wont resolve externally.
        # "url_add_url": "http://localhost:5001/api/v0/add",  #TODO-IPFS move uses of url_add_data to urladd when its working
        #"url_urlstore": "http://localhost:5001/api/v0/urlstore/add",    # FOr use on gateway or if run "ipfs daemon" on test machine
    },
    "gateway": {
        "url_download": "https://gateway.dweb.me/download/archiveid/",
        "url_servicesimg": "https://gateway.dweb.me/thumbnail/archiveid/",
        "url_torrent": "https://gateway.dweb.me/torrent/archiveid/",
    },
    "domains": {
        "metadata": 'NACL VERIFY:h9MB6YOnYEgby-ZRkFKzY3rPDGzzGZ8piGNwi9ltBf0=',
    },
    "directories": {
        "bootloader": "/usr/local/dweb-transport/examples/bootloader.html",
    },
    "logging": {
        "filename": '/Users/mitra/temp/dweb_gateway.log',
        "level": logging.DEBUG
    }
}

if socket.gethostname() in ["wwwb-dev0.fnf.archive.org"]:
    config["ipfs"]["url_urlstore"] = "http://localhost:5001/api/v0/urlstore/add" # Only runs in beta on archive.org research machine
elif socket.gethostname().startswith('mitraglass'):
    config["directories"]["bootloader"] = "/Users/mitra/git/_github_internetarchive/dweb-transport/examples/bootloader.html"
    config["logging"] = { "level": logging.DEBUG }  #Not to file
else:
    print("Needs configuring for {}".format(socket.gethostname()))

