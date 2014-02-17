# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

# This is a simple interface to Last.fm, based on the web API: http://www.last.fm/api/
# Some other implementations of a Last.fm scrobbler can be seen here:
# Amarok:
#  * source: https://github.com/orangejulius/amarok/blob/master/src/services/lastfm/LastFmService.cpp
#  * uses liblastfm
# Songbird:
#  * source: https://github.com/ianloic/songbird-lastfm/blob/master/components/sbLastFm.js
#  * JS source, uses the web API

import appinfo
from . import client, rest, session
import ssl

# i don't really know how to make these secure...
APP_KEY = '29d301e504af323d6246d9c652c227fa'
APP_SECRET = '781bca4d222866e27ac314c2e35565a0'


class OAuthReturnHandler:
	def __init__(oself):
		oself.httpd_access_token_callback = None
		
		import BaseHTTPServer
		class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
			def log_message(self, format, *args): pass
			def do_GET(webself):
				pathStart = "/get_access_token?"
				if webself.path.startswith(pathStart):
					oself.httpd_access_token_callback = webself.path[len(pathStart):]

					webself.send_response(200)
					webself.send_header("Content-type", "text/html")
					webself.end_headers()
					webself.wfile.write("""
						<html><head><title>OAuth return</title></head>
						<body onload="onLoad()">
						<script type="text/javascript">
						function onLoad() {
							ww = window.open(window.location, "_self");
							ww.close();
						}
						</script>
						</body></html>""")
				else:
					webself.send_response(404)
					webself.end_headers()

		oself.handler = Handler		
		def tryOrFail(fn):
			try: fn(); return True
			except Exception: return False
		# Try with some default ports first to avoid cluttering the users Google Authorized Access list.
		tryOrFail(lambda: oself.startserver(port = 8123)) or \
		tryOrFail(lambda: oself.startserver(port = 8321)) or \
		oself.startserver(port = 0)

		_,oself.port = oself.httpd.server_address
		oself.oauth_callback_url = "http://localhost:%d/get_access_token" % oself.port

	def startserver(self, port):
		import BaseHTTPServer
		self.httpd = BaseHTTPServer.HTTPServer(("", port), self.handler)

	def wait_callback_response(self):
		while self.httpd_access_token_callback == None:
			self.httpd.handle_request()
		return self.httpd_access_token_callback

class StoredSession(session.LastfmSession):
	"""a wrapper around LastfmSession that stores a token to a file on disk"""
	TOKEN_FILE = appinfo.userdir + "/lastfm_session_token_store.txt"
	
	def load_creds(self):
		try:
			stored_creds = open(self.TOKEN_FILE).read()
			self.set_token(stored_creds)
			print "Last.fm: loaded access token"
		except IOError:
			pass # don't worry if it's not there
	
	def write_creds(self, token):
		f = open(self.TOKEN_FILE, 'w')
		f.write(token)
		f.close()

	def delete_creds(self):
		import os
		try:
			os.unlink(self.TOKEN_FILE)
		except OSError:
			# file does not exist or so. ignore
			pass

	def link(self):
		#request_token = self.obtain_request_token()
		oauthreturnhandler = OAuthReturnHandler()

		#url = self.build_authorize_url(
		#	request_token, oauth_callback = oauthreturnhandler.oauth_callback_url)
		
		url = self.build_authorize_url(
			None, oauth_callback = oauthreturnhandler.oauth_callback_url)
		
		print "Last.fm: open oauth login page"
		import webbrowser; webbrowser.open(url)
		
		print "Last.fm: waiting for redirect callback ...",
		httpd_access_token_callback = oauthreturnhandler.wait_callback_response()
		print "Last.fm: done login"
		from urlparse import parse_qs
		token = parse_qs(httpd_access_token_callback)
		token = token["token"][0]

		print "Last.fm: obtain access token ..."
		self.obtain_access_token(token)
		print "Last.fm: write final credentials"
		self.write_creds(self.token)
	
	def unlink(self):
		self.delete_creds()
		session.LastfmSession.unlink(self)


class Client:
	def __init__(self):		
		self.sess = StoredSession(APP_KEY, APP_SECRET)
		self.api_client = client.LastfmClient(self.sess)
		self.sess.load_creds()

	@staticmethod
	def doWebAction(action):
		import threading, time
		curThread = threading.currentThread()
		lastExcType = None
		while True:
			if getattr(curThread, "cancel", False):
				raise KeyboardInterrupt
			try:
				return action()
			except rest.ErrorResponse as exc:
				print "Last.fm error: ErrorResponse %d" % exc.status
				# last.fm server busy or so
				# wait a bit and retry
				time.sleep(1)
			except (rest.RESTSocketError, ssl.SSLError) as exc:
				# maybe no internet connection or timeout or so
				# dont print an error if same exc, dont spam
				if type(exc) is not lastExcType:
					lastExcType = type(exc)
					print "Last.fm connection error:", exc
					import sys
					sys.excepthook(*sys.exc_info())
				# wait a bit and retry
				time.sleep(1)
			except Exception:
				import sys
				sys.excepthook(*sys.exc_info())
				# wait a bit and retry
				time.sleep(1)
		
	def login(self):
		def action():
			if self.sess.is_linked(): return True
			self.sess.link()
			return self.sess.is_linked()
		return self.doWebAction(action)

	def apiCall(self, apiFuncName, **kwargs):
		assert self.sess.is_linked()
		#print "lastfm", apiFuncName, kwargs
		
		def action():
			f = getattr(_client.api_client, apiFuncName)
			ret = f(**kwargs)
			assert ret is not None # either we get sth or we raise some exception
			if "error" in ret:
				print "Last.fm API", apiFuncName, kwargs, "returned error", ret
				# This is an API error, we would very likely get the same error again, so just stop
				return
			return ret
		return self.doWebAction(action)
		
_client = None

def login():
	global _client
	_client = Client()
	_client.login()

def quit():
	global _client
	if not _client: return
	_client = None
	
def onSongChange(newSong):
	if not _client: return
	_client.apiCall(
		"updateNowPlaying",
		artist=newSong.artist.encode("utf-8"),
		track=newSong.title.encode("utf-8"),
		duration=newSong.duration
	)
	
def onSongFinished(song, timestamp):
	if not _client: return
	_client.apiCall(
		"scrobble",
		artist=song.artist.encode("utf-8"),
		track=song.title.encode("utf-8"),
		duration=song.duration,
		timestamp=timestamp
	)

