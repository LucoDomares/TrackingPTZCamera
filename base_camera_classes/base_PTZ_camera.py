from abc import abstractmethod

from base_camera_classes.base_camera import base_camera


# a base camera class - do not instatiate directly
class base_PTZ_camera(base_camera):

	@property
	def supportsPTZ(self):
		return True

	@property
	def is_ptz_move_relative(self):
		return self._is_ptz_move_relative

	@property
	def ptz_tracking_threshold(self):
		return self._ptz_tracking_threshold

	# constructor
	def __init__(self, isdebug, camera_ip_address, username, password, camera_name):
		base_camera.__init__(self, isdebug, camera_ip_address, username, password, camera_name)

		self._is_ptz_move_relative = False
		self._ptz_tracking_threshold = 50  # if the target is within this no of pixels, we wont bother moving at all.
		self._ptz_movement_small_threshold = 80  # if the target is within this no of pixels, we do small movements of PTZ.
		self._pan_tilt_sleep_long = 1.0  # seconds
		self._pan_tilt_sleep_short = 0.3  # seconds

	# public overrides

	@abstractmethod
	def stopPTZ(self):
		raise NotImplementedError("Not Implemented.")

	# publics

	def set_tilt(self, tilt_amt):
		if self._is_ptz_move_relative:
			self._set_tilt_relative(tilt_amt)

		else:
			self._set_tilt_continuous(tilt_amt)

	def set_pan(self, pan_amt):
		if self._is_ptz_move_relative:
			self._set_pan_relative(pan_amt)

		else:
			self._set_pan_continuous(pan_amt)

	def set_zoom(self, zoom_amt):
		if self._is_ptz_move_relative:
			self._set_zoom_relative(zoom_amt)

		else:
			self._set_zoom_continuous(zoom_amt)

	def execute_pan_tilt(self):
		try:
			if self._is_ptz_move_relative:
				self._execute_pan_tilt_relative()

			else:
				self._execute_pan_tilt_continuous()

		except Exception as detail:
			print("error:", detail)

	def execute_zoom(self):
		try:
			if self._is_ptz_move_relative:
				self._execute_zoom_relative()

			else:
				self._execute_zoom_continuous()

		except Exception as detail:
			print("error:", detail)

	def move_up(self, lock):
		tilt_amt = 100
		if self._isinverted:
			tilt_amt = tilt_amt * -1

		lock.acquire()
		try:
			self.set_pan(0)
			self.set_tilt(tilt_amt)
			self.execute_pan_tilt()

		except Exception as detail:
			print("error:", detail)

		finally:
			lock.release()

	def move_down(self, lock):
		tilt_amt = -100
		if self._isinverted:
			tilt_amt = tilt_amt * -1

		lock.acquire()
		try:
			self.set_pan(0)
			self.set_tilt(tilt_amt)
			self.execute_pan_tilt()

		except Exception as detail:
			print("error:", detail)

		finally:
			lock.release()

	def move_left(self, lock):
		pan_amt = 100
		if self._isinverted:
			pan_amt = pan_amt * -1

		lock.acquire()
		try:
			self.set_pan(pan_amt)
			self.set_tilt(0)
			self.execute_pan_tilt()

		except Exception as detail:
			print("error:", detail)

		finally:
			lock.release()

	def move_right(self, lock):
		pan_amt = -100
		if self._isinverted:
			pan_amt = pan_amt * -1

		lock.acquire()
		try:
			self.set_pan(pan_amt)
			self.set_tilt(0)
			self.execute_pan_tilt()

		except Exception as detail:
			print("error:", detail)

		finally:
			lock.release()

	def zoom_out(self, lock):
		zoom_amt = -100
		if self._isinverted:
			zoom_amt = zoom_amt * -1

		lock.acquire()
		try:
			self.set_zoom(zoom_amt)
			self.execute_zoom()

		except Exception as detail:
			print("error:", detail)

		finally:
			lock.release()

	def zoom_in(self, lock):
		zoom_amt = 100
		if self._isinverted:
			zoom_amt = zoom_amt * -1

		lock.acquire()
		try:
			self.set_zoom(zoom_amt)
			self.execute_zoom()

		except Exception as detail:
			print("error:", detail)

		finally:
			lock.release()

	# privates
	def is_far_to_move(self, pan_amt, tilt_amt):
		return abs(pan_amt) > self._ptz_movement_small_threshold or abs(tilt_amt > self._ptz_movement_small_threshold)

	# private overrides

	@abstractmethod
	def _set_tilt_continuous(self, tilt_amt):
		raise NotImplementedError("Not Implemented.")

	@abstractmethod
	def _set_pan_continuous(self, pan_amt):
		raise NotImplementedError("Not Implemented.")

	@abstractmethod
	def _execute_pan_tilt_continuous(self):
		raise NotImplementedError("Not Implemented.")

	@abstractmethod
	def _set_zoom_continuous(self, tilt_amt):
		raise NotImplementedError("Not Implemented.")

	@abstractmethod
	def _execute_zoom_continuous(self):
		raise NotImplementedError("Not Implemented.")

	@abstractmethod
	def _set_tilt_relative(self, tilt_amt):
		raise NotImplementedError("Not Implemented.")

	@abstractmethod
	def _set_pan_relative(self, pan_amt):
		raise NotImplementedError("Not Implemented.")

	@abstractmethod
	def _execute_pan_tilt_relative(self):
		raise NotImplementedError("Not Implemented.")

	@abstractmethod
	def _set_zoom_relative(self, tilt_amt):
		raise NotImplementedError("Not Implemented.")

	@abstractmethod
	def _execute_zoom_relative(self):
		raise NotImplementedError("Not Implemented.")
