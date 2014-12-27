
from collections import deque
from threading import RLock, Condition, currentThread
import sys
import time


class OnRequestQueue:
	ListUsedModFunctions = ("append", "popleft")
	class QueueEnd:
		def __init__(self, queueList=None):
			if queueList is not None:
				self.q = queueList
			else:
				self.q = deque()
			self.cond = Condition()
			self.cancel = False
		def __repr__(self):
			with self.cond:
				return "<QueueEnd %r>" % self.q
		def put(self, item):
			with self.cond:
				if self.cancel: return False
				self.q.append(item)
				self.cond.notifyAll()
		def setCancel(self):
			with self.cond:
				self.cancel = True
				self.cond.notifyAll()
	def __init__(self):
		self.queues = set()
	def put(self, item):
		for q in list(self.queues):
			q.put(item)
	def cancelAll(self):
		for q in list(self.queues):
			q.setCancel()
	def read(self, *otherQueues, **kwargs):
		q = self.QueueEnd(**kwargs)
		thread = currentThread()
		thread.waitQueue = q
		if thread.cancel:
			# This is to avoid a small race condition for the case
			# that the thread which wants to join+cancel us was faster
			# and didn't got the waitQueue. In that case, it would
			# have set the cancel already to True.
			return
		for reqqu in otherQueues: assert(isinstance(reqqu, OnRequestQueue))
		reqQueues = (self,) + otherQueues
		for reqqu in reqQueues: reqqu.queues.add(q)
		while True:
			with q.cond:
				# Note on cancel-behavior:
				# Earlier, we always still yielded all left items in the queue
				# before breaking out here. This behavior doesn't fit if you
				# want to cancel as fast as possible and when you have a
				# persistent queue anyway - while you might hang at some entry.
				if q.cancel: break
				l = list(q.q)
				if not l:
					q.cond.wait()
			for item in l:
				if q.cancel: break
				yield item
				with q.cond:
					popitem = q.q.popleft()
					assert popitem is item
		for reqqu in reqQueues: reqqu.queues.remove(q)

class EventCallback:
	def __init__(self, targetQueue, name=None, reprname=None, extraCall=None):
		self.targetQueue = targetQueue
		self.name = name
		self.reprname = reprname
		self.extraCall = extraCall
	def __call__(self, *args, **kwargs):
		if not "timestamp" in kwargs:
			kwargs["timestamp"] = time.time()
		if self.extraCall:
			self.extraCall(*args, **kwargs)
		self.targetQueue.put((self, args, kwargs))
	def __repr__(self):
		if self.reprname:
			return self.reprname
		else:
			return "<EventCallback %s>" % self.name

class Event:
	def __init__(self):
		self.lock = RLock()
		self.targets = []
	def push(self, *args):
		with self.lock:
			targets = self.targets
			for weakt in targets:
				t = weakt() # resolve weakref
				if t: t(*args)
				else: self.targets.remove(weakt)
	def register(self, target):
		assert sys.getrefcount(target) > 1, "target will be weakrefed, thus we need more references to it"
		import weakref
		with self.lock:
			self.targets.append(weakref.ref(target))
