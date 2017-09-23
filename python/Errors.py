# encoding: utf-8

#TODO-PYTHON3 file needs reviewing for Python3 as well as Python2

class MyBaseException(Exception):
    """
    Base class for Exceptions

    Create subclasses with parameters in their msg e.g. {message} or {name}
    and call as in: raise NewException(name="Foo");

    msgargs Arguments that slot into msg
    __str__ Returns msg expanded with msgparms
    """
    errno=0
    httperror = 500         # See BaseHTTPRequestHandler for list of errors
    msg="Generic Model Exception"   #: Parameterised string for message
    def __init__(self, **kwargs):
        self.msgargs=kwargs # Store arbitrary dict of message args (can be used ot output msg from template

    def __str__(self):
        try:
            return self.msg.format(**self.msgargs)
        except:
            return self.msg+" "+unicode(self.msgargs)

class ToBeImplementedException(MyBaseException):
    """
    Raised when some code has not been implemented yet
    """
    httperror = 501
    msg = "{name} needs implementing"

# Note TransportError is in Transport.py

class CodingException(MyBaseException):
    httperror = 501
    msg = "Coding Error: {message}"

class EncryptionException(MyBaseException):
    httperror = 500  # Forbidden (Authentication won't help)
    msg = "Encryption error: {message}"

class ForbiddenException(MyBaseException):
    httperror = 403     # Forbidden (Authentication won't help)
    msg = "Not allowed: {what}"

class AuthenticationException(MyBaseException):
    """
    Raised when some code has not been implemented yet
    """
    httperror = 500  # TODO-AUTHENTICATON - which code
    msg = "Authentication Exception: {message}"

class IntentionallyUnimplementedException(MyBaseException):
    """
    Raised when some code has not been implemented yet
    """
    httperror = 501
    msg = "Intentionally not implemented: {message}"

class DecryptionFailException(MyBaseException):
    """
    Raised if decrypytion failed - this could be cos its the wrong (e.g. old) key
    """
    msg = "Decryption fail"

class SecurityWarning(MyBaseException):
    msg = "Security warning: {message}"


class AssertionFail(MyBaseException): #TODO-BACKPORT - console.assert on JS should throw this
    """
    Raised when something that should be true isn't - usually a coding failure or some change not propogated fully
    """
    httperror = 500
    msg = "{message}"


"""

# Following are currently obsolete - not being used in Python or JS

class PrivateKeyException(MyBaseException):
    #Raised when some code has not been implemented yet
    httperror = 500
    msg = "Operation requires Private Key, but only Public available."

"""