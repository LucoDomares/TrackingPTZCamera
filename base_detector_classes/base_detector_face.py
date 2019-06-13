from abc import abstractmethod

from base_detector_classes.base_detector import base_detector


# a base camera class - do not instatiate directly
class base_detector_face(base_detector):

	# constructor
	def __init__(self, minconfidence):
		base_detector.__init__(self, minconfidence)

	# overrides

	def detect(self, frame):
		try:
			# call implementor
			return self._get_faces(frame)

		except Exception as detail:
			globals.logger.error(detail)

		return None

	@abstractmethod
	def _get_faces(self, frame):
		raise NotImplementedError("Not Implemented.")

		return None
