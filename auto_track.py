# Required Packages:
# CV2

import shelve

import helpers.application_helpers as helpers
from tasks.task_factory import TaskFactory
from tasks.task_factory import register_all_task_classes

# check to see if this is the main body of execution
if __name__ == "__main__":
	settings = shelve.open('auto_track_settings')

	try:
		is_debugging = settings['is_debugging']
		onvif_wsdl_path = settings['wsdl']
		proto_file = settings['proto_file']
		detector_path = settings['detector_path']
		detector_model_file = settings['detector_model_file']
		embedding_model_file = settings['embedding_model_file']
		recogniser_model_file = settings['recogniser_model_file']
		label_encoder_file = settings['label_encoder_file']
		min_confidence = settings['min_confidence']
		cameras = settings['cameras']

		# fire up the camera factory
		running_tasks = []

		try:
			factory = TaskFactory()
			register_all_task_classes(factory)

			print('starting {} cameras'.format(len(cameras)))

			# create each camera, start up a shell to run it
			for camera_config in cameras:
				if camera_config['is_active']:
					camera_task = factory.create_task(key=camera_config['camera_class'], isdebug=is_debugging,
													  onvif_wsdl_path=onvif_wsdl_path, settings=camera_config,
													  appsettings=settings)

					running_tasks.append(camera_task)

			print('cameras are running')

			while True:
				task_count = 0

				for task in running_tasks:
					if task.poll() is None:
						task_count += 1

				if task_count == 0:
					break

		except Exception as detail:
			print("error", detail)

		finally:
			for task in running_tasks:
				task.terminate()

	except Exception as detail:
		helpers.print("error", detail)

	finally:
		settings.close()

	# complete
	exit(0)
