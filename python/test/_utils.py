from python.ServerGateway import DwebGatewayHTTPRequestHandler


def _processurl(url, verbose, **kwargs):
    # Simulates HTTP Server process - wont work for all methods
    args = url.split('/')
    method = args.pop(0)
    f = getattr(DwebGatewayHTTPRequestHandler, method)
    assert f
    namespace = args.pop(0)
    if verbose: kwargs["verbose"] = True
    print("XXX@_pu args=",args)
    res = f(DwebGatewayHTTPRequestHandler, namespace, *args, **kwargs)
    return res
