import time

from imutils.video import VideoStream

from base_camera_classes.base_HTTP_PTZ_camera import base_HTTP_PTZ_camera
from base_camera_classes.base_ONVIF_camera import base_ONVIF_camera


# an easyN camera class
class easyN_A110(base_ONVIF_camera, base_HTTP_PTZ_camera):

	# constructor
	def __init__(self, isdebug, camera_ip_address, username, password, camera_name, onvif_port, onvif_wsdl_path,
				 http_port, rtsp_port):
		# init
		base_HTTP_PTZ_camera.__init__(self, isdebug, camera_ip_address, username, password, camera_name,
									  http_port, rtsp_port)

		# init
		base_ONVIF_camera.__init__(self, isdebug, camera_ip_address, username, password, camera_name, onvif_port,
								   onvif_wsdl_path)

		self._ptz_command_uri += "/web/cgi-bin/hi3510/ptzctrl.cgi?-step=0&-act={}&-speed=45"
		self._ptz_command_stop = self._ptz_command_uri.format("stop")

	# private overrides
	def _open_video_impl(self):
		if self._videostream is not None:
			self.close_video()

		address_full = ""
		if self._videostream_uri is not None:
			# use the uri provided by the ONVIF service
			address_full = self._videostream_uri.Uri

		else:
			# "rtsp://admin:LetMe1n@192.168.8.7:554/1/stream3"
			address_prefix = "rtsp://"
			address_finalsuffix = "/1/stream3"

			address_full = "{}{}:{}@{}:{}{}".format(address_prefix, self._username,
													self._password, self._camera_ip_address,
													str(self._rtsp_port), address_finalsuffix)

		self._videostream = VideoStream(address_full).start()

		time.sleep(0.5)

	def _set_tilt_continuous(self, tilt_amt):
		# call down to the base class first
		super()._set_tilt_continuous(tilt_amt)

		if tilt_amt != 0 and abs(tilt_amt) > self._ptz_tracking_threshold:
			if self._isinverted:
				self._ptz_tilt_amt = tilt_amt * -1

			if self._ptz_tilt_amt > 0:
				self._ptz_command_tilt = "up"

			else:
				self._ptz_command_tilt = "down"

		else:
			self._ptz_tilt_amt = 0
			self._stop_flag = True

	def _set_pan_continuous(self, pan_amt):
		# call down to the base class first
		super()._set_pan_continuous(pan_amt)

		if pan_amt != 0 and abs(pan_amt) > self._ptz_tracking_threshold:
			if self._isinverted:
				self._ptz_pan_amt = pan_amt * -1

			if self._ptz_pan_amt > 0:
				self._ptz_command_pan = "left"

			else:
				self._ptz_command_pan = "right"

		else:
			self._ptz_pan_amt = 0
			self._stop_flag = True

	def _set_zoom_continuous(self, zoom_amt):
		# this camera doesn't support zoom
		raise NotImplementedError("Not Implemented.")


# privates


class easyN_A110CameraBuilder:
	def __init__(self):
		self._instance = None

	def __call__(self, isdebug, onvif_wsdl_path, settings, **_ignored):
		camera_ip_address = settings['ip_addr']
		username = settings['username']
		password = settings['password']
		camera_name = settings['camera_name']
		onvif_port = settings['onvif_port']
		http_port = settings['http_port']
		rtsp_port = settings['rtsp_port']

		if not self._instance:
			self._instance = easyN_A110(isdebug, camera_ip_address, username, password, camera_name, onvif_port,
										onvif_wsdl_path, http_port, rtsp_port)

		return self._instance
