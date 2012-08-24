"""
A simple JSON REST request abstraction layer that is used by the
dropbox.client and dropbox.session modules. You shouldn't need to use this.
"""

import httplib
import os
import re
import socket
import ssl
import sys
import urllib
import urlparse

mydir = os.path.dirname(__file__)

try:
    import json
except ImportError:
    import simplejson as json

SDK_VERSION = "1.4.1"

TRUSTED_CERT_FILE = mydir + '/trusted-certs.crt'

class ProperHTTPSConnection(httplib.HTTPConnection):
    """
    httplib.HTTPSConnection is broken because it doesn't do server certificate
    validation.  This class does certificate validation by ensuring:
       1. The certificate sent down by the server has a signature chain to one of
          the certs in our 'trusted-certs.crt' (this is mostly handled by the 'ssl'
          module).
       2. The hostname in the certificate matches the hostname we're connecting to.
    """

    def __init__(self, host, port, trusted_cert_file=TRUSTED_CERT_FILE):
        httplib.HTTPConnection.__init__(self, host, port)
        self.ca_certs = trusted_cert_file
        self.cert_reqs = ssl.CERT_REQUIRED

    def connect(self):
        sock = create_connection((self.host, self.port))
        self.sock = ssl.wrap_socket(sock, cert_reqs=self.cert_reqs, ca_certs=self.ca_certs)
        cert = self.sock.getpeercert()
        hostname = self.host.split(':', 0)[0]
        match_hostname(cert, hostname)

class CertificateError(ValueError):
    pass

def _dnsname_to_pat(dn):
    pats = []
    for frag in dn.split(r'.'):
        if frag == '*':
            # When '*' is a fragment by itself, it matches a non-empty dotless
            # fragment.
            pats.append('[^.]+')
        else:
            # Otherwise, '*' matches any dotless fragment.
            frag = re.escape(frag)
            pats.append(frag.replace(r'\*', '[^.]*'))
    return re.compile(r'\A' + r'\.'.join(pats) + r'\Z', re.IGNORECASE)

# This was ripped from Python 3.2 so it's not tested
def match_hostname(cert, hostname):
    """Verify that *cert* (in decoded format as returned by
    SSLSocket.getpeercert()) matches the *hostname*.  RFC 2818 rules
    are mostly followed, but IP addresses are not accepted for *hostname*.

    CertificateError is raised on failure. On success, the function
    returns nothing.
    """
    if not cert:
        raise ValueError("empty or no certificate")
    dnsnames = []
    san = cert.get('subjectAltName', ())
    for key, value in san:
        if key == 'DNS':
            if _dnsname_to_pat(value).match(hostname):
                return
            dnsnames.append(value)
    if not san:
        # The subject is only checked when subjectAltName is empty
        for sub in cert.get('subject', ()):
            for key, value in sub:
                # XXX according to RFC 2818, the most specific Common Name
                # must be used.
                if key == 'commonName':
                    if _dnsname_to_pat(value).match(hostname):
                        return
                    dnsnames.append(value)
    if len(dnsnames) > 1:
        raise CertificateError("hostname %r doesn't match either of %s" % (hostname, ', '.join(map(repr, dnsnames))))
    elif len(dnsnames) == 1:
        raise CertificateError("hostname %r doesn't match %r" % (hostname, dnsnames[0]))
    else:
        raise CertificateError("no appropriate commonName or subjectAltName fields were found")

def create_connection(address):
    host, port = address
    err = None
    for res in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        sock = None
        try:
            sock = socket.socket(af, socktype, proto)
            sock.connect(sa)
            return sock

        except socket.error, _:
            err = _
            if sock is not None:
                sock.close()

    if err is not None:
        raise err
    else:
        raise socket.error("getaddrinfo returns an empty list")

def json_loadb(data):
    if sys.version_info >= (3,):
        data = data.decode('utf8')
    return json.loads(data)

class RESTClientObject(object):
    def __init__(self, http_connect=None):
        self.http_connect = http_connect

    def request(self, method, url, post_params=None, body=None, headers=None, raw_response=False):
        post_params = post_params or {}
        headers = headers or {}
        headers['User-Agent'] = 'OfficialDropboxPythonSDK/' + SDK_VERSION

        if post_params:
            if body:
                raise ValueError("body parameter cannot be used with post_params parameter")
            body = urllib.urlencode(post_params)
            headers["Content-type"] = "application/x-www-form-urlencoded"

        # maintain dynamic lookup of ProperHTTPConnection
        http_connect = self.http_connect
        if http_connect is None:
            http_connect = ProperHTTPSConnection

        host = urlparse.urlparse(url).hostname
        conn = http_connect(host, 443)

        try:

            # This code is here because httplib in pre-2.6 Pythons
            # doesn't handle file-like objects as HTTP bodies and
            # thus requires manual buffering
            if not hasattr(body, 'read'):
                conn.request(method, url, body, headers)
            else:

                #We need to get the size of what we're about to send for the Content-Length
                #Must support len() or have a len or fileno(), otherwise we go back to what we were doing!
                clen = None

                try:
                    clen = len(body)
                except (TypeError, AttributeError):
                    try:
                        clen = body.len
                    except AttributeError:
                        try:
                            clen = os.fstat(body.fileno()).st_size
                        except AttributeError:
                            # fine, lets do this the hard way
                            # load the whole file at once using readlines if we can, otherwise
                            # just turn it into a string
                            if hasattr(body, 'readlines'):
                                body = body.readlines()
                            conn.request(method, url, str(body), headers)

                if clen != None:  #clen == 0 is perfectly valid. Must explicitly check for None
                    clen = str(clen)
                    headers["Content-Length"] = clen
                    conn.request(method, url, "", headers)
                    BLOCKSIZE = 4096 #4MB buffering just because

                    data=body.read(BLOCKSIZE)
                    while data:
                        conn.send(data)
                        data=body.read(BLOCKSIZE)

        except socket.error, e:
            raise RESTSocketError(host, e)
        except CertificateError, e:
            raise RESTSocketError(host, "SSL certificate error: " + e)

        r = conn.getresponse()
        if r.status != 200:
            raise ErrorResponse(r)

        if raw_response:
            return r
        else:
            try:
                resp = json_loadb(r.read())
            except ValueError:
                raise ErrorResponse(r)
            finally:
                conn.close()

        return resp

    def GET(self, url, headers=None, raw_response=False):
        assert type(raw_response) == bool
        return self.request("GET", url, headers=headers, raw_response=raw_response)

    def POST(self, url, params=None, headers=None, raw_response=False):
        assert type(raw_response) == bool
        if params is None:
            params = {}

        return self.request("POST", url,
                            post_params=params, headers=headers, raw_response=raw_response)

    def PUT(self, url, body, headers=None, raw_response=False):
        assert type(raw_response) == bool
        return self.request("PUT", url, body=body, headers=headers, raw_response=raw_response)

class RESTClient(object):
    IMPL = RESTClientObject()

    """
    An class with all static methods to perform JSON REST requests that is used internally
    by the Dropbox Client API. It provides just enough gear to make requests
    and get responses as JSON data (when applicable). All requests happen over SSL.
    """

    @classmethod
    def request(cls, *n, **kw):
        """Perform a REST request and parse the response.

        Args:
            method: An HTTP method (e.g. 'GET' or 'POST').
            url: The URL to make a request to.
            post_params: A dictionary of parameters to put in the body of the request.
                This option may not be used if the body parameter is given.
            body: The body of the request. Typically, this value will be a string.
                It may also be a file-like object in Python 2.6 and above. The body
                parameter may not be used with the post_params parameter.
            headers: A dictionary of headers to send with the request.
            raw_response: Whether to return the raw httplib.HTTPReponse object. [default False]
                It's best enabled for requests that return large amounts of data that you
                would want to .read() incrementally rather than loading into memory. Also
                use this for calls where you need to read metadata like status or headers,
                or if the body is not JSON.

        Returns:
            The JSON-decoded data from the server, unless raw_response is
            specified, in which case an httplib.HTTPReponse object is returned instead.

        Raises:
            dropbox.rest.ErrorResponse: The returned HTTP status is not 200, or the body was
                not parsed from JSON successfully.
            dropbox.rest.RESTSocketError: A socket.error was raised while contacting Dropbox.
        """
        return cls.IMPL.request(*n, **kw)

    @classmethod
    def GET(cls, *n, **kw):
        """Perform a GET request using RESTClient.request"""
        return cls.IMPL.GET(*n, **kw)

    @classmethod
    def POST(cls, *n, **kw):
        """Perform a POST request using RESTClient.request"""
        return cls.IMPL.POST(*n, **kw)

    @classmethod
    def PUT(cls, *n, **kw):
        """Perform a PUT request using RESTClient.request"""
        return cls.IMPL.PUT(*n, **kw)

class RESTSocketError(socket.error):
    """
    A light wrapper for socket.errors raised by dropbox.rest.RESTClient.request
    that adds more information to the socket.error.
    """

    def __init__(self, host, e):
        msg = "Error connecting to \"%s\": %s" % (host, str(e))
        socket.error.__init__(self, msg)

class ErrorResponse(Exception):
    """
    Raised by dropbox.rest.RESTClient.request for requests that:
    - Return a non-200 HTTP response, or
    - Have a non-JSON response body, or
    - Have a malformed/missing header in the response.

    Most errors that Dropbox returns will have a error field that is unpacked and
    placed on the ErrorResponse exception. In some situations, a user_error field
    will also come back. Messages under user_error are worth showing to an end-user
    of your app, while other errors are likely only useful for you as the developer.
    """

    def __init__(self, http_resp):
        self.status = http_resp.status
        self.reason = http_resp.reason
        self.body = http_resp.read()
        self.headers = http_resp.getheaders()

        try:
            body = json_loadb(self.body)
            self.error_msg = body.get('error')
            self.user_error_msg = body.get('user_error')
        except ValueError:
            self.error_msg = None
            self.user_error_msg = None

    def __str__(self):
        if self.user_error_msg and self.user_error_msg != self.error_msg:
            # one is translated and the other is English
            msg = "%s (%s)" % (self.user_error_msg, self.error_msg)
        elif self.error_msg:
            msg = self.error_msg
        elif not self.body:
            msg = self.reason
        else:
            msg = "Error parsing response body or headers: " +\
                  "Body - %s Headers - %s" % (self.body, self.headers)

        return "[%d] %s" % (self.status, repr(msg))

