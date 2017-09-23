from NameResolver import NameResolverDir, NameResolverFile
from miscutils import multihashsha256_58

#TODO-PYTHON3 file needs reviewing for Python3 as well as Python2

class DOI(NameResolverDir):
    """
    DOI is a class for Document Object Identifiers, an academic namespace
    typically of form   10.1234/abc123

    Case insensitive, have some significant punctuation, but sometimes presented with insignificant punctuation


    """

    def __init__(self, namespace, publisher, identifier):
        """
        Creates the object

        :param namespace:
        :param publisher:
        :param identifier:
        """
        #TODO read from sqlite table
        #Note if you dont have your own way of using sqlite I suggest SqliteWrap from https://github.com/mitra42/sqlite_models
        pass

    def content(self):
        #TODO replace with something that reads out fields of object
        return {'Content-type': 'application/json',
            'data': {
                'name': "FOO BAR",
                'files': {   # Metadata for each file found with DOI goes here
                    "first.pdf": {
                        "contenthash": "Q123456",
                        "url": "/foo/bar",
                        }
                },
            }
        }

