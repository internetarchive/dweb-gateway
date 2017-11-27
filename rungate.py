from python.ServerGateway import DwebGatewayHTTPRequestHandler
# This is just used for running tests
import logging
logging.basicConfig(filename='/Users/mitra/temp/dweb_gateway.log', level=logging.DEBUG)
DwebGatewayHTTPRequestHandler.DwebGatewayHTTPServeForever({'ipandport': ('localhost',4244)}) # Run local gateway