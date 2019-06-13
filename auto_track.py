# Required Packages:
# CV2

import shelve

from helpers import globals
from tasks.task_factory import TaskFactory
from tasks.task_factory import register_all_task_classes

# import cvui

# check to see if this is the main body of execution
if __name__ == "__main__":
	globals.initialize()
	settings = shelve.open('auto_track_settings')

	try:
		camera_configs = settings['cameras']
		onvif_wsdl_path = settings['wsdl']
		proto_file = settings['proto_file']
		detector_path = settings['detector_path']
		detector_model_file = settings['detector_model_file']
		embedding_model_file = settings['embedding_model_file']
		recogniser_model_file = settings['recogniser_model_file']
		label_encoder_file = settings['label_encoder_file']
		min_confidence = settings['min_confidence']


		# fire up the camera factory
		running_tasks = []

		try:
			factory = TaskFactory()
			register_all_task_classes(factory)

			cameras_to_open = sum(camera_config['is_active'] == True for camera_config in camera_configs)
			globals.logger.info('starting {} cameras'.format(cameras_to_open))

			# create each camera, start up a shell to run it
			for camera_config in camera_configs:
				if camera_config['is_active']:
					# debug
					# if camera_config['camera_name'] != 'backyard cam':
					#	camera_config['is_active'] = False

					camera_task = factory.create_task(key=camera_config['camera_class'],
													  onvif_wsdl_path=onvif_wsdl_path, settings=camera_config,
													  appsettings=settings)

					running_tasks.append(camera_task)

			globals.logger.info('cameras are running')

			# init gui
			# main_window_name = 'Auto Tracking PTZ Management'
			# root = Tk()
			# root.title(main_window_name)
			# root.mainloop()

			##cv2.namedWindow(main_window_name)
			##cvui.init(main_window_name, -1, False)

			## tell cvui to monitor the window for events
			##cvui.watch(main_window_name)

			## Image path provided as first command line arg. PNG format
			## root.iconphoto(root, PhotoImage(file=sys.argv[1]))

			##frame = np.zeros((200, 400, 3), np.uint8)

			while True:
				task_count = 0

				for task in running_tasks:
					if task.poll() is None:
						task_count += 1

				if task_count == 0:
					break

		# cvui.imshow(main_window_name, frame)
		# key = cv2.waitKey(1) & 0xFF

		# if key == ord('q'):
		#	break

		except Exception as detail:
			globals.logger.error(detail)

		finally:
			for task in running_tasks:
				task.terminate()

	except Exception as detail:
		globals.logger.error(detail)

	finally:
		if camera_configs is not None:
			settings['cameras'] = camera_configs  # copy camera settings back into settings object

		settings.close()

	# complete
	exit(0)
