#!python

import sqlite3
import sys


def archive_url(row):
    """
    Take a tuple of sha-1 URL datetime and return a direct URL to file content
    :return: url to file content
    """
    sha1, url, datetime = row
    if not datetime:
        return url
    else:
        return 'https://web.archive.org/web/{}/{}'.format(datetime, url)


def lookup_doi(the_doi):
    """
    Take a DOI in the form of a string
    :return: A list of dictionaries of file metadata, incl urls
    """

    db = sqlite3.connect('idents_files_urls.sqlite')

    results = list()

    sha1_list = list(db.execute('SELECT * FROM files_id_doi WHERE doi = ?;', [the_doi]))

    for row in sha1_list:
        _, the_sha1, _ = row
        files_metadata_list = list(db.execute('SELECT * FROM files_metadata WHERE sha1 = ?;', [the_sha1]))
        _, mimetype, size_bytes, md5 = files_metadata_list[0]
        urls_list = list(db.execute('SELECT * FROM urls WHERE sha1 = ?;', [the_sha1]))
        results.append({
            'doi': the_doi,
            'urls': [archive_url(url) for url in urls_list],
            'mimetype': mimetype,
            'size_bytes': size_bytes,
            'md5': md5,
            })

    return results

# print(lookup_doi('10.1001/jama.2009.1064'))
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('hey I expected a single doi!!')
        sys.exit(-1)
    print(lookup_doi(sys.argv[1]))