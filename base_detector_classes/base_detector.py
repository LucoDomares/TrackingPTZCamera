from abc import ABC, abstractmethod


# a base detector class - do not instatiate directly
class base_detector(ABC):

	# constructor
	def __init__(self, minconfidence):
		self._minconfidence = minconfidence

		self._detector = None
		self._embedder = None
		self._labelencoder = None

	# publics
	@abstractmethod
	def detect(self, frame):
		raise NotImplementedError("Not Implemented.")

		return None
