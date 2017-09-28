from .NameResolver import NameResolverDir, NameResolverFile
from .Multihash import Multihash
import sqlite3
from .miscutils import httpget
from .HashStore import LocationService, MimetypeService, IPLDHashService
import requests
import util_multihash as multihash
import base58
from sys import version as python_version


class DOI(NameResolverDir):
    """
    DOI is a class for Document Object Identifiers, an academic namespace
    typically of form   10.1234/abc123
    URL: `/xxx/doi/10.pub_id/pub_specific_id` (forwarded here by ServerGateway methods)

    Implements name resolution of the DOI namespace, via a sqlite database (provided by Brian Reynolds)

    Case insensitive, have some significant punctuation, but sometimes presented with insignificant punctuation

    Future Work
    * Build way to preload the hashstore with the hashes and URLs from the sqlite

    TODO - ssome of this will end up in NameResolverDir as we build other classe and see commonalities
    """

    """
    $ cd data; sqlite3 idents_files_urls.sqlite .schema 
    CREATE TABLE files_id_doi (doi text not null, sha1 char(40) not null, type text);
    CREATE UNIQUE INDEX file_id_doi_sha1 on files_id_doi (sha1);
    CREATE INDEX files_doi on files_id_doi (doi);
    CREATE TABLE files_metadata (sha1 char(40) not null, mimetype text, size_bytes integer, md5 char(32));
    CREATE INDEX files_metadata_sha1 on files_metadata (sha1);
    CREATE TABLE urls (sha1 char(40) not null, url text not null, datetime integer);
    CREATE INDEX url_sha1 on urls (sha1);
    """

    # SQLITE="../data/idents_files_urls_sqlite"   # Old version in Python2 when working dir was "python"
    SQLITE="data/idents_files_urls.sqlite"
    _sqliteconnection=None

    def __init__(self, namespace, publisher, *identifier, **kwargs):
        """
        Creates the object

        :param namespace:
        :param publisher:   Publisher ID allocated by DOI.org, always of form 10.nnnn
        :param identifier:  Id for an academic article or resource, allocated by the publisher. Case insensitive, Alphanumeric plus a few (undefined) punctuation.
                            Its an array, because may be multiple fields seperated by /, can safely re-concatenate
        :param kwargs:      Any other args to the URL, ignored for now.
        """
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
        verbose=kwargs.get("verbose",False)
        if verbose: print("DOI.__init__",namespace,publisher,identifier)
        super(DOI,self).__init__(namespace, publisher, *identifier)
        db = self.sqliteconnection(verbose)                     # Lazy connection to database
        self.doi = self.canonical(publisher, *identifier)    # "10.nnnn/xxxx/yyyy"
        self.metadata = {}
        if verbose: print("DOI.__init__ getting metadata for",self.doi)
        self.doi_org_metadata = {}  # Will hold metadata retrieved from doi.org
        self.get_doi_metadata(verbose)
        if verbose: print("DOI.__init__ looking up",self.doi)
        sha1_list = list(db.execute('SELECT * FROM files_id_doi WHERE doi = ?;', [self.doi]))

        if verbose: print("DOI.__init__ iterating over",len(sha1_list),"rows")
        for row in sha1_list:
            _, sha1_hex, _ = row
            doifile = DOIfile(doi=self.doi, multihash=Multihash(sha1_hex=sha1_hex))
            self.push(doifile)
        if verbose: print("DOI.__init__ completing")

    @classmethod
    def sqliteconnection(cls, verbose=False):
        if not cls._sqliteconnection:
            if verbose: print("DOI.sqliteconnection connecting to DB")
            cls._sqliteconnection = sqlite3.connect(cls.SQLITE)
            if verbose: print("DOI.sqliteconnection connected to DB")
        return cls._sqliteconnection


    @staticmethod
    def archive_url(row):
        """
        Take a tuple of sha-1 URL datetime and return a direct URL to file content
        Currently the sqlite database has URLs with an optional datetime column.
        If the url starts "https://archive.org/download/" then it's an item/file pointer, and there is no datetime.
        If the url starts with something else, it's a URL from wayback, and the datetime can be used to construct a
        "https://web.archive.org/web/<datetime>/<url>" URL. TODO: double-check that wayback gateway supports range-requests
        :return: url to file content
        """
        _, url, datetime = row  # sha1, url, datetime(optional)
        return 'https://web.archive.org/web/{}/{}'.format(datetime, url) if datetime else url

    def push(self,doifile):
        """
        Add a DOIfile to a DOI -
        :return:    undefined
        """
        # Currently Nothing done here other than superclass adding to list.
        super(DOI, self).push(doifile)

    def content(self, verbose=False):
        return {'Content-type': 'application/json',
            'data': {
                'metadata': self.metadata,  # Archive generated metadata - there isnt any, its all at files level for DOI
                'doi_org_metadata': self.doi_org_metadata,  # Metadata as supplied by DOI.org
                "files": [
                    doifile.metadata for doifile in self.files()
                ]
            }
        }

    @classmethod
    def canonical(cls, publisher, *identifier):
        """
        As a pre-mature heads up, the DOI format is sort of underspecified.
        It is case-insensitive (can be used in URLs, sometimes with encoding),
        but can have weird shit like whitespace.
        The vast majority are more "well behaved", but things like parentheses are common.
        They do always start with "10\.\d+\/" (aka, 10, period, numerical digits, slash)
        Brian says its a long-tail, the vast majority of correct DOI appear to be case insensitive alphanumeric with some allowed punctuation
        This will require lookin in the Sqlite (or asking Brian) to determine suitable characters for a OK DOI
        """
        #TODO convert this identifier into a canonicised form,
        #TDO check publisher is canonicised 10.nnnn
        return publisher.lower() + "/" + "/".join([i.lower() for i in identifier])


    def check_if_link_works(self, url, verbose=False):
        """
        See if a link is valid (i.e., returns a '200' to the HTML request).
        """
        if verbose:
            print("check_if_link_works",url)
        print("XXX@check_if_link_works - dummied out")
        #return True
        try:
            headers = {"accept": "*/*"}
            # This next link can fail, it follows a redirection and then can fail on th actual PDF, which isnt what we want cos we'll use a Archive URL
            request = requests.get(url, headers=headers)
        except Exception as e:
            raise e
        if verbose: print("result=", request.status_code)
        return request.status_code == 200


    def get_doi_metadata(self, verbose):
        """
        For a DOI, get metadata from doi.org about that file
        TODO: pick which fields want to analyze, e.g.
        :return: metadata on the doi in json format
        """
        url = "http://dx.doi.org/" + self.doi
        headers = {"accept": "application/vnd.citationstyles.csl+json"}
        r = requests.get(url, headers=headers) # Note that with headers it wont redirect, without it will go to doc which may fail
        if verbose: print("get_doi_metadata returned:",r)
        if r.status_code == 200:
            self.doi_org_metadata = r.json()
        # If dont get metadata, the rest of our info may still be valid

class DOIfile(NameResolverFile):
    """
    Class for one file
    """

    # TODO get ContentHash to build a DOIfile

    def __init__(self, doi=None, multihash=None, metadata=None, verbose=False):
        super(NameResolverFile, self).__init__(metadata)
        self.doi = doi
        self.metadata = metadata or {}    # For now all in one dict
        self.multihash = multihash
        if multihash and not self.doi:
            # Lookup DOI from sha1_hex if not supplied.
            if verbose: print("DOIfile.__init__ looking up", multihash.sha1_hex)
            self.doi, _, _ = list(db.execute('SELECT * FROM files_id_doi WHERE sha1 = ?;', [multihash.sha1_hex]))[0]
        if multihash:
            self.sqlite_metadata(verbose)

    def sqlite_metadata(self, verbose):
            files_metadata_list = list(DOI.sqliteconnection(verbose).execute('SELECT * FROM files_metadata WHERE sha1 = ?;', [self.multihash.sha1_hex]))
            _, mimetype, size_bytes, md5 = files_metadata_list[0]
            files_list = list(DOI.sqliteconnection(verbose).execute('SELECT * FROM urls WHERE sha1 = ?;', [self.multihash.sha1_hex]))
            self.metadata = { 'mimetype': mimetype, 'size_bytes': size_bytes, 'md5': md5, 'multihash58': self.multihash.multihash58,
                    'files': [DOI.archive_url(file) for file in files_list] }
            if verbose: print("multihash base58=",self.multihash.multihash58)
            #multihash58_sha256 = Multihash(data=doifile.retrieve(), code=SHA256)
            #print("Saving location", multihash58_sha256, doifile.metadata["urls"][0]  )
            LocationService.set(self.multihash.multihash58, self.metadata["files"][0],verbose=verbose)
            MimetypeService.set(self.multihash.multihash58, self.metadata["mimetype"],verbose=verbose)
            ipldhash = IPLDHashService.get(self.multihash.multihash58)    # May be None, we don't know it
            if ipldhash:
                self.metadata["ipldhash"] = ipldhash
            else:
                pass
                #TODO-IPFS this is where we send the contenthash to IPFS


    def retrieve(self):
        return httpget(self.metadata["urls"][0])

    def content(self):
        #TODO iterate over urls and find first matching hash
        return { "Content-type": self.metadata["mimetype"], "data": self.retrieve() }

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print('hey I expected a single doi!!')
        sys.exit(-1)
    doi = DOI("doi", *sys.argv[1].split('/'))

    for i in doi.files():
        print(i)
        print(i.content())

