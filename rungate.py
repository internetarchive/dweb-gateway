import logging
from python.ServerGateway import DwebGatewayHTTPRequestHandler
# This is just used for running tests
from python.config import config
logging.basicConfig(**config["logging"])
DwebGatewayHTTPRequestHandler.DwebGatewayHTTPServeForever({'ipandport': ('localhost',4244)}) # Run local gateway