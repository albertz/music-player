
from utils import UserAttrib
import Traits

class Search:
	Keys = ("artist", "title", "duration", "rating")
	_searchText = ""
	
	@UserAttrib(type=Traits.EditableText, searchLook=True)
	def searchText(self, updateText=None):
		if updateText is not None:
			self._searchText = updateText
		return self._searchText
	
	@UserAttrib(type=Traits.Table(keys=Keys))
	def searchResults(self):
		pass

search = Search()
