
from utils import *
import sys, os

stdinQueue = OnRequestQueue()

def readNextInput():
	ch = os.read(sys.stdin.fileno(),7)
	stdinQueue.put(ch)

def setTtyNoncanonical(fd, timeout=0):
	import termios
	old = termios.tcgetattr(fd)
	new = termios.tcgetattr(fd)
	new[3] = new[3] & ~termios.ICANON & ~termios.ECHO
	# http://www.unixguide.net/unix/programming/3.6.2.shtml
	#new[6] [termios.VMIN] = 1
	#new[6] [termios.VTIME] = 0
	new[6] [termios.VMIN] = 0 if timeout > 0 else 1
	timeout *= 10 # 10ths of second
	if timeout > 0 and timeout < 1: timeout = 1
	new[6] [termios.VTIME] = timeout

	termios.tcsetattr(fd, termios.TCSANOW, new)
	termios.tcsendbreak(fd,0)


from State import state, reloadModules

def printState():
	if state.curSong:
		try:
			print os.path.basename(state.curSong.url) + " : " + \
				formatTime(state.player.curSongPos) + " / " + \
				formatTime(state.player.curSongLen)
		except:
			print "song ???"
	else:
		print "no song"

def handleInput(ch):
	if ch == "q" or ch == "\0" or ch == "":
		print "stdin: quit"
		state.quit()
	try:
		if ch == "\x1b[D": # left
			state.player.seekRel(-10)
			printState()
		elif ch == "\x1b[C": #right
			state.player.seekRel(10)
			printState()
		elif ch == "\n": # return
			state.nextSong()
		elif ch == " ":
			state.playPause()
		elif ch == "r":
			reloadModules()
	except:
		sys.excepthook(*sys.exc_info())

def stdinconsoleMain():
	fd = sys.stdin.fileno()
	if not os.isatty(fd): return # don't do anything

	import gui
	if hasattr(gui, "main"):
		# the GUI is handling the main thread.
		# it means we dont get stdinQueue updates here.
		# as we need a way to be able to cancel this,
		# we only can frequently check with a timeout here.
		setTtyNoncanonical(fd, timeout=1)

		from threading import currentThread
		thread = currentThread()
		print "stdin input ready"
		while not thread.cancel:
			ch = os.read(fd,7)
			if ch:
				handleInput(ch)

	else:
		# the main thread is pushing stdin updates to stdinQueue.
		setTtyNoncanonical(sys.stdin.fileno())
		print "stdin input ready"

		for ch in stdinQueue.read():
			handleInput(ch)
