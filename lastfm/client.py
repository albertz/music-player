# code under public domain

"""
The main client API you'll be working with most often.  You'll need to
configure a lastfm.session.LastfmSession for this to work, but otherwise
it's fairly self-explanatory.
"""
from __future__ import absolute_import

import re

try:
	import json
except ImportError:
	import simplejson as json

from .rest import ErrorResponse, RESTClient

def format_path(path):
	"""Normalize path for use with the Lastfm API.

	This function turns multiple adjacent slashes into single
	slashes, then ensures that there's a leading slash but
	not a trailing slash.
	"""
	if not path:
		return path

	path = re.sub(r'/+', '/', path)

	if path == '/':
		return (u"" if isinstance(path, unicode) else "")
	else:
		return '/' + path.strip('/')

# see http://www.last.fm/api/scrobbling

class LastfmClient(object):
	"""
	The main access point of doing REST calls on Lastfm. You should
	first create and configure a lastfm.session.LastfmSession object,
	and then pass it into LastfmClient's constructor. LastfmClient
	then does all the work of properly calling each API method
	with the correct OAuth authentication.

	You should be aware that any of these methods can raise a
	rest.ErrorResponse exception if the server returns a non-200
	or invalid HTTP response. Note that a 401 return status at any
	point indicates that the user needs to be reauthenticated.
	"""

	def __init__(self, session, rest_client=RESTClient):
		"""Initialize the LastfmClient object.

		Args:
			session: A lastfm.session.LastfmSession object to use for making requests.
			rest_client: A lastfm.rest.RESTClient-like object to use for making requests. [optional]
		"""
		self.session = session
		self.rest_client = rest_client

	def request(self, target, params=None, method='POST'):
		"""Make an HTTP request to a target API method.

		This is an internal method used to properly craft the url, headers, and
		params for a Lastfm API request.  It is exposed for you in case you
		need craft other API calls not in this library or if you want to debug it.

		Args:
			target: The target URL with leading slash (e.g. '/files')
			params: A dictionary of parameters to add to the request
			method: An HTTP method (e.g. 'GET' or 'POST')
			content_server: A boolean indicating whether the request is to the
			   API content server, for example to fetch the contents of a file
			   rather than its metadata.

		Returns:
			A tuple of (url, params, headers) that should be used to make the request.
			OAuth authentication information will be added as needed within these fields.
		"""
		assert method in ['GET','POST', 'PUT'], "Only 'GET', 'POST', and 'PUT' are allowed."
		if params is None:
			params = {}

		host = self.session.API_HOST
		base = self.session.build_url(host, target)
		headers, params = self.session.build_access_headers(params=params)

		if method in ('GET', 'PUT'):
			url = self.session.build_url(host, target, params)
		else:
			url = self.session.build_url(host, target)

		return url, params, headers

	# http://www.last.fm/api/show/track.updateNowPlaying
	def updateNowPlaying(self, artist, track, duration=None):
		params = {
			"method": "track.updateNowPlaying",
			"artist": artist,
			"track": track,
		}
		if duration and duration > 0:
			params["duration"] = str(int(duration))
		url, params, headers = self.request("/", method='POST', params=params)

		ret = self.rest_client.POST(url, headers=headers, params=params)
		#assert "error" not in ret
		return ret
        
	# http://www.last.fm/api/show/track.scrobble
	def scrobble(self, artist, track, duration=None, timestamp=None):
		if not timestamp:
			import time
			timestamp = int(time.time())
			if duration: timestamp -= duration
			else: timestamp -= 5*60 # assume the song was 5min long
		timestamp = str(int(timestamp))
		params = {
			"method": "track.scrobble",
			"artist": artist,
			"track": track,
			"timestamp": timestamp,
		}
		if duration:
			params["duration"] = str(int(duration))
		url, params, headers = self.request("/", method='POST', params=params)

		ret = self.rest_client.POST(url, headers=headers, params=params)
		#assert "error" not in ret
		return ret
