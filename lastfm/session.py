# code under public domain

"""
lastfm.session.LastfmSession is responsible for holding OAuth authentication info
(app key/secret, request key/secret,  access key/secret) as well as configuration information for your app
('app_folder' or 'lastfm' access type, optional locale preference). It knows how to
use all of this information to craft properly constructed requests to Lastfm.

A LastfmSession object must be passed to a lastfm.client.LastfmClient object upon
initialization.
"""
from __future__ import absolute_import

import random
import sys
import time
import urllib

try:
	from urlparse import parse_qs
except ImportError:
	# fall back for Python 2.5
	from cgi import parse_qs

from . import rest

class OAuthToken(object):
	__slots__ = ('key', 'secret')
	def __init__(self, key, secret):
		self.key = key
		self.secret = secret

# see http://www.last.fm/api/authentication
# see http://www.last.fm/api/desktopauth
# see http://www.last.fm/api/webauth

def build_api_sig(kwargs, api_secret):
	# kwargs e.g. contains api_key, method, token
	s = "".join([key + kwargs[key] for key in sorted(kwargs.keys())])
	s += api_secret
	from hashlib import md5
	return md5(s).hexdigest()

class LastfmSession(object):
	API_VERSION = "2.0"

	API_HOST = "ws.audioscrobbler.com"
	WEB_HOST = "www.last.fm"

	def __init__(self, consumer_key, consumer_secret, rest_client=rest.RESTClient):
		"""Initialize a LastfmSession object.

		Your consumer key and secret are available
		at http://www.last.fm/api/
		"""
		self.consumer_creds = OAuthToken(consumer_key, consumer_secret)
		self.token = None
		self.request_token = None
		self.rest_client = rest_client

	def is_linked(self):
		"""Return whether the LastfmSession has an access token attached."""
		return bool(self.token)

	def unlink(self):
		"""Remove any attached access token from the LastfmSession."""
		self.token = None

	def set_token(self, token):
		self.token = token

	def set_request_token(self, request_token, request_token_secret):
		"""Attach an request token to the LastfmSession.

		Note that the reuest 'token' is made up of both a token string
		and a secret string.
		"""
		self.request_token = OAuthToken(request_token, request_token_secret)

	def build_path(self, target, params=None, withVersion=True):
		"""Build the path component for an API URL.

		This method urlencodes the parameters, adds them
		to the end of the target url, and puts a marker for the API
		version in front.

		Args:
			target: A target url (e.g. '/files') to build upon.
			params: A dictionary of parameters (name to value). [optional]

		Returns:
			The path and parameters components of an API URL.
		"""
		if sys.version_info < (3,) and type(target) == unicode:
			target = target.encode("utf8")

		target_path = urllib.quote(target)

		params = params or {}
		params = params.copy()
				
		prefix = "/"
		if withVersion: prefix += self.API_VERSION		
		if params:
			return prefix + target_path + "?" + urllib.urlencode(params)
		else:
			return prefix + target_path

	def build_url(self, host, target, params=None):
		"""Build an API URL.

		This method adds scheme and hostname to the path
		returned from build_path.

		Args:
			target: A target url (e.g. '/files') to build upon.
			params: A dictionary of parameters (name to value). [optional]

		Returns:
			The full API URL.
		"""
		return "https://%s%s" % (host, self.build_path(target, params))

	def build_authorize_url(self, request_token, oauth_callback=None):
		"""Build a request token authorization URL.

		After obtaining a request token, you'll need to send the user to
		the URL returned from this function so that they can confirm that
		they want to connect their account to your app.

		Args:
			request_token: A request token from obtain_request_token.
			oauth_callback: A url to redirect back to with the authorized
				request token.

		Returns:
			An authorization for the given request token.
		"""
		params = {
			"api_key": self.consumer_creds.key,
			#'token': request_token, # if we don't provide this, Last.fm takes it as a webapp and uses the callback, otherwise it don't. our current way to return to our app is via the callback, so just leave this away
		}
		if oauth_callback:
			params['cb'] = oauth_callback
		params["api_sig"] = build_api_sig(params, self.consumer_creds.secret)

		return "https://%s%s" % (self.WEB_HOST, self.build_path("/api/auth/", params, withVersion=False))

	# http://www.last.fm/api/show/auth.getToken
	def obtain_request_token(self):
		"""Obtain a request token from the Lastfm API.

		This is your first step in the OAuth process.  You call this to get a
		request_token from the Lastfm server that you can then use with
		LastfmSession.build_authorize_url() to get the user to authorize it.
		After it's authorized you use this token with
		LastfmSession.obtain_access_token() to get an access token.

		NOTE:  You should only need to do this once for each user, and then you
		can store the access token for that user for later operations.

		Returns:
			An lastfm.session.OAuthToken representing the request token Lastfm assigned
			to this app. Also attaches the request token as self.request_token.
		"""
		self.token = None # clear any token currently on the request
		url = self.build_url(self.API_HOST, '/')
		params = {
			"method":"auth.getToken",
			}
		headers, params = self.build_access_headers(params, withSessionKey=False)
		
		response = self.rest_client.POST(url, headers=headers, params=params)
		self.request_token = response["token"]
		return self.request_token

	# http://www.last.fm/api/show/auth.getSession
	def obtain_access_token(self, request_token=None):
		"""Obtain an access token for a user.

		After you get a request token, and then send the user to the authorize
		URL, you can use the authorized request token with this method to get the
		access token to use for future operations. The access token is stored on
		the session object.

		Args:
			request_token: A request token from obtain_request_token. [optional]
				The request_token should have been authorized via the
				authorization url from build_authorize_url. If you don't pass
				a request_token, the fallback is self.request_token, which
				will exist if you previously called obtain_request_token on this
				LastfmSession instance.

		Returns:
			An tuple of (key, secret) representing the access token Lastfm assigned
			to this app and user. Also attaches the access token as self.token.
		"""
		request_token = request_token or self.request_token
		assert request_token, "No request_token available on the session. Please pass one."
		url = self.build_url(self.API_HOST, '/')
		params = {
			"method":"auth.getSession",
			"token":request_token,
			}
		headers, params = self.build_access_headers(params, withSessionKey=False)
		
		response = self.rest_client.POST(url, headers=headers, params=params)
		self.token = response["session"]["key"]
		self.user_name = response["session"]["name"]
		return self.token

	def build_access_headers(self, params=None, withSessionKey=True):
		params = params or {}
		params = params.copy()
		params["api_key"] = self.consumer_creds.key
		if withSessionKey:
			assert self.token
			params["sk"] = self.token
		params["api_sig"] = build_api_sig(params, self.consumer_creds.secret)
		params["format"] = "json"
		headers = {}
		return headers, params
		