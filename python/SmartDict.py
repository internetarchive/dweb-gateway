# encoding: utf-8
import dateutil.parser  # pip py-dateutil
from json import dumps, loads
from .Errors import ToBeImplementedException, EncryptionException
"""
from Dweb import Dweb
from Transportable import Transportable
"""

# THIS FILE IS COPIED FROM THE OLD DWEB repo IT IS NOT TESTED FULLY, SO BIG CHUNKS ARE COMMENTED OUT
# - ONLY PARTS NEEDED FOR KEYPAIR ARE BACKPORTED FROM JS AND UNCOMMENTED

class SmartDict(object): #TODO-SMARTDICT - normally subclass of Transportable

    """
    Subclass of Transport that stores a data structure, usually a single layer Javascript dictionary object.
    SmartDict is intended to support the mechanics of storage and retrieval while being  subclassed to implement functionality
    that understands what the data means.

    By default any fields not starting with “_” will be stored, and any object will be converted into its url.

    The hooks for encrypting and decrypting data are at this level, depending on the _acl field, but are implemented by code in KeyPair.

     _acl If set (on master) defines storage as encrypted
    """
    table = "sd"

    def __init__(self, data=None, verbose=False, **options):
        """
        Creates and initialize a new SmartDict.

        :param data:	String|Object, If a string (typically JSON), then parse first.
                        A object with attributes to set on SmartDict via _setdata
        :param options:	Passed to _setproperties, by default overrides attributes set by data
        """
        # COPIED BACK FROM JS 2018-07-02
        self._urls = []                # Empty URLs - will be loaded by SmartDict.p_fetch if loading from an URL
        self._setdata(data)            # The data being stored - note _setdata usually subclassed does not store or set _url
        self._setproperties(options)   # Note this will override any properties set with data   #TODO-SMARTDICT need this

    def __str__(self):
        return self.__class__.__name__+"("+str(self.__dict__)+")"

    def __repr__(self):
        return repr(self.__dict__)

    # Allow access to arbitrary attributes, allows chaining e.g. xx.data.len = foo
    def __setattr__(self, name, value):
        # THis code was running self.dirty() - problem is that it clears url during loading from the dWeb
        if name[0] != "_":
            if "date" in name and isinstance(value,basestring):
                value = dateutil.parser.parse(value)
        return super(SmartDict, self).__setattr__(name, value)  # Calls any property esp _data

    def _setproperties(self, options):  # Call chain is ... onloaded or constructor > _setdata > _setproperties > __setattr__
        # Checked against JS 20180703
        for k in options:
            self.__setattr__(k, options[k])

    def __getattr__(self, name):    # Need this in Python while JS supports foo._url
        return self.__dict__.get(name)

    """

    def preflight(self, dd):
        "-"-"
        Default handler for preflight, strips attributes starting “_” and stores and converts objects to urls.
        Subclassed in AccessControlList and KeyPair to avoid storing private keys.
        :param dd:	dictionary to convert..
        :return:	converted dictionary
        "-"-"
        res = {
            k: dd[k].store()._url if isinstance(dd[k], Transportable) else dd[k]
            for k in dd
            if k[0] != '_'
        }
        res["table"] = res.get("table",self.table)  # Assumes if used table as a field, that not relying on it being the table for loading
        assert res["table"]
        return res

    def _getdata(self):
        "-"-"
        Prepares data for sending. Retrieves attributes, runs through preflight.
        If there is an _acl field then it passes data through it for encrypting (see AccessControl library)
        Exception: UnicodeDecodeError - if its binary
        :return:	String suitable for rawstore
        "-"-"
        try:
            res = self.transport().dumps(self.preflight(self.__dict__.copy())) # Should call self.dumps below { k:self.__dict__[k] for k in self.__dict__ if k[0]!="_" })
        except UnicodeDecodeError as e:
            print "Unicode error in StructuredBlock"
            print self.__dict__
            raise e
        if self._acl:   # Need to encrypt
            encdata = self._acl.encrypt(res, b64=True)
            dic = {"encrypted": encdata, "acl": self._acl._publicurl, "table": self.table}
            res = self.transport().dumps(dic)
        return res

    ABOVE HERE NOT BACKPORTED FROM JS
    """

    def _setdata(self, value):
        """
        Stores data, subclass this if the data should be interpreted as its stored.
        value	Object, or JSON string to load into object.
        """
        # Note SmartDict expects value to be a dictionary, which should be the case since the HTTP requester interprets as JSON
        # Call chain is ...  or constructor > _setdata > _setproperties > __setattr__
        # COPIED BACK FROM JS 2018-07-02
        value = loads(value) if isinstance(value, str) else value  # Will throw exception if it isn't JSON
        if value and ("encrypted" in value):
            raise EncryptionException("Should have been decrypted in fetch")
        self._setproperties(value);

    """
    BELOW HERE NOT BACKPORTED FROM JS

    def _match(self, key, val):
        if key[0] == '.':
            return (key == '.instance' and isinstance(self, val))
        else:
            return (val == self.__dict__[key])

    def match(self, dict):
        "-"-"
        Checks if a object matches for each key:value pair in the dictionary.
        Any key starting with "." is treated specially esp:
        .instanceof: class: Checks if this is a instance of the class
        other fields will be supported here, any unsupported field results in a false.

        :returns: boolean, true if matches
        "-"-"
        return all([self._match(k, dict[k]) for k in dict])


    @classmethod
    def fetch(cls, url, verbose):
        "-"-"
        Fetches the object from Dweb, passes to decrypt in case it needs decrypting,
        and creates an object of the appropriate class and passes data to _setdata
        This should not need subclassing, (subclass _setdata or decrypt instead).

        :return: New object - e.g. StructuredBlock or MutableBlock
        :catch: TransportError - can probably, or should throw TransportError if transport fails
        :throws: TransportError if url invalid, Authentication Error
        "-"-"
        from letter2class.py import LetterToClass
        if verbose: print "SmartDict.fetch", url;
        data = super(SmartDict, cls).fetch(url, verbose) #Fetch the data Throws TransportError immediately if url invalid, expect it to catch if Transport fails
        data = Dweb.transport(url).loads(data)          # Parse JSON //TODO-REL3 maybe function in Transportable
        table = data.table                              # Find the class it belongs to
        cls = LetterToClass[table]             # Gets class name, then looks up in Dweb - avoids dependency
        if not cls:
            raise ToBeImplementedException("SmartDict.fetch: "+table+" isnt implemented in table2class")
        if not isinstance(Dweb.table2class[table], cls):
            raise ForbiddenException("Avoiding data driven hacks to other classes - seeing "+table);
        data = cls.decrypt(data, verbose)             # decrypt - may return string or obj , note it can be suclassed for different encryption
        data["_url"] = url;                             # Save where we got it - preempts a store - must do this afer decrypt
        return cls(data)

    @classmethod
    def decrypt(data, verbose):
        "-"-"
         This is a hook to an upper layer for decrypting data, if the layer isn't there then the data wont be decrypted.
         Chain is SD.fetch > SD.decryptdata > ACL|KC.decrypt, then SD.setdata

         :param data: possibly encrypted object produced from json stored on Dweb
         :return: same object if not encrypted, or decrypted version
         "-"-"
        return AccessControlList.decryptdata(data, verbose)

    def dumps(self):    # Called by json_default, but preflight() is used in most scenarios rather than this
        1/0 # DOnt believe this is used
        return {k: self.__dict__[k] for k in self.__dict__ if k[0] != "_"}  # Serialize the dict, excluding _xyz

    def copy(self):
        return self.__class__(self.__dict__.copy())
    """