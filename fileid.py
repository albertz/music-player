# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2013, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

# Get some native file-id handle which is persistent from file-moves.

import os, sys
import utils

if sys.platform == "darwin" and utils.isPymoduleAvailable("AppKit"):

	import AppKit
	
	def getFileNativeId(filepath):
		if not os.path.isfile(filepath): return None
		filepath = os.path.abspath(filepath)
		filepath = unicode(filepath)
		
		url = AppKit.NSURL.alloc().initFileURLWithPath_(filepath)	
		
		bookmark = url.bookmarkDataWithOptions_includingResourceValuesForKeys_relativeToURL_error_(AppKit.NSURLBookmarkCreationPreferFileIDResolution,None,None,None)
		bytes = bookmark[0].bytes().tobytes()
		
		return bytes

	def getPathByNativeId(fileid):
		nsdata = AppKit.NSData.alloc().initWithBytes_length_(fileid, len(fileid))
		url, _, _ = AppKit.NSURL.URLByResolvingBookmarkData_options_relativeToURL_bookmarkDataIsStale_error_(nsdata, AppKit.NSURLBookmarkResolutionWithoutUI, None,None,None)
		
		if not url: return None
		
		return unicode(url.path())

else:
	
	def getFileNativeId(filepath): return None
	def getPathByNativeId(fileid): return None

