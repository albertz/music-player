
# -*- coding: utf-8 -*-

import songdb
import os
import appinfo
from Song import Song


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
	return all_songs


def _intelli_resolve_song(obj):
	if isinstance(obj, Song):
		return {"url": obj.url, "id": obj.id}
	if isinstance(obj, (str, unicode)):
		if os.path.exists(obj):
			return {"url": obj}
		song_filename_by_id = songdb.getSongFilenameById(obj)
		if song_filename_by_id:
			return {"url": song_filename_by_id, "id": obj}
		songs = resolve_txt_song(obj, single=True)
		assert songs, "Did not find song %r" % obj
		obj = songs[0]
	assert isinstance(obj, dict), "Expected dict but got %r" % obj
	obj = obj.copy()
	if "url" in obj:
		if os.path.exists(obj["url"]):
			if "id" in obj: return {"url": obj["url"], "id": obj["id"]}
			return {"url": obj["url"]}
		if "id" not in obj:
			song_id = songdb.getSongId_viaUrl(obj["url"])
			obj["id"] = song_id
	if "id" in obj:
		song_filename_by_id = songdb.getSongFilenameById(obj["id"])
		assert song_filename_by_id, "Song id %r is invalid in %r" % (obj["id"], obj)
		assert os.path.exists(song_filename_by_id), "Unexpected non-existing song %r" % song_filename_by_id
		return {"url": song_filename_by_id, "id": obj["id"]}
	assert False, "Cannot resolve song %r" % obj


def playlist_add_top(sth, index=0):
	if isinstance(sth, list):
		for i, s in enumerate(sth):
			playlist_add_top(s, index=i)
		return
	song = _intelli_resolve_song(sth)
	from State import state
	state.queue.queue.insert(index, Song(**song))

def playlist_add_bottom(sth):
	if isinstance(sth, list):
		for s in sth:
			playlist_add_bottom(s)
		return
	song = _intelli_resolve_song(sth)
	from State import state
	state.queue.queue.append(Song(**song))


playlist_dir = appinfo.userdir + "/playlists"
playlist_types = [".m3u", ".musicplayer-playlist"]

def playlist_exported_lists(path=None):
	if not path: path = playlist_dir
	if not os.path.isdir(playlist_dir): return []
	ls = []
	for fn in os.listdir(path):
		fullfn = path + "/" + fn
		if os.path.isfile(fullfn):
			ext = os.path.splitext(fn)[1].lower()
			if ext in playlist_types:
				if fullfn.startswith("%s/" % playlist_dir):
					ls.append(fullfn[len(playlist_dir) + 1:])
				else:
					ls.append(fullfn)
				ls.append(os.path.relpath(fullfn, ))
		elif os.path.isdir(fullfn):
			ls += playlist_exported_lists(fullfn)
	return ls

def playlist_clear():
	from State import state
	state.queue.queue.clear()

def playlist_import(path):
	assert isinstance(path, (str, unicode))
	if not path.startswith("/"):
		path = "%s/%s" % (playlist_dir, path)
	if not os.path.splitext(path)[1]:
		path += ".m3u"
	assert os.path.exists(path), "Playlist not found: %r" % path
	if path.endswith(".m3u"):
		urls = []
		ls = open(path).read().splitlines()
		for url in ls:
			url = url.strip()
			if not url: continue
			if url[:1] == "#": continue
			if not url.startswith("/"):
				url = "%s/%s" % (os.path.dirname(path), url)
			urls.append(url)
		playlist_add_bottom(urls)
	elif path.endswith(".txt"):
		ls = open(path).read().splitlines()
		songs = map(_intelli_resolve_song, ls)
		playlist_add_bottom(songs)
	else:
		assert False, "not handled file format: %r" % path

def playlist_list_urls():
	from State import state
	queue = state.queue.queue
	ls = []
	with queue.lock:
		n = len(queue)
		for i in range(n):
			ls.append(queue[i])
	return [song.url for song in ls]

def playlist_export(path):
	assert isinstance(path, (str, unicode))
	if not path.startswith("/"):
		if not os.path.isdir(playlist_dir):
			os.makedirs(playlist_dir)
		path = "%s/%s" % (playlist_dir, path)
	if not os.path.splitext(path)[1]:
		path += ".m3u"
	from State import state
	queue = state.queue.queue
	ls = []
	with queue.lock:
		n = len(queue)
		for i in range(n):
			ls.append(queue[i])
	if path.endswith(".m3u"):
		f = open(path, "wb")
		f.write("#EXTM3U\n")
		for song in ls:
			f.write("#%s:id=%s\n" % (appinfo.appid, repr(song.id)))
			f.write("#EXTINF:%i,%s - %s\n" % (song.duration, song.artist.encode("utf8"), song.title.encode("utf8")))
			f.write("%s\n" % song.url.encode("utf8"))
		f.close()
	else:
		assert False, "not handled file format: %r" % path
