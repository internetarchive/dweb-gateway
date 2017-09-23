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

        @classmethod
        def canonicial(cls, publisher, identifier):
            #TODO convert this identifier into a canonicised form,
            #TDO check publisher is canonicised 10.nnnn
            pass
            return publisher, identifier
            """
            As a pre-mature heads up, the DOI format is sort of underspecified. 
            It is case-insensitive (can be used in URLs, sometimes with encoding), 
            but can have weird shit like whitespace. 
            The vast majority are more "well behaved", but things like parentheses are common.
            They do always start with "10\.\d+\/" (aka, 10, period, numerical digits, slash)
            """


        @classmethod
        def findDOI(cls, publisher, identifier):
            #TODO search the sqlite database, and come back with a list of rows with any meta data found.
            #TODO gradually extend it to return the biblio info etc from the other files.

            """
            Notes from Brian on the sqlite
            Currently the sqlite database has URLs with an optional datetime column.
            If the url starts "https://archive.org/download/" then it's an item/file pointer, and there is no datetime.
            If the url starts with something else, it's a URL from wayback, and the datetime can be used to construct a
            "https://web.archive.org/web/<datetime>/<url>" URL. TODO: double-check that wayback gateway supports range-requests
            """
            pass
