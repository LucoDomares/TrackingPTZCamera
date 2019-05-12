import cv2
# start monkey patch
import zeep
from onvif import ONVIFCamera

from base_camera_classes.base_camera import base_camera


def zeep_pythonvalue(self, xmlvalue):
	return xmlvalue


zeep.xsd.simple.AnySimpleType.pythonvalue = zeep_pythonvalue


# end monkey patch

# a base camera class - do not instantiate directly
class base_ONVIF_camera(base_camera):

	@property
	def media(self):
		return self._media

	@property
	def is_camera_init(self):
		return hasattr(self, "_isinitialised")

	# constructor
	def __init__(self, isdebug, camera_ip_address, username, password, camera_name, onvif_port, onvif_wsdl_path):
		# if camera is already initialised, we have multiple inheritence, and this init code has already executed.
		if self.is_camera_init:
			return

		base_camera.__init__(self, isdebug, camera_ip_address, username, password, camera_name)

		self._onvif_port = onvif_port
		self._onvif_wsdl_path = onvif_wsdl_path

		if isdebug:
			print("Connecting to camera at {}".format(camera_ip_address))

		self._camera = ONVIFCamera(camera_ip_address, self._onvif_port, self._username, self._password,
								   onvif_wsdl_path)  # , no_cache=True)

		if isdebug:
			print("Camera connected")

		# Create media service object
		self._camera.devicemgmt.GetServices(False)
		self._media = self._camera.create_media_service()
		self._media_profile = self._media.GetProfiles()[0]

		# get video stream uri
		getstreamobj = self._media.create_type('GetStreamUri')
		getstreamobj.ProfileToken = self._media_profile.token
		getstreamobj.StreamSetup = {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'TCP'}}  # 'RTSP', 'HTTP', 'UDP'

		self._videostream_uri = self._media.GetStreamUri(getstreamobj)

		# get list of supported network protocols
		network_protocols = self._camera.devicemgmt.GetNetworkProtocols()

		# store http and rtsp ports
		for protocol in network_protocols:
			if protocol.Name == "HTTP":
				self._http_port = protocol.Port[0]
			elif protocol.Name == "RTSP":
				self._rtsp_port = protocol.Port[0]

		if self._isdebug:
			print("ONVIF Port: " + str(self._onvif_port))

		# finally, set up init flag
		self._isinitialised = True

	# private overrides

	def _get_frame_impl(self):
		try:
			if self._videostream is not None:
				# grab the frame from the video stream
				frame = self._videostream.read()

				if frame is None:
					raise ValueError("Empty frame was returned by videostream")

				if self._isinverted:
					# the camera is inverted, so flip the video feed.
					frame = cv2.flip(frame, 0)

				return frame

			else:
				raise ValueError("Cannot get frame because there is no videostream")

		except Exception as detail:
			print("error:", detail)

		return None

# privates
