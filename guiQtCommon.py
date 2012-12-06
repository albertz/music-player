
try:
	class ButtonActionHandler():
		def initWithArgs(self, userAttr, inst):
			self.userAttr = userAttr
			self.inst = inst
			return self
		def click(self, sender):
			attr = self.userAttr.__get__(self.inst)
			from threading import Thread
			Thread(target=attr, name="click handler").start()
except:
	ButtonActionHandler = objc.lookUpClass("ButtonActionHandler") # already defined earlier