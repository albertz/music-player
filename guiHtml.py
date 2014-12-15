
# HTML GUI


def main():
	
	import BaseHTTPServer
	class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
		def log_message(self, format, *args): pass
		def do_GET(webself):
			print("GET: %s" % webself.path)
			webself.send_response(404)
			webself.end_headers()

	def startServer(port = 0):
		import BaseHTTPServer
		return BaseHTTPServer.HTTPServer(("", port), Handler)
	
	def tryOrFail(fn):
		try: return fn()
		except Exception: return

	# Try with some default ports first.
	httpd = \
		tryOrFail(lambda: startServer(port = 9123)) or \
		tryOrFail(lambda: startServer(port = 9321)) or \
		startServer()

	_,port = httpd.server_address
	
	import webbrowser
	webbrowser.open("http://localhost:%i" % port)

	while True:
		httpd.handle_request()
	
def guiMain():
	pass


def dummyMainLoop():
	from State import state
	for ev,args,kwargs in state.updates.read():
		pass
