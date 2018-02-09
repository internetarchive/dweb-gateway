import sqlite3

import logging
import requests

from .HashStore import LocationService, MimetypeService, IPLDHashService
from .Multihash import Multihash
from .NameResolver import NameResolverDir, NameResolverFile, NameResolverSearchItem, NameResolverSearch
from .miscutils import httpget
from .Errors import SearchException, NoContentException

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
    SQLITE = "data/idents_files_urls.sqlite"
    #_sqliteconnection=None  #TODO-SQL should be per thread

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
        verbose = kwargs.get("verbose", False)
        if verbose:
            logging.debug("DOI.__init__({0}, {1}, {2})".format(namespace, publisher, identifier))
        super(DOI, self).__init__(namespace, publisher, *identifier)
        db = self.sqliteconnection(verbose)                     # Lazy connection to database
        self.doi = self.canonical(publisher, *identifier)    # "10.nnnn/xxxx/yyyy"
        self._metadata = {}
        if verbose: logging.debug("DOI.__init__ looking up {0}".format(self.doi))
        sha1_list = list(db.execute('SELECT * FROM files_id_doi WHERE doi = ?;', [self.doi]))

        if verbose: logging.debug("DOI.__init__ iterating over {0} rows".format(len(sha1_list)))
        for row in sha1_list:
            _, sha1hex, _ = row
            doifile = DOIfile(doi=self.doi, multihash=Multihash(sha1hex=sha1hex), verbose=verbose)
            self.push(doifile)
        if verbose: logging.debug("DOI.__init__ completing")

    @classmethod
    def sqliteconnection(cls, verbose=False):
        """
        # This below wont work in a multithreaded server, as sqlite connections cant be used across threads and doesnt appear
        # to be a way to access thread variables.  #TODO-THREADING
        if not cls._sqliteconnection:
            if verbose: logging.debug("DOI.sqliteconnection connecting to DB")
            cls._sqliteconnection = sqlite3.connect(cls.SQLITE)
            if verbose: logging.debug("DOI.sqliteconnection connected to DB")
        return cls._sqliteconnection
        """
        # Using a new sqlite connection for each request
        return sqlite3.connect(cls.SQLITE)

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

    def push(self, doifile):
        """
        Add a DOIfile to a DOI -
        :return:    undefined
        """
        # Currently Nothing done here other than superclass adding to list.
        super(DOI, self).push(doifile)

    def metadata(self, headers=True, verbose=False):
        data = {
            "doi": self.doi,
            'metadata': self._metadata,  # Archive generated metadata - there isnt any, its all at files level for DOI
            'doi_org_metadata': self.doi_org_metadata(verbose),  # Metadata as supplied by DOI.org
            "files": [
                doifile._metadata for doifile in self.files()
            ]
        }
        mimetype = 'application/json';
        return {"Content-type": mimetype, "data": data} if headers else data

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
            logging.debug("check_if_link_works {0}".format(url))
        try:
            headers = {"accept": "*/*"}
            # This next link can fail, it follows a redirection and then can fail on th actual PDF, which isnt what we want cos we'll use a Archive URL
            request = requests.get(url, headers=headers)
        except Exception as e:
            raise e
        if verbose: logging.debug("result={0}".format(request.status_code))
        return request.status_code == 200

    @staticmethod
    def get_doi_metadata(doi, verbose=False):
        """
        For a DOI, get metadata from doi.org about that file
        #TODO - move this to browser - but having problems with CBOR
        :return: metadata on the doi in json format
        """
        url = "http://dx.doi.org/" + doi
        headers = {"accept": "application/vnd.citationstyles.csl+json"}
        r = requests.get(url, headers=headers)  # Note that with headers it wont redirect, without it will go to doc which may fail
        if verbose: logging.debug("get_doi_metadata returned: {0}".format(r))
        if r.status_code == 200:
            return r.json()
        else:
            logging.warning("Failed to read metadata at {0}".format(url))
            return None
        # If dont get metadata, the rest of our info may still be valid

    def doi_org_metadata(self, verbose=False):
        """
        Get and save metadata from DOI.org
        Same code on DOIfile - which can have doi_org_metadata when invoked singularly as in sha1hex/1a2b3c

        :param verbose:
        :return:
        """
        if verbose: logging.debug("DOI.__init__ getting metadata for {0}".format(self.doi))
        if not getattr(self,"_doi_org_metadata", None):
            self._doi_org_metadata = self.get_doi_metadata(self.doi)   # Maybe None if not found
        return self._doi_org_metadata


class DOIfile(NameResolverFile):    # Note plural
    """
    Class for one file

    Fields:
    multihash   A Multihash instance either found from the DOI, or being searched on - note its contenthash, not ipldhash

    """

    def __init__(self, doi=None, multihash=None, metadata=None, verbose=False):
        """
        Initilize a new DOIfile, usually called from new()

        :param doi:
        :param multihash:
        :param metadata:
        :param verbose:
        :raises NoContentException: if no DOI and cant find sha1 in index
        """
        super(NameResolverFile, self).__init__(None)    # TODO note this is wrong, superclass expects namespace (but ignores it)
        self.doi = doi
        self._metadata = metadata or {}    # For now all in one dict
        self.multihash = multihash
        if multihash and not self.doi:
            # Lookup DOI from sha1hex if DOI not supplied.
            if verbose: logging.debug("DOIfile.__init__ looking up {0}".format(multihash.sha1hex))
            l = list(DOI.sqliteconnection(verbose).execute('SELECT * FROM files_id_doi WHERE sha1 = ?;', [multihash.sha1hex]))
            if not l:
                raise NoContentException    # If cant find a doi, no point continuing
            self.doi, _, _ = l[0]
        if multihash:
            self.sqlite_metadata(verbose)

    def sqlite_metadata(self, verbose):
            files_metadata_list = list(DOI.sqliteconnection(verbose).execute('SELECT * FROM files_metadata WHERE sha1 = ?;', [self.multihash.sha1hex]))
            _, mimetype, size_bytes, md5 = files_metadata_list[0]
            files_list = list(DOI.sqliteconnection(verbose).execute('SELECT * FROM urls WHERE sha1 = ?;', [self.multihash.sha1hex]))
            self._metadata = {'mimetype': mimetype, 'size_bytes': size_bytes, 'md5': md5, 'multihash58': self.multihash.multihash58,
                              'files': [DOI.archive_url(file) for file in files_list]}
            if verbose: logging.debug("multihash base58={0}".format(self.multihash.multihash58))
            #multihash58_sha256 = Multihash(data=doifile.retrieve(), code=SHA256)
            #logging.debug("Saving location "+ multihash58_sha256+":"+doifile._metadata["urls"][0]  )
            LocationService.set(self.multihash.multihash58, self._metadata["files"][0], verbose=verbose)
            MimetypeService.set(self.multihash.multihash58, self._metadata["mimetype"], verbose=verbose)
            ipldhash = IPLDHashService.get(self.multihash.multihash58)    # May be None, we don't know it
            if not ipldhash:
                data = httpget(self._metadata["files"][0])
                #TODO move this to a URL or better to TransportIPFS when built
                #ipfsurl = "https://ipfs.dweb.me/api/v0/add"  # note Kyle was using localhost:5001/api/v0/add which wont resolve externally.
                ipfsurl = "http://localhost:5001/api/v0/add"  # note Kyle was using localhost:5001/api/v0/add which wont resolve externally.
                if verbose: logging.debug("Fetching IPFS from {0}".format(ipfsurl))
                #Debugging - running into problems with 404, not sure if laptop/HTTPS issue or server
                #ipldresp = requests.post(ipfsurl, files={'file': ('', data, self.metadata["mimetype"])})
                #ipldhash = ipldresp.json()['Hash']
                res = requests.post(ipfsurl, files={'file': ('', data, self._metadata["mimetype"])}).json()
                logging.debug("IPFS result={}".format(res))
                ipldhash = res['Hash']
                IPLDHashService.set(self.multihash.multihash58, ipldhash)
            self._metadata["ipldhash"] = ipldhash
            if verbose: logging.debug("sqlite_metadata done")

    @property
    def url(self):
        """
        Find the url for this DOIfile, if necessary reading the metadata and finding first URL in it.
        :return:
        """
        if not self._url:
            if not self._metadata:
                self.sqlite_metadata(verbose=False)
            self._url = self._metadata["urls"][0]
        return self._url

    @property
    def mimetype(self):     # Defined as property because NameResolver.content() needs mimetypes from various superclasses
        if not self._metadata:
            self.sqlite_metadata(verbose=False)
        return self._metadata["mimetype"]

    def retrieve(self, **kwargs):
        """
        Return content of DOI from its URL.  (typically called by NameResolver.content()

        :return:
        """
        return httpget(self.url)    #TODO-STREAM handle streams from URl

    def metadata(self, headers=True, verbose=False):
        data = {
            "doi": self.doi,
            'metadata': self._metadata,  # Archive generated metadata - there isnt any, its all at files level for DOI
            'doi_org_metadata': self.doi_org_metadata(verbose),  # Metadata as supplied by DOI.org
            "files": [
                self._metadata  # Just one, but in array to keep HTML consistent with DOI, note same as metadata above
            ]
        }
        mimetype = 'application/json';
        return {"Content-type": mimetype, "data": data} if headers else data

    def doi_org_metadata(self, verbose=False):
        """
        Get and save metadata from DOI.org

        :param verbose:
        :return:
        """
        if verbose: logging.debug("DOI.__init__ getting metadata for {0}".format(self.doi))
        if not getattr(self,"_doi_org_metadata", None):
            self._doi_org_metadata = DOI.get_doi_metadata(self.doi)   # Maybe None if not ound
        return self._doi_org_metadata

class DOIsearchItem(NameResolverSearchItem):
    # NOTE THESE ARE STUBS UNTESTED AND DONT WORK YET

    def __init__(self, result=None):
        super(DOIsearchItem, self).__init__()
        if result: # Its a DOI search result
            # Ensure 'authors' is a list, not a single string
            if type(result['authors']) is not list:
                result['authors'] = [result['authors'], ]
        self._metadata = result

    def metadata(self, headers=True, verbose=False):
        mimetype = 'application/json';
        return {"Content-type": mimetype, "data": self._metadata} if headers else self._metadata
        # Will match elastic_schema.json  which is doi, title, author, journal, date, publisher, topic, media

class DOIsearch(NameResolverSearch):
    # NOTE THESE ARE STUBS UNTESTED AND DONT WORK YET
    #TODO-SEARCH add search of scholar.archivelab.org?q=harvard or direct to elasticsearch.openjournal.foundation - this is Bryan's

    @classmethod
    def search(self, querystring, limit=20, do_highlight=False):
        """
        Use like  /metadata/search/
        :param querystring:
        :param limit:
        :param do_highlight:
        :return:
        """
        logging.debug("Search hit: {0}".format(querystring))

        querystring = querystring.replace("author:", "authors:")  # Replace author: with authors: in query


        search_request = {
            "query": {
                "query_string": {
                    "query": querystring,
                    "analyzer": "snowball",
                    "default_operator": "AND",
                    "analyze_wildcard": True,
                },
            },
            "size": limit,
        }
        if do_highlight:
            search_request['highlight'] = {
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"],
                "fields": {"_all": {}},
            }
        url = "http://localhost:9200/crossref-works/_search"  # Might parameterise part of this, but unlikely
        resp = requests.post(url, json=search_request)
        if resp.status_code != 200:
            raise SearchException(search="search_request")  # TODO-SEARCH extract useful part of search_request
        return resp.json()

    def __init__(self, namespace, querystring, limit=20, do_highlight=False, verbose=False):
        super(DOIsearch,self).__init__(namespace, querystring, verbose=verbose)
        results = self.search(querystring,
                                do_highlight=do_highlight,
                                limit=min(max(0, int(limit)), 100))
        self._list = [  DOIsearchItem(result=h) for h in results['hits']['hits'] ]
        self.count_found = results['hits']['total']
        self.count_returned = len(self._list)
        self.highlight = do_highlight

    def metadata(self, headers=True, verbose=False):
        """
        Return metadata in a useful form for the HTML query

        :return:
        """
        data =  {
                    "count_found": self.count_found,
                    "count_returned": self.count_returned,
                    "highlight": self.highlight,
                    "results": [ result.metadata(headers=False) for result in self._list ]
                }
        mimetype = 'application/json';
        return {"Content-type": mimetype, "data": data} if headers else data

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        logging.debug('hey I expected a single doi!!')
        sys.exit(-1)
    doi = DOI("doi", *sys.argv[1].split('/'))

    for i in doi.files():
        logging.debug(i)
        logging.debug(i.content())
