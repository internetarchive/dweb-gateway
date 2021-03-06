# Dweb Gateway - Extending

This document is a work in progress on how to extend the Dweb gateway

## Adding a new data type / resolver

* Create a new file (or sometimes class in existing file)
* Create a class in that file
    * If the class conceptually holds multiple objects (like a directory or collection) subclass NameResolverDir
    * If just one file, sublass NameResolverFile
    * See SEE-OTHERNAMESPACE in Python (and potentially in clients) for places to hook in.
* Add required / optional methods
    * new(cls, namespace, *args, **kwargs) - which is passed everything from the HTTPS request except the outputtype
    
    
    
### Add the following methods

__init__(cls, namespace, *args, **kwargs) 
* Create and initialize an object, often the superclass's method is used and work done in "new"

@property mimetype
* The mimetype string for the content
    
@classmethod new(cls, namespace, *args, **kwargs)
* Create a new object, initialize from args & kwargs, often does a metadata fetch etc. 
    
retrieve(verbose)
* returns: "content" of an object, typically a binary such as a PDF
    
content(verbose)
* returns: "content" encapsulated for return to server
* default: encapsulates retrieve() with mimetype

