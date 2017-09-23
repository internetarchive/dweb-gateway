from miscutils import multihashsha256_58

# Base classes for DOI etc
# Methods not defined yet
#TODO-PYTHON3 file needs reviewing for Python3 as well as Python2

class NameResolver(object):

    def contenthash(self):
        """
        By default contenthash is the hash of the content.

        :return:
        """
        return {'Content-type': 'text/plain',
         'data': multihashsha256_58(self.content())  # A list of names of services supported below  (not currently consumed anywhere)
         }

class NameResolverDir(NameResolver):
    pass

class NameResolverFile(NameResolver):
    pass
