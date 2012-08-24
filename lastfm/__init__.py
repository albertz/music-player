import appinfo
from . import client, rest, session

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
				if webself.path.startswith("/get_access_token?"):
					oself.httpd_access_token_callback = webself.path

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
			except: return False
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
			self.set_token(*stored_creds.split('|'))
			print "* loaded access token"
		except IOError:
			pass # don't worry if it's not there
	
	def write_creds(self, token):
		f = open(self.TOKEN_FILE, 'w')
		f.write("|".join([token.key, token.secret]))
		f.close()

	def delete_creds(self):
		os.unlink(self.TOKEN_FILE)

	def link(self):
		request_token = self.obtain_request_token()
		oauthreturnhandler = OAuthReturnHandler()

		url = self.build_authorize_url(
			request_token, oauth_callback = oauthreturnhandler.oauth_callback_url)
		
		print "* open oauth login page"
		import webbrowser; webbrowser.open(url)
		
		print "* waiting for redirect callback ...",
		httpd_access_token_callback = oauthreturnhandler.wait_callback_response()
		print "done"
	
		self.obtain_access_token(request_token)
		self.write_creds(self.token)
	
	def unlink(self):
		self.delete_creds()
		session.LastfmSession.unlink(self)

class Client:
	def __init__(self):
		self.sess = StoredSession(APP_KEY, APP_SECRET, access_type=ACCESS_TYPE)
		self.api_client = client.DropboxClient(self.sess)
		self.sess.load_creds()
		if not self.sess.is_linked():
			try:			
				self.sess.link()
			except rest.ErrorResponse, e:
				self.stdout.write('Error: %s\n' % str(e))
				raise

def onSongChange(newSong):
	pass

def onSongFinished(song):
	pass
