import socket
import logging
import urllib.parse


config = {
    "archive": {
        "url_download": "https://archive.org/download/",
        "url_servicesimg": "https://archive.org/services/img/",
        "url_metadata": "https://archive.org/metadata/",
        "url_btihsearch": 'https://archive.org/advancedsearch.php?fl=identifier,btih&output=json&rows=1&q=btih:',
    },
    "ipfs": {
        "url_add_data": "http://localhost:5001/api/v0/add", # FOr use on gateway or if run "ipfs daemon" on test machine
        # "url_add_data": "https://ipfs.dweb.me/api/v0/add",  # note Kyle was using localhost:5001/api/v0/add which wont resolve externally.
        # "url_add_url": "http://localhost:5001/api/v0/add",  #TODO-IPFS move uses of url_add_data to urladd when its working
        "url_urlstore": "http://localhost:5001/api/v0/urlstore/add",    # Should have "ipfs daemon" running locally
        "url_dht_provide": "http://localhost:5001/api/v0/dht/provide",
    },
    "gateway": {
        "url_metadata": "https://https://dweb.me/arc/archive.org/metadata/",
        "url_download": "https://dweb.me/arc/archive.org/download/",
        "url_servicesimg": "https://dweb.me/arc/archive.org/thumbnail/",
        "url_torrent": "https://dweb.me/arc/archive.org/torrent/",
    },
    "httpserver": {  # Configuration used by generic HTTP server
        "favicon_url": "https://dweb.me/favicon.ico",
        "root_path": "info",
    },
    "domains": {
        # This is also name of directory in /usr/local/dweb-gateway/.cache/table, if change this then can safely rename that directory to new name to retain metadata saved
        "metadataverifykey": 'NACL VERIFY:h9MB6YOnYEgby-ZRkFKzY3rPDGzzGZ8piGNwi9ltBf0=',
        "metadatapassphrase": "Replace this with something secret/arc/archive.org/metadata",                       # TODO - change for something secret!
        "directory": '/usr/local/dweb-gateway/.cache/table/',                             # Used by maintenance note overridden below for mitraglass (mitra's laptop)
    },
    "directories": {
        "bootloader": "/usr/local/dweb-archive/dist/bootloader.html",               # Location of bootloader file, note overridden below for mitraglass (mitra's laptop)
    },
    "logging": {
        "level": logging.DEBUG,
        # "filename": '/var/log/dweb/dweb-gateway', # Use stdout for logging and redirect in supervisorctl
    },
    "ignoreurls": [ # Ignore these, they are hacks or similar
        urllib.parse.unquote("%E2%80%9D"),
        ".well-known",
        "clientaccesspolicy.xml",
        "db",
        "index.php",
        "mysqladmin",
        "login.cgi",
        "robots.txt",   #Not a hack, but we dont have one TODO
        "phpmyadmin",
        "phpMyAdminold",
        "phpMyAdmin.old",
        "phpmyadmin-old",
        "phpMyadmin_bak",
        "phpMyAdmin",
        "phpma"
        "phpmyadmin0",
        "phpmyadmin1",
        "phpmyadmin2",
        "pma",
        "PMA",
        "scripts",
        "setup.php",
        "sitemap.xml",
        "sqladmin",
        "tools",
        "typo3",
        "web",
        "www",
        "xampp",
    ]

}

if socket.gethostname() in ["wwwb-dev0.fnf.archive.org"]:
    pass
elif socket.gethostname().startswith('mitraglass'):
    config["directories"]["bootloader"] = "/Users/mitra/git/dweb-archive/bootloader.html"
    config["domains"]["directory"] = "/Users/mitra/git/dweb-gateway/.cache/table/"
else:
    # Probably on docker
    pass

