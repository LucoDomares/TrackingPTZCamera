import copy
import time

from base_camera_classes.base_ONVIF_camera import base_ONVIF_camera
from base_camera_classes.base_PTZ_camera import base_PTZ_camera


# a base camera class - do not instatiate directly
class base_ONVIF_PTZ_camera(base_PTZ_camera, base_ONVIF_camera):

	# constructor
	def __init__(self, camera_ip_address, username, password, camera_name, onvif_port, onvif_wsdl_path):
		# multiple inheritance
		base_PTZ_camera.__init__(self, camera_ip_address, username, password, camera_name)
		base_ONVIF_camera.__init__(self, camera_ip_address, username, password, camera_name, onvif_port,
								   onvif_wsdl_path)

		self._ptz_status = None
		self._ptz_service = None
		self._ptz_move_request = None
		self._ptz_configuration_options = None

		# Create PTZ service object
		self._ptz_service = self._camera.create_ptz_service()

		# Get PTZ configuration options for getting continuous move range
		'''
		ptz_config_options_request = self._ptz_service.create_type('GetConfigurationOptions')
		ptz_config_options_request.ConfigurationToken = self._media_profile.PTZConfiguration.token
		self._ptz_configuration_options = self._ptz_service.GetConfigurationOptions(ptz_config_options_request)
		'''
		self._ptz_configuration_options = self._ptz_service.GetConfigurationOptions(
			self._media_profile.PTZConfiguration.token)

		# Create ptz move request
		if self._is_ptz_move_relative == True:
			self._ptz_move_request = self._ptz_service.create_type('RelativeMove')

		else:
			self._ptz_move_request = self._ptz_service.create_type('ContinuousMove')

		self._ptz_move_request.ProfileToken = self._media_profile.token

		self._ptz_service.Stop({'ProfileToken': self._media_profile.token})

		# Get range of pan and tilt
		# NOTE: X and Y are velocity vector
		self._XMAX = self._ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange.Max
		self._XMIN = self._ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange.Min
		self._YMAX = self._ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange.Max
		self._YMIN = self._ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange.Min

		self._ptz_status = self._ptz_service.GetStatus({'ProfileToken': self._media_profile.token})
		if self._ptz_status.Position is None:
			gp = self._ptz_service.create_type('GetPresets')
			gp.ProfileToken = self._media_profile.token
			presets = self._ptz_service.GetPresets(gp)
			self._ptz_status.Position = copy.deepcopy(presets[0].PTZPosition)

	# public overrides

	def stopPTZ(self):
		# Stop continuous move
		self._ptz_service.Stop({'ProfileToken': self._ptz_move_request.ProfileToken})

	# private overrides

	def _set_tilt_continuous(self, tilt_amt):
		if tilt_amt != 0 and abs(tilt_amt) > self._ptz_tracking_threshold:
			if self._ptz_move_request.Velocity is None:
				self._ptz_move_request.Velocity = copy.deepcopy(self._ptz_status.Position)

			if self._isinverted:
				tilt_amt = tilt_amt * -1

		else:
			tilt_amt = 0

		if self._ptz_move_request.Velocity is not None:
			self._ptz_move_request.Velocity.PanTilt.y = tilt_amt

	def _set_pan_continuous(self, pan_amt):
		if pan_amt != 0 and abs(pan_amt) > self._ptz_tracking_threshold:
			if self._ptz_move_request.Velocity is None:
				self._ptz_move_request.Velocity = copy.deepcopy(self._ptz_status.Position)

			if not self._isinverted:
				pan_amt = pan_amt * -1

		else:
			pan_amt = 0

		if self._ptz_move_request.Velocity is not None:
			self._ptz_move_request.Velocity.PanTilt.x = pan_amt

	def _execute_pan_tilt_continuous(self):
		pan_amt = self._ptz_move_request.Velocity.PanTilt.x
		tilt_amt = self._ptz_move_request.Velocity.PanTilt.y

		self._ptz_service.ContinuousMove(self._ptz_move_request)

		if abs(pan_amt) > 80 or abs(tilt_amt > 80):
			# Wait for camera to move longer as there's further to move
			time.sleep(self._pan_tilt_sleep_long)

		else:
			# Wait for camera to move only a short while
			time.sleep(self._pan_tilt_sleep_short)

		# Stop continuous move
		self.stopPTZ()

	def _set_zoom_continuous(self, tilt_amt):
		raise NotImplementedError("Not Implemented.")

	def _execute_zoom_continuous(self):
		raise NotImplementedError("Not Implemented.")

	def _set_tilt_relative(self, tilt_amt):
		'''
		if pan_amt != 0 and abs(pan_amt) > self._ptz_tracking_threshold:
			if self._ptz_move_request.Translation is None:
				self._ptz_move_request.Translation = copy.deepcopy(self._ptz_status.Position)

		else:
			pan_amt = 0

		self._ptz_move_request.Translation.PanTilt.y = pan_amt
		'''

		raise NotImplementedError("Not Implemented.")

	def _set_pan_relative(self, pan_amt):
		'''
		if pan_amt != 0.0 and abs(pan_amt) > self._ptz_tracking_threshold:
			if self._ptz_move_request.Translation is None:
				self._ptz_move_request.Translation = copy.deepcopy(self._ptz_status.Position)

			self._ptz_move_request.Translation.PanTilt.x = pan_amt
		'''

		raise NotImplementedError("Not Implemented.")

	def _execute_pan_tilt_relative(self):
		'''
		self._ptz_move_request.Speed = copy.deepcopy(self._ptz_move_request.Translation)
		self._ptz_move_request.Speed.PanTilt.x = 20.0
		self._ptz_move_request.Speed.PanTilt.y = 20.0
		self._ptz_service.RelativeMove(self._ptz_move_request)
		'''

		self.stopPTZ()

		raise NotImplementedError("Not Implemented.")

	def _set_zoom_relative(self, tilt_amt):
		raise NotImplementedError("Not Implemented.")

	def _execute_zoom_relative(self):
		raise NotImplementedError("Not Implemented.")

	def is_far_to_move(self, pan_amt, tilt_amt):
		return abs(pan_amt) > self._ptz_movement_small_threshold or abs(tilt_amt > self._ptz_movement_small_threshold)
