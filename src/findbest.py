
# -*- coding: utf-8 -*-

import songdb
import os
import appinfo


def search(s):
	songs = songdb.search(s)
	songs = [s for s in songs if s.get("rating",0) > 0]
	songs.sort(lambda s1,s2: s1.get("rating") > s2.get("rating"))
	return ["%s - %s" % (s["artist"], s["title"]) for s in songs]


def all_in_subdir(path):
	assert os.path.isdir(path), "%r must be a directory" % path
	ls = []
	for fn in os.listdir(path):
		fullfn = path + "/" + fn
		if os.path.isfile(fullfn):
			ext = os.path.splitext(fn)[1].lower()
			if ext[:1] == ".": ext = ext[1:]
			if ext in appinfo.formats:
				ls.append({"url": fullfn})
		elif os.path.isdir(fullfn):
			ls += all_in_subdir(fullfn)
	return ls


def _resolve_txt_song(txt, single=True):
	songs = songdb.search(txt)
	if songs:
		if len(songs) == 1:
			return songs
		songs.sort(lambda s1,s2: s1.get("rating", 0) > s2.get("rating", 0))
		if single:
			return songs[:1]
		rated_songs = [s for s in songs if s.get("rating",0) > 0]
		if rated_songs:
			return rated_songs
		return songs
	return []

def resolve_txt_song(txt, single=True):
	songs = _resolve_txt_song(txt, single=single)
	if songs: return songs
	for c in "[]()<>+-*/^!\"'$%&=?#_.:,;´`°€@":
		txt = txt.replace(c, " ")
	songs = _resolve_txt_song(txt, single=single)
	if songs: return songs
	txtparts = txt.split()
	for i in range(len(txtparts), 0, -1):
		songs = _resolve_txt_song(" ".join(txtparts[:i]), single=single)
		if songs: return songs
		songs = _resolve_txt_song(" ".join(txtparts[:i]) + "*", single=single)
		if songs: return songs
	return []


def resolve_txt_playlist(ls, single=True):
	assert isinstance(ls, list), "list expected but got type %r" % type(ls)
	all_songs = []
	for txt in ls:
		songs = resolve_txt_song(txt, single=single)
		assert songs, "Did not find anything for %r" % txt
		all_songs += songs
	return songs
