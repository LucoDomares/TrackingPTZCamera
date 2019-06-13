# usage: test_base_ONVIF_PTZ_camera -i 192.168.8.7 -o 8080 -u admin -p LetMe1n -w "/Users/Lamby/python-onvif-zeep-zeep/wsdl"

import argparse
import os
from multiprocessing import Manager, Process, Lock

import cv2
import imutils
from imutils.video import FPS

from base_camera_classes.base_ONVIF_PTZ_camera import base_ONVIF_PTZ_camera
from camera_classes.easyN_A110 import easyN_A110
from detector_classes.detector_face_openface_nn4 import openface_nn4_detector
from helpers import application_helpers
from helpers import globals


def toggle_auto_tracking(auto_track_enabled):
	if auto_track_enabled.value == 0:
		auto_track_enabled.value = 1

	else:
		auto_track_enabled.value = 0


def start_PTZ_thread(lock, camera, pan_amt, tilt_amt, is_system_on_high_alert, cam_name):
	# Initialise threaded PTZ controller
	processPTZ = Process(target=application_helpers.PTZ_task,
						 args=(lock, camera, pan_amt, tilt_amt, is_system_on_high_alert))
	processPTZ.name = "PTZ_Controller_" + cam_name
	processPTZ.daemon = True  # run the watchdog as daemon so it terminates with the main process
	processPTZ.start()

	return processPTZ


# check to see if this is the main body of execution
if __name__ == "__main__":
	globals.initialize()

	# construct the argument parser and parse the arguments
	ap = argparse.ArgumentParser()
	ap.add_argument("-i", "--ip", type=str, required=True,
					help="the IP address of the camera")
	ap.add_argument("-o", "--port", type=str, required=True,
					help="the ONVIF port of the camera")
	ap.add_argument("-u", "--user", type=str, required=True,
					help="the user name to log in to the camera")
	ap.add_argument("-p", "--pass", type=str, required=True,
					help="the password to log in to the camera")
	ap.add_argument("-w", "--wsdl", type=str, required=True,
					help="the path to the folder containing .wsdl files describing the ONVIF interface")
	ap.add_argument("-t", "--prototxt", required=True,
					help="path to Caffe 'deploy' prototxt file")
	ap.add_argument("-m", "--model", required=True,
					help="path to Caffe pre-trained model")
	ap.add_argument("-c", "--confidence", type=float, default=0.5,
					help="minimum probability to filter weak detections")
	ap.add_argument("-d", "--detector", required=True,
					help="path to OpenCV's deep learning face detector")
	ap.add_argument("-e", "--embedder", required=True,
					help="path to OpenCV's deep learning face embedding model")
	ap.add_argument("-r", "--recognizer", required=True,
					help="path to model trained to recognize faces")
	ap.add_argument("-l", "--labelencoder", required=True,
					help="path to label encoder")

	args = vars(ap.parse_args())

	ip_addr = args["ip"]
	onvif_port = args["port"]
	username = args["user"]
	password = args["pass"]
	wsdl = args["wsdl"]

	minconfidence = args["confidence"]
	proto_file = args["prototxt"]
	detector_path = args["detector"]
	detector_model_file = args["model"]
	embedding_model_file = args["embedder"]
	recogniser_model_file = args["recognizer"]
	label_encoder_file = args["labelencoder"]
	camera_name = "backyard cam"
	http_port = 81
	rtsp_port = 554

	# instantiate our face detector
	detector = openface_nn4_detector(minconfidence=minconfidence,
									 detector_path=detector_path,
									 proto_file=proto_file,
									 detector_model_file=detector_model_file,
									 embedding_model_file=embedding_model_file,
									 recogniser_model_file=recogniser_model_file,
									 label_encoder_file=label_encoder_file)

	# open connection to the camera
	# camera = easyN_A110(camera_ip_address=ip_addr, username=username, password=password,
	#						   camera_name=camera_name, http_port=http_port, rtsp_port=rtsp_port)
	camera = easyN_A110(camera_ip_address=ip_addr, username=username, password=password,
						camera_name=camera_name, onvif_port=onvif_port, onvif_wsdl_path=wsdl,
						http_port=http_port, rtsp_port=rtsp_port)
	# camera = easyN_A110(camera_ip_address=ip_addr, username=username, password=password,
	#					camera_name=camera_name, http_port=http_port, rtsp_port=rtsp_port)
	camera.open_video()

	with Manager() as manager:
		# instantiate process lock
		lock = Lock()

		pan_amt = manager.Value("i", 0)
		tilt_amt = manager.Value("i", 0)
		is_system_on_high_alert = manager.Value("i", 0)
		auto_track_enabled = manager.Value("i", 1)

		# Initialise threaded PTZ controller
		# processPTZ = Process(target=application_helpers.PTZ_task, args=(lock, camera, pan_amt, tilt_amt, is_system_on_high_alert))
		# processPTZ.name = "PTZ Controller"
		# processPTZ.daemon = True		# run the watchdog as daemon so it terminates with the main process
		# processPTZ.start()
		processPTZ = start_PTZ_thread(lock, camera, pan_amt, tilt_amt, is_system_on_high_alert, type(camera).__name__)

		# start frames per second counter
		fps = FPS().start()

		calculate_frame_centre = True
		focus_window = True

		# loop indefinitely
		while True:
			if camera.camera is None:
				continue

			# if PTZ thread is dead, restart it.
			if processPTZ is None or not processPTZ.is_alive():
				processPTZ = start_PTZ_thread(lock, camera, pan_amt, tilt_amt, is_system_on_high_alert,
											  type(camera).__name__)

			# grab the next frame
			frame = camera.get_frame()

			# resize the frame for better detection accuracy
			frame = imutils.resize(frame, width=640, inter=cv2.INTER_CUBIC)

			if auto_track_enabled.value != 0:
				if calculate_frame_centre:
					calculate_frame_centre = False

					# calculate the center of the frame as this is where we will
					# try to keep the target
					(H, W) = frame.shape[:2]
					frame_centerX = W // 2
					frame_centerY = H // 2

				# detect faces
				# faces_list = None
				faces_list = detector.detect(frame)

				if faces_list is not None:
					faces_list.sort(key=application_helpers.sort_confidence, reverse=True)

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

			# put watermark at top of frame
			if auto_track_enabled.value == 0:
				autotrack_text = "OFF"

			else:
				autotrack_text = "ON"

			if camera.isContinuousRecording:
				recording_text = "ON"

			else:
				recording_text = "OFF"

			if camera.isContinuousRecording:
				rgb_colour = (0, 0, 255)

			elif auto_track_enabled.value == 0:
				rgb_colour = (0, 255, 0)

			else:
				rgb_colour = (0, 255, 255)

			watermark_text = "Auto Tracking: {}   Continuous Recording: {}".format(autotrack_text, recording_text)

			cv2.putText(frame, watermark_text, (10, 12),
						cv2.FONT_HERSHEY_SIMPLEX, 0.45, rgb_colour, 2)

			cv2.imshow(camera.camera_name, frame)

			if focus_window:
				os.system(
					'''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "python" to true' ''')  # To make window active
				focus_window = False

			key = cv2.waitKey(1) & 0xFF

			if key == ord('q'):
				break

			elif key == 0:
				camera.move_up(lock)

			elif key == 1:
				camera.move_down(lock)

			elif key == 2:
				camera.move_left(lock)

			elif key == 3:
				camera.move_right(lock)

			elif key == ord('z'):
				camera.zoom_in(lock)

			elif key == ord('x'):
				camera.zoom_out(lock)

			elif key == ord('a'):
				toggle_auto_tracking(auto_track_enabled)

				if auto_track_enabled.value == 0:
					if isinstance(camera, base_ONVIF_PTZ_camera):
						camera.stopPTZ()

			# elif key == ord('c'):
			#	toggle_continuous_capture()

			# update the FPS counter
			fps.update()

			# debug every 100 frames
			if fps._numFrames > 100:
				# stop the timer
				fps.stop()
				globals.logger.debug("elasped time: {:.2f}".format(fps.elapsed()))
				globals.logger.debug("approx. FPS: {:.2f}".format(fps.fps()))

				# restart the timer
				fps = FPS().start()

	# do a bit of cleanup
	processPTZ.terminate
	processPTZ.join(timeout=1.0)
	fps.stop()
	cv2.destroyAllWindows()
	camera.close_video()

	# complete
	quit()
