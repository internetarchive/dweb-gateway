# Dweb Gateway - Metadata


Metadata changes - in brief….

See []https://dweb.me/arc/archive.org/metadata/commute] for example
```
{ 
    collection_titles {
        artsandmusicvideos: “Arts & Music”   # Maps collection name to the title in the UI
    files: [
        {
            contenthash: contenthash:/contenthash/<base58 content multihash - current sha1>
            magnetlink:    “magnet …. /<filename>”
        }
    ]
    metadata: {
        magnetlink: “magnet ….”
        thumbnaillinks: [
            “ipfs:/ipfs/<ipfs hash>”,                                                    # IPFS link (lazy added if not already in Redis)
            “http://dweb.me/arc/archive.org/thumbnail/commute”,  # Direct http link
        ]
}
```

[]https://dweb.me/arc/archive.org/metadata/commute/commute.avi]
Expands on the files metadata to add 
```
{
    contenthash: contenthash:/contenthash/<base58 content multihash - current sha1>
    ipfs:  ipfs:/ipfs/<ipfshash> # Adds IPFS link after lazy adding file to IPFS (only done at this point because of speed of adding)
    magnetlink:    “magnet …. /<filename>”
}
``` 