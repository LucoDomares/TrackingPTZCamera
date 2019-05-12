import cv2

from base_camera_classes.base_camera import base_camera


# a base camera class - do not instatiate directly
class base_HTTP_camera(base_camera):

	# constructor
	def __init__(self, isdebug, camera_ip_address, username, password, camera_name, http_port, rtsp_port):
		base_camera.__init__(self, isdebug, camera_ip_address, username, password, camera_name)

		self._http_port = http_port
		self._rtsp_port = rtsp_port

		if self._isdebug:
			print("HTTP Port: " + str(self._http_port))
			print("RTSP Port: " + str(self._rtsp_port))

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
