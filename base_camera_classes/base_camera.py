from abc import ABC, abstractmethod
from multiprocessing import Queue, Lock

from helpers import globals


# a base camera class - do not instatiate directly
class base_camera(ABC):

	@property
	def supportsPTZ(self):
		return False

	@property
	def lock(self):
		return self._lock

	@property
	def camera(self):
		return self._camera

	@property
	def camera_name(self):
		return self._camera_name

	@property
	def videostream(self):
		return self._videostream

	@property
	def supportsPTZ(self):
		return False

	@property
	def isinverted(self):
		return self._isinverted

	@property
	def isContinuousRecording(self):
		return self._isContinuousRecording

	@property
	def current_frame_queue(self):
		return self._current_frame_queue

	@property
	def processed_frame_queue(self):
		return self._processed_frame_queue

	@property
	def focus_window(self):
		return self._focus_window

	@property
	def calculate_frame_centre(self):
		return self._calculate_frame_centre

	@property
	def auto_track_enabled(self):
		return self._auto_track_enabled

	# constructor
	def __init__(self, camera_ip_address, username, password, camera_name):
		# multiple inheritance
		self._lock = Lock()
		self._username = username
		self._password = password
		self._camera_ip_address = camera_ip_address
		self._isContinuousRecording = False

		self._current_frame_queue = Queue(maxsize=1)
		self._processed_frame_queue = Queue(maxsize=1)
		self._focus_window = True
		self._calculate_frame_centre = True
		self._auto_track_enabled = False

		if camera_name != "":
			self._camera_name = camera_name

		else:
			self._camera_name = type(self).__name__

		self._camera = None
		self._videostream = None
		self._isinverted = False

	# destructor
	def __del__(self):
		self.close_video()

	# public

	def open_video(self):
		try:
			# call implementor
			self._open_video_impl()

		except Exception as detail:
			globals.logger.error(detail)

	def close_video(self):
		try:
			if self._videostream is not None:
				self._videostream.stop()

		except Exception as detail:
			globals.logger.error(detail)
			raise

	def get_frame(self):
		try:
			# call implementor
			return self._get_frame_impl()

		except Exception as detail:
			globals.logger.error(detail)
			raise

		return None

	# private overrides

	@abstractmethod
	def _open_video_impl(self):
		raise NotImplementedError("Not Implemented.")

	@abstractmethod
	def _get_frame_impl(self):
		raise NotImplementedError("Not Implemented.")

		return None

# privates
