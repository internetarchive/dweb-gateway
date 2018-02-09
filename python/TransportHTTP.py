# encoding: utf-8
import logging

class TransportHTTP(Transport):
    """
    Subclass of Transport.
    Implements the raw primitives via an http API to a local IPFS instance
    Only partially complete TODO - get from old library
    """

    # urlschemes = ['http','https'] - subclasses as can handle all
    supportFunctions = ['set']

    def __init__(self, options=None, verbose=False):
        """
        Create a transport object (use "setup" instead)
        |Exceptions: TransportFileNotFound if dir invalid, IOError other OS error (e.g. cant make directory)

        :param dir:
        :param options:
        """
        self.options = options or {}
        pass

    def __repr__(self):
        return self.__class__.__name__ + " " + dumps(self.options)

    def supports(self, url, func):
        return (func in supportfunctions) and (url.startswith('https:') or url.startswith('http'))       # Local can handle any kind of URL, since cached.

    def set(self, url, keyvalues, value, verbose)
