from collections import deque
from threading import Condition
class OnRequestQueue:
	class QueueEnd:
		def __init__(self):
			self.q = deque()
			self.cond = Condition()
			self.cancel = False
	def __init__(self):
		self.queues = set()
	def put(self, item):
		for q in self.queues:
			with q.cond:
				if q.cancel: continue
				q.q.append(item)
				q.cond.notify()
	def cancelAll(self):
		for q in self.queues:
			with q.cond:
				q.cancel = True
				q.cond.notify()
		self.queues.clear()
	def read(self):
		q = self.QueueEnd()
		self.queues.add(q)
		while True:
			with q.cond:
				q.cond.wait()
				l = list(q.q)
				q.q.clear()
				cancel = q.cancel
			for item in l:
				yield item
			if cancel: break

class initBy(property):
	def __init__(self, initFunc):
		property.__init__(self, fget = self.fget)
		self.initFunc = initFunc
	def fget(self, inst):
		if hasattr(self, "value"): return self.value
		self.value = self.initFunc()
		return self.value

class oneOf(property):
	def __init__(self, *consts):
		property.__init__(self, fget = self.fget, fset = self.fset)
		assert len(consts) > 0
		self.consts = consts
		self.value = consts[0]
	def fget(self, inst):
		return self
	def fset(self, inst, value):
		assert value in self.consts
		self.value = value
