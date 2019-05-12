import time

import cv2
from imutils.video import VideoStream

from base_camera_classes.base_HTTP_PTZ_camera import base_HTTP_PTZ_camera


# a generic HIKVISION Camera class
# also known as 'HD IR INTELLIGENT SPEED DOME'
class HIKVISION_camera(base_HTTP_PTZ_camera):

	# constructor
	def __init__(self, isdebug, camera_ip_address, username, password, camera_name, onvif_port, onvif_wsdl_path,
				 http_port, rtsp_port):
		# init
		base_HTTP_PTZ_camera.__init__(self, isdebug, camera_ip_address, username, password, camera_name,
									  http_port, rtsp_port)

		self._generate_rnd_numbers_on_command = True
		self._pan_tilt_sleep_long = 0.7  # seconds
		self._pan_tilt_sleep_short = 0.3  # seconds

		self._ptz_command_uri += "/vb.htm?language=ie&ipncptz={}%000."
		self._ptz_command_stop = self._ptz_command_uri.format("pstop00000")

	# example commands:
	# "/vb.htm?language=ie&ipncptz=zoomi00000%000.2785449361658845"
	# "/vb.htm?language=ie&ipncptz=zoomo00000%000.948494675396676"
	# "/vb.htm?language=ie&ipncptz=ptzup08000%000.5817199275609197"
	# "/vb.htm?language=ie&ipncptz=pdown08000%000.24612438780342027"
	# "/vb.htm?language=ie&ipncptz=right08000%000.21992105561130615"
	# "/vb.htm?language=ie&ipncptz=pleft08000%000.9581326602997672"
	# "/vb.htm?language=ie&ipncptz=pstop00000"

	# private overrides

	def _open_video_impl(self):
		if self._videostream is not None:
			self.close_video()

		self._address_full = ""

		# "admin:admin@192.168.178.229/ipcam/avc.cgi"
		# "rtsp://192.168.178.229:8557/PSIA/Streaming/channels/2?videoCodecType=H.264"
		self._address_full = "rtsp://{}:{}/PSIA/Streaming/channels/2?videoCodecType=H.264".format(
			self._camera_ip_address, str(self._rtsp_port))

		if self._isdebug:
			print("Opening VideoStream")

		self._videostream = VideoStream(self._address_full).start()

		if self._isdebug:
			print("VideoStream opened")

		time.sleep(0.5)

	def _get_frame_impl(self):
		try:
			frame = None

			if self._videostream is not None:
				# grab the frame from the video stream
				frame = self._videostream.read()

				if frame is None:
					raise ValueError("could not decode inbound video frame check codec")

				if self._isinverted:
					# the camera is inverted, so flip the video feed.
					frame = cv2.flip(frame, 0)

				return frame

			else:
				raise ValueError("Cannot get frame because there is no videostream")

		except Exception as detail:
			print("error:", detail)

		return None

	# private overrides

	def _set_tilt_continuous(self, tilt_amt):
		# call down to the base class first
		super()._set_tilt_continuous(tilt_amt)

		if tilt_amt != 0 and abs(tilt_amt) > self._ptz_tracking_threshold:
			if self._isinverted:
				self._ptz_tilt_amt = tilt_amt * -1

			if self._ptz_tilt_amt > 0:
				self._ptz_command_tilt = "ptzup02000"

			else:
				self._ptz_command_tilt = "pdown02000"

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
				self._ptz_command_pan = "pleft02000"

			else:
				self._ptz_command_pan = "right02000"

		else:
			self._ptz_pan_amt = 0
			self._stop_flag = True

	def _set_zoom_continuous(self, zoom_amt):
		# call down to the base class first
		super()._set_zoom_continuous(zoom_amt)

		if zoom_amt != 0:
			if self._isinverted:
				self._ptz_zoom_amt = zoom_amt * -1

			if self._ptz_zoom_amt > 0:
				self._ptz_command_zoom = "zoomi00000"

			else:
				self._ptz_command_zoom = "zoomo00000"

		else:
			self._ptz_pan_amt = 0
			self._stop_flag = True


class HIKVISION_cameraCameraBuilder:
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
			self._instance = HIKVISION_camera(isdebug, camera_ip_address, username, password, camera_name, onvif_port,
											  onvif_wsdl_path, http_port, rtsp_port)

		return self._instance
