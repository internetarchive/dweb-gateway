from NameResolver import NameResolverDir, NameResolverFile
from miscutils import multihashsha256_58

#TODO-PYTHON3 file needs reviewing for Python3 as well as Python2

class DOI(NameResolverDir):
    """
    DOI is a class for Document Object Identifiers, an academic namespace
    typically of form   10.1234/abc123
    URL: `/xxx/doi/10.pub_id/pub_specific_id` (forwarded here by ServerGateway methods)

    Implements name resolution of the DOI namespace, via a sqlite database (provided by Brian Reynolds)

    Case insensitive, have some significant punctuation, but sometimes presented with insignificant punctuation

    Future Work
    * Build way to preload the hashstore with the hashes and URLs from the sqlite
    """

    def __init__(self, namespace, publisher, *identifier, **kwargs):
        """
        Creates the object

        :param namespace:
        :param publisher:   Publisher ID allocated by DOI.org, always of form 10.nnnn
        :param identifier:  Id for an academic article or resource, allocated by the publisher. Case insensitive, Alphanumeric plus a few (undefined) punctuation.
                            Its an array, because may be multiple fields seperated by /, can safely re-concatenate
        :param kwargs:      Any other args to the URL, ignored for now.
        """
        #TODO read from sqlite table
        #Note if you dont have your own way of using sqlite I suggest SqliteWrap from https://github.com/mitra42/sqlite_models
        """
        Pseudo-code
        * Canonicalize pub_specific_id (lowercase, strip chars)
        * Look up in sqlite to find the [hash, location]* of the file (no need to retrieve it)
        * Convert hashes to multihashes
        * For each multihash: location_store(multihash, location)
        *   Create a DOIfile(..)
        *   self.push(DOIfile)
        """
        pass

    def push(self):
        """
        Add a DOIfile to a DOI -
        :return:
        """
        pass # Note could probably be defined on NameResolverDir class

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
            Brian says its a long-tail, the vast majority of correct DOI appear to be case insensitive alphanumeric with some allowed punctuation 
            This will require lookin in the Sqlite (or asking Brian) to determine suitable characters for a OK DOI
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
