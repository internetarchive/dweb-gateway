from NameResolver import NameResolverDir, NameResolverFile
from miscutils import multihashsha256_58
from Errors import TransportURLNotFound, CodingException
from HashStore import LocationService
import requests

#TODO-PYTHON3 file needs reviewing for Python3 as well as Python2

class ContentHash(NameResolverFile):
    """
    ContentHash is a class for retrieval by content hash
    typically of form   contenthash/Qmd.... for SHA256 or contenthahs/5.... for SHA1
    URL: `/xxx/contenthash/Q...` (forwarded here by ServerGateway methods)

    Implements name resolution of the ContentHash namespace, via a local store and any other internal archive method

    Future Work
    * Build way to preload the hashstore with the hashes and URLs from various parts of the Archive
    """

    def __init__(self, namespace, multihash58, **kwargs):
        """
        Creates the object

        :param namespace:   "contenthash"
        :param multihash:   Base58 representation of multihash (may support other bases later)
        :param kwargs:      Any other args to the URL, ignored for now.
        """
        """
        Pseudo-code
        Looks up the multihash in Location Service to find where can be retrieved from.
        """
        if namespace != "contenthash":
            raise CodingException("namespace != contenthash")
        self.url = LocationService.get(multihashsha256_58) #TODO-FUTURE recognize different types of location, currently assumes URL

    def push(self):
        """
        Add a Shard to a ContentHash -
        :return:
        """
        pass # Note could probably be defined on NameResolverFile class

    def content(self):
        # Returns the content - i.e. bytes
        #TODO-STREAMS future work to return a stream

        try:
            r = requests.get(self.url)
            r.raise_for_status()
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            if r is not None and (r.status_code == 404):
                raise TransportURLNotFound(url=self.url)
            else:
                # print e.__class__.__name__, e
                # TODO-LOGGING: logger.error(e)
                raise e  # For now just raise it
        data = r.text   #TODO-STREAM return a stream to the content,
        return {'Content-type': 'application/json',
            'data': data,
        }

    # def canonical - not needed as already in a canonical form

