
from utils import UserAttrib, Event, initBy, safe_property
import Traits


class Preferences(object):
	def __init__(self):
		self._sampleRateStr = None
		self.lastFm_update(self.__class__.lastFm)

	@UserAttrib(type=Traits.OneLineText, autosizeWidth=True)
	@safe_property
	@property
	def sampleRateLabel(self):
		return "Sample rate in Hz:"

	@property
	def _sampleRate(self):
		from State import state
		return state.player.outSamplerate

	@UserAttrib(type=Traits.EditableText,
		alignRight=True, variableWidth=True,
		width=200 # this forces a min-width
		)
	def sampleRate(self, updateText=None):
		if updateText is not None and self._sampleRateStr != updateText:
			self._sampleRateStr = updateText
		if self._sampleRateStr is not None:
			return self._sampleRateStr
		rate = str(self._sampleRate)
		if rate[-3:] == "000": rate = rate[:-3] + "k"
		return rate

	@sampleRate.setUpdateEvent
	@initBy
	def sampleRate_updateEvent(self): return Event()

	@UserAttrib(type=Traits.Action, name="apply", alignRight=True, variableWidth=False)
	def applySampleRate(self):
		self.sampleRate_updateEvent.push()

		self._sampleRateStr, rate = None, self._sampleRateStr
		if rate is None: return
		if rate[-1:] == "k": rate = rate[:-1] + "000"
		try: rate = int(rate)
		except Exception: return # no valid integer

		# do some very basic check on the number.
		# later, our ffmpeg module should allow us to check this.
		if rate in (44100,48000,88200,96000,176400,192000): pass
		else: return

		from State import state
		state.player.playing = False # can only change that when not playing
		state.player.outSamplerate = rate

		from appinfo import config
		config.sampleRate = rate
		config.save()

	def lastFm_update(self, attrib):
		from appinfo import config
		if config.lastFm:
			attrib.name = "Last.fm is enabled. Disable it."
		else:
			attrib.name = "Last.fm is disabled. Enable it."

	@UserAttrib(type=Traits.Action, updateHandler=lastFm_update, variableWidth=False)
	def lastFm(self):
		self.lastFm_updateEvent.push()

		from appinfo import config
		config.lastFm = not config.lastFm
		config.save()

		from State import getModule
		getModule("tracker_lastfm").reload()

	@lastFm.setUpdateEvent
	@initBy
	def lastFm_updateEvent(self): return Event()

	@UserAttrib(type=Traits.Action, alignRight=True, name="reset Last.fm login", variableWidth=False)
	def resetLastFm(self):
		import lastfm, os, sys
		try:
			os.remove(lastfm.StoredSession.TOKEN_FILE)
		except Exception:
			sys.excepthook(*sys.exc_info())

prefs = Preferences()

