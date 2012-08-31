
from utils import *
import sys, os

noncanonicalStdinQueue = OnRequestQueue()

def readNextInput():
	ch = os.read(sys.stdin.fileno(),7)
	noncanonicalStdinQueue.put(ch)

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


from State import state


def handleInput(ch):
	if ch == "q" or ch == "\0":
		print "stdin: quit"
		state.quit()
	try:
		if ch == "\x1b[D": # left
			state.player.seekRel(-10)
		elif ch == "\x1b[C": #right
			state.player.seekRel(10)
		elif ch == "\n": # return
			state.player.nextSong()
		elif ch == " ":
			state.player.playing = not state.player.playing
	except:
		sys.excepthook(*sys.exc_info())

def stdinconsoleMain():
	# If we are a TTY, do some very simple input handling.
	if os.isatty(sys.stdin.fileno()):
		setTtyNoncanonical(sys.stdin.fileno())
	else:
		# don't do anything
		return

	#for ch in noncanonicalStdinQueue.read():
	while True:
		ch = os.read(sys.stdin.fileno(),7)
		handleInput(ch)
