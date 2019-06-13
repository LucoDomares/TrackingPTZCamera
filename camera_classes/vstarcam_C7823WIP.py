import os
import subprocess
import time

from imutils.video import VideoStream

from base_camera_classes.base_ONVIF_PTZ_camera import base_ONVIF_PTZ_camera


# a vstarcam camera class
class vstarcam_C7823WIP(base_ONVIF_PTZ_camera):

	# constructor
	def __init__(self, camera_ip_address, username, password, camera_name, onvif_port, onvif_wsdl_path):
		base_ONVIF_PTZ_camera.__init__(self, camera_ip_address, username, password, camera_name, onvif_port,
									   onvif_wsdl_path)

	# overrides
	def _open_video_impl(self):
		if self._videostream is not None:
			self.close_video()

		address_full = ""
		if self._videostream_uri is not None:
			'''
			# use the uri provided by the ONVIF service
			address_full = self._videostream_URL.Uri

		else:'''
			address_prefix = "http://"
			address_suffix = "/livestream.cgi?"
			address_usersuffix = "user="
			address_passwordsuffix = "&pwd="
			address_finalsuffix = "&streamid=0"
			address_full = "{}{}:{}{}{}{}{}{}{}".format(address_prefix, self._camera_ip_address,
														str(self._http_port), address_suffix, address_usersuffix,
														self._username, address_passwordsuffix,
														self._password, address_finalsuffix)

		self._videostream = VideoStream(address_full).start()
		time.sleep(0.5)


# privates


class vstarcam_C7823WIPCameraBuilder():
	def __init__(self):
		self._instance = None

	def __call__(self, onvif_wsdl_path, settings, **_ignored):
		camera_ip_address = settings['ip_addr']
		username = settings['username']
		password = settings['password']
		camera_name = settings['camera_name']
		onvif_port = settings['onvif_port']

		if not self._instance:
			self._instance = vstarcam_C7823WIP(camera_ip_address, username, password, camera_name, onvif_port,
											   onvif_wsdl_path)

		return self._instance


class vstarcam_C7823WIPTaskBuilder:
	def __init__(self):
		self._instance = None

	def __call__(self, onvif_wsdl_path, camera_settings, appsettings, **_ignored):
		camera_ip_address = camera_settings['ip_addr']
		username = camera_settings['username']
		password = camera_settings['password']
		camera_name = camera_settings['camera_name']
		onvif_port = camera_settings['onvif_port']

		proto_file = appsettings['proto_file']
		detector_path = appsettings['detector_path']
		detector_model_file = appsettings['detector_model_file']
		embedding_model_file = appsettings['embedding_model_file']
		recogniser_model_file = appsettings['recogniser_model_file']
		label_encoder_file = appsettings['label_encoder_file']
		min_confidence = appsettings['min_confidence']

		'''
		commands = 'python tasks/task_vStarCam_camera.py '
		args = '-i ' + camera_ip_address + ', -o ' + str(onvif_port) + ', -u ' + username + ', -p ' + password + \
			   ', -w ' + onvif_wsdl_path + ', --prototxt ' + proto_file + ', --model ' + detector_model_file + \
			   ', --confidence ' + str(min_confidence) + ', --detector ' + detector_path + ', --embedder ' + \
			   embedding_model_file + ', --recognizer ' + recogniser_model_file + ', --labelencoder ' + \
			   label_encoder_file + ', --cameraname "' + camera_name + '"'

		proc = subprocess.Popen(['python tasks/task_vStarCam_camera.py ' + args], shell=True,
								stdout=subprocess.PIPE, stderr=subprocess.PIPE,
								cwd=os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
		'''

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

		proc = subprocess.Popen(['python', 'tasks/task_vStarCam_camera.py', arg1, arg2, arg3, arg4, arg5, arg6,
								 arg7, arg8, arg9, arg10, arg11, arg12, arg13], shell=False,
								stdout=subprocess.PIPE, stderr=subprocess.PIPE,
								cwd=os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

		# debug
		# globals.logger.debug(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
		# (out, err) = proc.communicate()

		return proc
