from python.ServerGateway import DwebGatewayHTTPRequestHandler

DOIURL = "content/doi/10.1001/jama.2009.1064"
CONTENTMULTIHASH = "5dr1gqVNt1mPzCL2tMRSMnJpWsJ5Qs"
CONTENTHASHURL = "content/contenthash/" + CONTENTMULTIHASH
CONTENTSIZE = 262438

def _processurl(url, verbose):
    # Simulates HTTP Server process - wont work for all methods
    args=url.split('/')
    method = args.pop(0)
    assert method in ("content",), "Unsupported method for _processurl"
    namespace = args.pop(0)
    kwargs = {}
    if verbose: kwargs["verbose"]=True
    obj = DwebGatewayHTTPRequestHandler.namespaceclasses[namespace](namespace, *args, **kwargs)
    res = getattr(obj, method)(verbose=verbose)
    if verbose: print(res)
    return res

def test_doi_resolve():
    verbose=True   # True to debug
    res = _processurl(DOIURL, verbose)
    assert res["Content-type"] == "application/json"
    assert res["data"]["files"][0]["sha1multihash"] == CONTENTMULTIHASH


def test_contenthash_resolve():
    verbose=True   # True to debug
    res = _processurl(CONTENTHASHURL, verbose)
    assert res["Content-type"] == "application/pdf"
    assert len(res["data"]) == CONTENTSIZE

