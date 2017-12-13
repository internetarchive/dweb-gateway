"""
A set of classes to hold different kinds of hashes etc and convert between them,

Much of this was adapted from https://github.com/tehmaze/python-multihash,
which seems to have evolved from the pip3 multihash, which is seriously broken.
"""

import hashlib
import struct
import sha3
import pyblake2
import base58
import binascii
import logging

from sys import version as python_version
if python_version.startswith('3'):
    from urllib.parse import urlparse
else:
    from urlparse import urlparse        # See https://docs.python.org/2/library/urlparse.html
from .Errors import MultihashError

class Multihash(object):
    """
    Superclass for all kinds of hashes, this is for convenience in passing things around between some places that want binary, or
    multihash or hex.

    core storage is as a multihash_binary i.e. [ code, length, digest...]

    Each instance:
    code = SHA1, SHA256 etc (uses integer conventions from multihash
    """

    # Constants
    # 0x01..0x0F are app specific (unused)
    SHA1 = 0x11
    SHA2_256 = 0x12
    SHA2_512 = 0x13
    SHA3 = 0x14
    BLAKE2B = 0x40
    BLAKE2S = 0x41

    FUNCS = {
        SHA1:       hashlib.sha1,
        SHA2_256:   hashlib.sha256,
                    # Alternative use nacl.hash.sha256(data, encoder=nacl.encoding.RawEncoder) which has different footprint
        SHA2_512:   hashlib.sha512,
        SHA3:     lambda: hashlib.new('sha3_512'),
        BLAKE2B:    lambda: pyblake2.blake2b(),
        BLAKE2S:    lambda: pyblake2.blake2s(),
    }
    LENGTHS = {
        SHA1: 20,
        SHA2_256: 32,
        SHA2_512: 64,
        SHA3: 64,
        BLAKE2B: 64,
        BLAKE2S: 32,
    }

    def assertions(self, code=None):
        if code and code != self.code:
            raise MultihashError(message="Expecting code {}, got {}".format(code, self.code))
        if self.code not in self.FUNCS:
            raise MultihashError(message="Unsupported Hash type {}".format(self.code))
        if (self.digestlength != len(self.digest)) or (self.digestlength != self.LENGTHS[self.code]):
            raise MultihashError(message="Invalid lengths: expect {}, byte {}, len {}"
                                  .format(self.LENGTHS[self.code], self.digestlength, len(self.digest)))

    def __init__(self, multihash58=None, sha1hex=None, data=None, code=None, url=None):
        """
        Accept variety of parameters,

        :param multihash_58:
        """
        digest = None

        if url:
            logging.debug("url={} {}".format(url.__class__.__name__,url))
            if isinstance(url, str) and "/" in url:   # https://.../Q...
                url = urlparse(url)
            if not isinstance(url, str):
                multihash58 = url.path.split('/')[-1]
            else:
                multihash58 = url
            if multihash58[0] not in ('5','Q'):     # Simplistic check that it looks ok-ish
                raise MultihashError(message="Invalid hash portion of URL {}".format(multihash58))
        if multihash58:
            self._multihash_binary = base58.b58decode(multihash58)
        if sha1hex:
            if python_version.startswith('2'):
                digest = sha1hex.decode('hex')  # Python2
            else:
                digest = bytes.fromhex(sha1hex)  # Python3
            code = self.SHA1
        if data and code:
                digest = self._hash(code, data)
        if digest and code:
            self._multihash_binary = bytearray([code, len(digest)])
            self._multihash_binary.extend(digest)
        self.assertions()   # Check consistency

    def _hash(self, code, data):
        if not code in self.FUNCS:
            raise MultihashError(message="Cant encode hash code={}".format(code))
        hashfn = self.FUNCS.get(code)()  # Note it calls the function in that strange way hashes work!
        if isinstance(data, bytes):
            hashfn.update(data)
        elif isinstance(data, str):
            # In Python 3 this is ok, would be better if we were sure it was utf8
            # raise MultihashError(message="Should be passing bytes, not strings as could encode multiple ways")  # TODO can remove this if really need to handle UTF8 strings, but better to push conversion upstream
            hashfn.update(data.encode('utf-8'))
        return hashfn.digest()

    def check(self, data):
        assert(self.digest == self._hash(self.code, data), "Hash doesnt match expected")

    @property
    def code(self):
        return self._multihash_binary[0]

    @property
    def digestlength(self):
        return self._multihash_binary[1]

    @property
    def digest(self):
        """
        :return: bytes, the digest part of any multihash
        """
        return self._multihash_binary[2:]

    @property
    def sha1hex(self):
        """
        :return: The hex of the sha1 (as used in DOI sqlite tables)
        """
        self.assertions(self.SHA1)
        return binascii.hexlify(self.digest).decode('utf-8')  # The decode is turn bytes b'a1b2' to str 'a1b2'

    @property
    def multihash58(self):
        return base58.b58encode(bytes(self._multihash_binary))
