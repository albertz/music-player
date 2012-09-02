
import itunes

# returns None or realnum in [0,1]
def getRating(filename, default=None):
	# for now, we just have iTunes
	return itunes.ratings.get(filename, default)
