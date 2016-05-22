
import songdb

def search(s):
	songs = songdb.search(s)
	songs = [s for s in songs if s.get("rating",0) > 0]
	songs.sort(lambda s1,s2: s1.get("rating") > s2.get("rating"))
	return ["%s - %s" % (s["artist"], s["title"]) for s in songs]
