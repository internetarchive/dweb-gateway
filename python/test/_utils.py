from python.ServerGateway import DwebGatewayHTTPRequestHandler


def _processurl(url, verbose=False, headers={}, **kwargs):
    # Simulates HTTP Server process - wont work for all methods
    args = url.split('/')
    method = args.pop(0)
    DwebGatewayHTTPRequestHandler.headers = headers # This is a kludge, put headers on class, method expects an instance.
    f = getattr(DwebGatewayHTTPRequestHandler, method)
    assert f
    namespace = args.pop(0)
    if verbose: kwargs["verbose"] = True
    res = f(DwebGatewayHTTPRequestHandler, namespace, *args, **kwargs)
    return res
