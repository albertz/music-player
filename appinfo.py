import sys, os

progname = "MusicPlayer"
appid = "com.albertzeyer." + progname
version = "1.0"

userdir = "~/." + appid
platform = None

uname = os.uname()
if "iPhone" in uname[4] or "iPod" in uname[4]:
	userdir = "~/Library/" + progname
	platform = "iOS"	
elif sys.platform == "darwin":
	userdir = "~/Library/Application Support/" + appid
	platform = "MacOSX"
elif sys.platform == "win32":
	from win32com.shell import shellcon, shell
	userdir = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0) + "/" + progname
	platform = "Win32"
else:
	print "warning: unknown/untested platform", repr(sys.platform)

userdir = os.path.expanduser(userdir)
musicdir = os.path.expanduser("~/Music")
formats = ("mp3", "ogg", "flac", "wma")
musicdatabase = userdir + "/songs.sqlite"

try: os.makedirs(userdir)
except: pass
