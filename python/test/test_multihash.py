from python.Multihash import Multihash

BASESTRING="A quick brown fox"
SHA1BASESTRING="5drjPwBymU5TC4YNFK5aXXpwpFFbww"

PDF_SHA1HEX="02efe2abec13a309916c6860de5ad8a8a096fe5d"
PDF_MULTIHASHSHA1_58="5dqpnTaoMSJPpsHna58ZJHcrcJeAjW"

def test_sha1():
    assert Multihash(data=BASESTRING, code=Multihash.SHA1).multihash58 == SHA1BASESTRING, "Check expected sha1 from encoding basestring"
    assert Multihash(sha1_hex=PDF_SHA1HEX).multihash58 == PDF_MULTIHASHSHA1_58
    assert Multihash(multihash58=PDF_MULTIHASHSHA1_58).sha1_hex == PDF_SHA1HEX
