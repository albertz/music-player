# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.
import sys, os

progname = "MusicPlayer"
appid = "com.albertzeyer." + progname
version = "1.0"

try:
	from appinfo_build import *
except ImportError:
	buildTime = "<unknown>"
	gitRef = "<unknown>"

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
elif sys.platform == "linux2":
	platform = "Linux"
else:
	print "warning: unknown/untested platform", repr(sys.platform)

userdir = os.path.expanduser(userdir)
formats = ["mp3", "ogg", "flac", "wma", "m4a"]
musicdatabase = userdir + "/songs.sqlite"
musicdirs = (os.path.expanduser("~/Music"),)


try: os.makedirs(userdir)
except: pass


import utils

class Config:
	lastFm = True
	def __init__(self, **kwargs):
		for k in dir(self):
			if k.startswith("_"): continue
			setattr(self, k, getattr(self, k)) # to have it in own dict
		for k,v in kwargs.items():
			setattr(self, k, v)
	def __repr__(self):
		return "Config(**%s)" % utils.betterRepr(self.__dict__)

config = utils.PersistentObject(Config, "main.cfg")
config.save()


import sys
if not getattr(sys, "argv", None):
	sys.argv = ["."] # foo... constructor of ArgumentParser needs that

from appinfo_args import argParser
args = argParser.parse_args()

