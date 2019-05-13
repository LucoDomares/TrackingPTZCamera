def register_all_task_classes(task_factory):
	from camera_classes.easyN_A110 import easyN_A110TaskBuilder
	task_factory.register_builder('easyN_A110', easyN_A110TaskBuilder())

	from camera_classes.HIKVISION_camera import HIKVISION_cameraTaskBuilder
	task_factory.register_builder('HIKVISION_camera', HIKVISION_cameraTaskBuilder())

	from camera_classes.vstarcam_C7823WIP import vstarcam_C7823WIPTaskBuilder
	task_factory.register_builder('vstarcam_C7823WIP', vstarcam_C7823WIPTaskBuilder())


class TaskFactory:
	def __init__(self):
		self._builders = {}

	def register_builder(self, key, builder):
		self._builders[key] = builder

	def create_task(self, key, isdebug, onvif_wsdl_path, settings, appsettings, **kwargs):  # typ):
		builder = self._builders.get(key)
		if not builder:
			raise ValueError(key)
		return builder(isdebug, onvif_wsdl_path, settings, appsettings)
