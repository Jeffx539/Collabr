
class Collaborator(object):
	def __init__(self, nwHandle):
		self.currentView = -1
		self.color = None
		self.name = None
		self.networkHandle = nwHandle
		self.id = 0