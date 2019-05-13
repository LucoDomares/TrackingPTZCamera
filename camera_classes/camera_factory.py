def register_all_camera_classes(factory):
	from camera_classes.easyN_A110 import easyN_A110CameraBuilder
	factory.register_builder('easyN_A110', easyN_A110CameraBuilder())

	from camera_classes.HIKVISION_camera import HIKVISION_cameraCameraBuilder
	factory.register_builder('HIKVISION_camera', HIKVISION_cameraCameraBuilder())

	from camera_classes.vstarcam_C7823WIP import vstarcam_C7823WIPCameraBuilder
	factory.register_builder('vstarcam_C7823WIP', vstarcam_C7823WIPCameraBuilder())


class CameraFactory:
	def __init__(self):
		self._builders = {}

	def register_builder(self, key, builder):
		self._builders[key] = builder

	def create_camera(self, key, isdebug, onvif_wsdl_path, settings, **kwargs):  # typ):
		builder = self._builders.get(key)
		if not builder:
			raise ValueError(key)
		return builder(isdebug, onvif_wsdl_path, settings)
