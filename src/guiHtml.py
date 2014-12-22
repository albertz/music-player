
# HTML GUI

#def GuiObject

def main():
	
	import BaseHTTPServer
	class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
		def log_message(self, format, *args): pass
		
		def do_GET(self):
			print("GET: %s" % self.path)
			
			if self.path == "/":
				return self.returnMainPage()
			
			self.send_response(404)
			self.end_headers()

		def returnMainPage(self):
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(
				"""
				<html>
				<body>Hey there!</body>
				</html>
				"""
				)

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

	import main
	main.handleApplicationInit()

	try:
		while True:
			httpd.handle_request()
	except KeyboardInterrupt:
		raise SystemExit
	
def guiMain():
	pass


def dummyMainLoop():
	from State import state
	for ev,args,kwargs in state.updates.read():
		pass
