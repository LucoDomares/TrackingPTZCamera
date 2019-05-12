import random
import time

import requests

from base_camera_classes.base_HTTP_camera import base_HTTP_camera
from base_camera_classes.base_PTZ_camera import base_PTZ_camera


# a base camera class - do not instatiate directly
class base_HTTP_PTZ_camera(base_PTZ_camera, base_HTTP_camera):

	@property
	def supportsPTZ(self):
		return True

	# constructor
	def __init__(self, isdebug, camera_ip_address, username, password, camera_name, http_port, rtsp_port):
		base_PTZ_camera.__init__(self, isdebug, camera_ip_address, username, password, camera_name)
		base_HTTP_camera.__init__(self, isdebug, camera_ip_address, username, password, camera_name, http_port,
								  rtsp_port)

		self._is_ptz_move_relative = False  # HTTP cameras dont support relative movement
		self._ptz_tracking_threshold = 50  # if the target is within this no of pixels, we wont bother moving at all.
		self._ptz_movement_small_threshold = 80  # if the target is within this no of pixels, we do small movements of PTZ.
		self._pan_tilt_sleep_long = 0.8  # seconds
		self._pan_tilt_sleep_short = 0.5  # seconds

		self._generate_rnd_numbers_on_command = False
		self._stop_flag = False
		self._ptz_pan_amt = 0
		self._ptz_tilt_amt = 0
		self._ptz_zoom_amt = 0
		self._ptz_command_uri = "http://{}:{}@{}:{}".format(self._username, self._password,
															self._camera_ip_address, self._http_port)
		self._ptz_command_pan = ""
		self._ptz_command_tilt = ""
		self._ptz_command_zoom = ""
		self._ptz_command_stop = ""

		# Create the session for all http requests to go through
		self._http_session = requests.Session()

		# workaround: make a test HTTP request to force the session.proxy to be set.
		# if we dont do this, the PTZTask thread hangs whien getting default proxy info from the Operating System.xxxa
		r = self._http_session.get('http://www.google.com/')

		# stop any existing PTZ activity
		self.stopPTZ()

	# public overrides

	def stopPTZ(self):
		self._execute_command_http(self._ptz_command_stop)
		self._stop_flag = False

	# privates
	def _execute_command_http(self, command_url):
		if command_url != "":
			try:
				if self._generate_rnd_numbers_on_command:
					command_url = command_url + str(random.randint(1000000000000000, 9999999999999999))

				print("PTZ: " + command_url)
				r = self._http_session.get(command_url, timeout=0.5)  # requests

				if r.status_code != 200:  # OK
					print("error:", "bad command result - " + r.reason)

			except Exception as detail:
				print("error:", detail)

	# private overrides

	# this method should be overridden in the descendant class and called down to before implementing descendant logic
	def _set_tilt_continuous(self, tilt_amt):
		self._ptz_tilt_amt = tilt_amt

	# this method should be overridden in the descendant class and called down to before implementing descendant logic
	def _set_pan_continuous(self, pan_amt):
		self._ptz_pan_amt = pan_amt

	# this method should be overridden in the descendant class and called down to before implementing descendant logic
	def _set_zoom_continuous(self, zoom_amt):
		self._ptz_zoom_amt = zoom_amt

	def _execute_pan_tilt_continuous(self):
		has_panned_tilt_zoomed = False

		if self._ptz_pan_amt != 0:
			command_url = self._ptz_command_uri.format(self._ptz_command_pan)
			self._execute_command_http(command_url)
			has_panned_tilt_zoomed = True

		if self._ptz_tilt_amt != 0:
			command_url = self._ptz_command_uri.format(self._ptz_command_tilt)
			self._execute_command_http(command_url)
			has_panned_tilt_zoomed = True

		if self._ptz_zoom_amt != 0:
			command_url = self._ptz_command_uri.format(self._ptz_command_zoom)
			self._execute_command_http(command_url)
			has_panned_tilt_zoomed = True

		if has_panned_tilt_zoomed:
			if abs(self._ptz_pan_amt) > 80 or abs(self._ptz_tilt_amt > 80):
				# Wait for camera to move longer as there's further to move
				time.sleep(self._pan_tilt_sleep_long)

			else:
				# Wait for camera to move only a short while
				time.sleep(self._pan_tilt_sleep_short)

			# Stop continuous move
			self.stopPTZ()

		elif self._stop_flag:
			self.stopPTZ()

	def _execute_zoom_continuous(self):
		if self._ptz_command_zoom != "":
			command_url = self._ptz_command_uri.format(self._ptz_command_zoom)
			self._execute_command_http(command_url)

			# Wait for camera to zoom only a short while
			time.sleep(self._pan_tilt_sleep_short)

		# Stop continuous move
		self.stopPTZ()

	# relative movement functions not used by this class

	def _set_tilt_relative(self, tilt_amt):
		raise NotImplementedError("Not Implemented.")

	def _set_pan_relative(self, pan_amt):
		raise NotImplementedError("Not Implemented.")

	def _execute_pan_tilt_relative(self):
		raise NotImplementedError("Not Implemented.")

	def _set_zoom_relative(self, tilt_amt):
		raise NotImplementedError("Not Implemented.")

	def _execute_zoom_relative(self):
		raise NotImplementedError("Not Implemented.")
