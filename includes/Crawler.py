import logging
import urllib
import urllib2
import cookielib

logger = logging.getLogger()


class Crawler(object):
    """
    Crawls the web while keeping cookies in a temporary jar.
    """
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'

    def __init__(self):
        self.cookie_jar = cookielib.LWPCookieJar()
        cookie_handler = urllib2.HTTPCookieProcessor(self.cookie_jar)
        self.opener = urllib2.build_opener(cookie_handler)

    def request(self, url, data=None, headers=None):
        headers = headers or {}
        headers['User-Agent'] = self.user_agent
        if data is not None:
            data = urllib.urlencode(data)
            headers['Content-type'] = 'application/x-www-form-urlencoded'
        self.opener.addheaders = headers.items()
        logger.debug('Requesting %s', url)
        response = self.opener.open(url, data)
        return response

    def ajax(self, url, data=None, headers=None):
        headers = headers or {}
        headers['X-Requested-With'] = 'XMLHttpRequest'
        return self.request(url, data, headers)
