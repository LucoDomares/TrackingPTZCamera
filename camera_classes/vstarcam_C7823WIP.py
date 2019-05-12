import time

from imutils.video import VideoStream

from base_camera_classes.base_ONVIF_PTZ_camera import base_ONVIF_PTZ_camera


# a vstarcam camera class
class vstarcam_C7823WIP(base_ONVIF_PTZ_camera):

	# constructor
	def __init__(self, isdebug, camera_ip_address, username, password, camera_name, onvif_port, onvif_wsdl_path):
		base_ONVIF_PTZ_camera.__init__(self, isdebug, camera_ip_address, username, password, camera_name, onvif_port,
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

	def __call__(self, isdebug, onvif_wsdl_path, settings, **_ignored):
		camera_ip_address = settings['ip_addr']
		username = settings['username']
		password = settings['password']
		camera_name = settings['camera_name']
		onvif_port = settings['onvif_port']

		if not self._instance:
			self._instance = vstarcam_C7823WIP(isdebug, camera_ip_address, username, password, camera_name, onvif_port,
											   onvif_wsdl_path)

		return self._instance
