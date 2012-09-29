
# returns None or realnum in [0,1]
def getRating(filename, default=None):
	try:
		# for now, we just have iTunes
		import itunes
		return itunes.ratings.get(filename, default)
	except:
		import sys
		sys.excepthook(*sys.exc_info())
	return 0.0
