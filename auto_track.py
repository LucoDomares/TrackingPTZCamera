import os
import shelve
# import multiprocessing as mp
# from multiprocessing import Manager, Process, Lock
# from multiprocessing.pool import ThreadPool
from concurrent.futures import ThreadPoolExecutor

import cv2
import imutils

import helpers.application_helpers as helpers
from base_camera_classes import base_ONVIF_PTZ_camera
from camera_classes.camera_factory import CameraFactory
from camera_classes.camera_factory import register_all_camera_classes
from detector_classes.detector_face_openface_nn4 import openface_nn4_detector


def start_camera_thread(camera, detector):
	# Initialise threaded PTZ controller
	camera_process = mp.Process(target=helpers.simple_cam_task, args=(camera, detector))  #
	camera_process.name = "camera_process_" + camera.camera_name
	# camera_process.daemon = True  # run the watchdog as daemon so it terminates with the main process
	camera_process.start()

	return camera_process


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

		'''
		settings['is_debugging'] = True
		settings['wsdl'] = '/Users/Lamby/python-onvif-zeep-zeep/wsdl'
		settings['proto_file'] = 'deploy.prototxt'
		settings['detector_path'] = 'detector_classes/model_detector_face_openface_nn4'
		settings['detector_model_file'] = 'res10_300x300_ssd_iter_140000.caffemodel'
		settings['embedding_model_file'] = 'openface_nn4.small2.v1.t7'
		settings['recogniser_model_file'] = '_detectormodels/recognizer.pickle'
		settings['label_encoder_file'] = '_detectormodels/le.pickle'
		settings['min_confidence'] = 0.6

		cam1 = dict(ip_addr='192.168.8.18',
					username='admin',
					password='Gateway2',
					minconfidence=0.60,
					camera_name='study cam',
					http_port=0,
					rtsp_port=0,
					onvif_port=10080,
					is_active=True,
					camera_class='vstarcam_C7823WIP'
					)

		cam2 = dict(ip_addr='192.168.8.7',
					username='admin',
					password='LetMe1n',
					minconfidence=0.60,
					camera_name='backyard cam',
					http_port=81,
					rtsp_port=554,
					onvif_port=8080,
					is_active=True,
					camera_class='easyN_A110'
					)

		cam3 = dict(ip_addr='192.168.8.229',
					username='admin',
					password='admin',
					minconfidence=0.60,
					camera_name='johnny cam',
					http_port=80,
					rtsp_port=8557,
					onvif_port=8200,
					is_active=True,
					camera_class='HIKVISION_camera'
					)

		cameras = []
		cameras.append(cam1)
		cameras.append(cam2)
		cameras.append(cam3)

		settings['cameras'] = cameras
		'''

		# instantiate our face detector
		detector = openface_nn4_detector(isdebug=is_debugging,
										 minconfidence=min_confidence,
										 detector_path=detector_path,
										 proto_file=proto_file,
										 detector_model_file=detector_model_file,
										 embedding_model_file=embedding_model_file,
										 recogniser_model_file=recogniser_model_file,
										 label_encoder_file=label_encoder_file)

		# instantiate the camera factory
		running_cameras = []
		camera_pool = ThreadPoolExecutor(len(cameras))

		try:
			# mp.set_start_method('spawn')	# prevent hangs in cv2 within threads

			factory = CameraFactory()
			register_all_camera_classes(factory)

			helpers.dmprint('starting {} cameras'.format(len(cameras)))

			# create each camera, start up a thread to manage it
			for camera_config in cameras:
				if camera_config['is_active']:
					camera = factory.create_camera(key=camera_config['camera_class'], isdebug=is_debugging,
												   onvif_wsdl_path=onvif_wsdl_path, settings=camera_config)
					camera._http_session = None  # clear the session
					running_cameras.append(camera)

					camera_pool.submit(helpers.simple_cam_task, camera, detector)

			# camera_process = start_camera_thread(camera, detector)
			# camera_processes.append(camera_process)

			for camera_config in cameras:
				if camera_config['is_active']:
					# import requests

					# camera._http_session = requests.Session()
					camera.open_video()
			# mp.active_children() 	# this joins all the started processes, and runs them.

			while True:
				for running_camera in running_cameras:
					if not running_camera.current_frame_queue.empty():
						frame = running_camera.current_frame_queue.get()

						# resize the frame for better detection accuracy
						frame = imutils.resize(frame, width=640, inter=cv2.INTER_CUBIC)

						frame = helpers.frame_add_watermark_text(frame, running_camera)

						cv2.imshow(camera.camera_name, frame)

						if running_camera.focus_window:
							os.system(
								'''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "python" to true' ''')  # To make window active
							running_camera._focus_window = False

						key = cv2.waitKey(1) & 0xFF

						if key == ord('q'):
							break

						elif key == 0:
							running_camera.move_up(running_camera.lock)

						elif key == 1:
							running_camera.move_down(running_camera.lock)

						elif key == 2:
							running_camera.move_left(running_camera.lock)

						elif key == 3:
							running_camera.move_right(running_camera.lock)

						elif key == ord('z'):
							running_camera.zoom_in(running_camera.lock)

						elif key == ord('x'):
							running_camera.zoom_out(running_camera.lock)

						elif key == ord('a'):
							running_camera.auto_track_enabled = helpers.toggle_auto_tracking(
								running_camera.auto_track_enabled)

							if running_camera.auto_track_enabled == False:
								if isinstance(running_camera, base_ONVIF_PTZ_camera):
									running_camera.stopPTZ()

						# elif key == ord('c'):
						#	helpers.toggle_continuous_capture()

						'''
						if running_camera.auto_track_enabled != 0:
							if running_camera.calculate_frame_centre:
								calculate_frame_centre = False

								# calculate the center of the frame as this is where we will
								# try to keep the target
								(H, W) = frame.shape[:2]
								frame_centerX = W // 2
								frame_centerY = H // 2

							# detect faces
							faces_list = detector.detect(frame)

							if faces_list is not None:
								faces_list.sort(key=helpers.sort_confidence, reverse=True)

								for face in faces_list:
									# extract the location and bounds of the face
									((face_locX, face_locY), rect, confidence, face_name) = face
									(x, y, w, h) = rect

									# draw a rectabgle around the face
									cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

									# name the face
									face_text = "{}: {:.2f}%".format(face_name, confidence * 100)
									cv2.putText(frame, face_text, (x, y - 9),
												cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)

								# Track the highest confidence object found
								((object_locationX, object_locationY), rect, confidence, name) = faces_list[0]

								# set pan/tilt based on distance of target from centre of frame.
								lock.acquire()  # acquire a lock
								try:
									pan_amt.value = frame_centerX - object_locationX
									tilt_amt.value = frame_centerY - object_locationY

								finally:
									lock.release()  # release the lock

								# there are faces, so put the system on high alert
								is_system_on_high_alert.value = 1

							else:
								# no faces, reset the pan/tilt values
								lock.acquire()  # acquire a lock
								try:
									pan_amt.value = 0
									tilt_amt.value = 0

								finally:
									lock.release()  # release the lock

								# there are no faces, so put the system out of high alert
								is_system_on_high_alert.value = 0
								
						'''
		#	key = cv2.waitKey(1) & 0xFF

		#	if key == ord('q'):
		#		break

		except Exception as error:
			print(error)
			raise


		finally:
			camera_pool.shutdown(wait=True)  # wait for all processes in the pool to complete
	# if camera_processes is not None:
	#	for process in camera_processes:
	#		process.terminate
	#		process.join(timeout=1.0)

	except Exception as error:
		helpers.exprint(error)

	finally:
		settings.close()

	# complete
	quit()
