import os
import subprocess
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


class easyN_A110TaskBuilder:
	def __init__(self):
		self._instance = None

	def __call__(self, isdebug, onvif_wsdl_path, camera_settings, appsettings, **_ignored):
		camera_ip_address = camera_settings['ip_addr']
		username = camera_settings['username']
		password = camera_settings['password']
		camera_name = camera_settings['camera_name']
		onvif_port = camera_settings['onvif_port']
		http_port = camera_settings['http_port']
		rtsp_port = camera_settings['rtsp_port']

		proto_file = appsettings['proto_file']
		detector_path = appsettings['detector_path']
		detector_model_file = appsettings['detector_model_file']
		embedding_model_file = appsettings['embedding_model_file']
		recogniser_model_file = appsettings['recogniser_model_file']
		label_encoder_file = appsettings['label_encoder_file']
		min_confidence = appsettings['min_confidence']

		arg1 = '-i' + camera_ip_address
		arg2 = '-o' + str(onvif_port)
		arg3 = '-u' + username
		arg4 = '-p' + password
		arg5 = '-w' + onvif_wsdl_path
		arg6 = '-t' + proto_file
		arg7 = '-m' + detector_model_file
		arg8 = '-c' + str(min_confidence)
		arg9 = '-d' + detector_path
		arg10 = '-e' + embedding_model_file
		arg11 = '-r' + recogniser_model_file
		arg12 = '-l' + label_encoder_file
		arg13 = '-n"' + camera_name + '"'
		arg14 = '-x' + str(http_port)
		arg15 = '-y' + str(rtsp_port)

		proc = subprocess.Popen(['python', 'tasks/task_easyN_camera.py', arg1, arg2, arg3, arg4, arg5, arg6,
								 arg7, arg8, arg9, arg10, arg11, arg12, arg13, arg14, arg15], shell=False,
								stdout=subprocess.PIPE, stderr=subprocess.PIPE,
								cwd=os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

		# debug
		# print(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
		# (out, err) = proc.communicate()

		return proc
