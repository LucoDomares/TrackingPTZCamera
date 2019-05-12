import logging
import os
import signal
import sys
import time
from multiprocessing import Manager, Process, Lock

import cv2
import requests
from imutils.video import FPS

from base_camera_classes.base_HTTP_PTZ_camera import base_HTTP_PTZ_camera
from base_camera_classes.base_ONVIF_PTZ_camera import base_ONVIF_PTZ_camera


# function to handle keyboard interrupt
def signal_handler(sig, frame):
	# print a status message
	print("[INFO] You pressed `ctrl + c`! Exiting...")

	# exit
	sys.exit()


# function to compare confidence level of items in faces_list.
def sort_confidence(val):
	return val[2]


# test if the target is centred in the frame
def is_target_centred(ptz_camera, pan_amt, tilt_amt):
	if pan_amt is None or tilt_amt is None:
		result = True

	elif abs(pan_amt.value) < ptz_camera.ptz_tracking_threshold and abs(
			tilt_amt.value) < ptz_camera.ptz_tracking_threshold:
		result = True

	else:
		result = False

	return result


# method to control camera PTZ movements
# this method should be run on its own thread to ensure application responsiveness
def PTZ_task(lock, ptz_camera, pan_amt, tilt_amt, is_system_on_high_alert):
	# signal trap to handle keyboard interrupt
	signal.signal(signal.SIGINT, signal_handler)

	if not isinstance(ptz_camera, base_ONVIF_PTZ_camera) and not isinstance(ptz_camera, base_HTTP_PTZ_camera):
		raise TypeError("ptz_camera must be descended from type base_ONVIF_PTZ_camera or base_PTZ_camera")

	# loop indefinitely
	while True:
		if pan_amt is None or tilt_amt is None:
			time.sleep(1.2)

		else:
			if not is_target_centred(ptz_camera, pan_amt, tilt_amt):
				lock.acquire()  # acquire a lock so that the main thread can't update pan/tilt amounts

				try:
					# target is off centre, set pan/tilt to centre it.
					ptz_camera.set_pan(pan_amt.value)
					ptz_camera.set_tilt(tilt_amt.value)

				finally:
					lock.release()  # release the lock.

				# execute the pan/tilt
				ptz_camera.execute_pan_tilt()

			else:
				# target is centred, sleep for a while if we're not on high alert
				if is_system_on_high_alert.value == 0:
					time.sleep(0.2)


def simple_cam_task(camera, detector):
	# signal trap to handle keyboard interrupt
	signal.signal(signal.SIGINT, signal_handler)

	# Re-create the session for all http requests to go through whilst in this thread.
	camera._http_session = requests.Session()

	with Manager() as manager:
		# instantiate process lock
		lock = Lock()

		pan_amt = manager.Value("i", 0)
		tilt_amt = manager.Value("i", 0)
		is_system_on_high_alert = manager.Value("i", 0)
		auto_track_enabled = manager.Value("i", 1)  # todo: save this to the config file

		# Initialise threaded PTZ controller
		processPTZ = None

		# start frames per second counter
		fps = FPS().start()

		try:
			# loop indefinitely
			while True:
				if camera.current_frame_queue.empty():
					# grab the next frame
					frame = camera.get_frame()

					if frame is None:
						continue

					# add the fame to the queue
					camera.current_frame_queue.put(frame)

				# if PTZ thread is dead or not yet started, (re)start it.
				if processPTZ is None or not processPTZ.is_alive():
					processPTZ = start_PTZ_thread(lock, camera, pan_amt, tilt_amt, is_system_on_high_alert,
												  type(camera).__name__)

				''' call out to main thread to do image processing here?'''

				# update the FPS counter
				fps.update()

				# debug print every 100 frames
				if fps._numFrames > 100:
					# stop the timer
					fps.stop()
					print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
					print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

					# restart the timer
					fps = FPS().start()

		finally:
			# do a bit of cleanup
			if processPTZ is not None:
				processPTZ.terminate()
				processPTZ.join(timeout=0.5)

			fps.stop()


# method to manage an instance of a running camera
# this method should be run on its own thread to ensure application responsiveness
def camera_task(camera, detector):
	# signal trap to handle keyboard interrupt
	signal.signal(signal.SIGINT, signal_handler)

	with Manager() as manager:
		# instantiate process lock
		lock = Lock()

		pan_amt = manager.Value("i", 0)
		tilt_amt = manager.Value("i", 0)
		is_system_on_high_alert = manager.Value("i", 0)
		auto_track_enabled = manager.Value("i", 1)  # todo: save this to the config file

		# Initialise threaded PTZ controller
		# processPTZ = start_PTZ_thread(lock, camera, pan_amt, tilt_amt, is_system_on_high_alert, type(camera).__name__)

		try:
			# start frames per second counter
			fps = FPS().start()

			calculate_frame_centre = True
			focus_window = True

			# loop indefinitely
			while True:
				# grab the next frame
				frame = camera.get_frame()

				if frame is None:
					continue

				# if PTZ thread is dead, restart it.
				# if processPTZ is None or not processPTZ.is_alive():
				# processPTZ = start_PTZ_thread(lock, camera, pan_amt, tilt_amt, is_system_on_high_alert, Stype(camera).__name__)

				'''
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
					faces_list = detector.detect(frame)

					if faces_list is not None:
						faces_list.sort(key=sort_confidence, reverse=True)

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
						lock.acquire()     		# acquire a lock
						try:
							pan_amt.value = frame_centerX - object_locationX
							tilt_amt.value = frame_centerY - object_locationY

						finally:
							lock.release()			# release the lock

						# there are faces, so put the system on high alert
						is_system_on_high_alert.value = 1

					else:
						# no faces, reset the pan/tilt values
						lock.acquire()			# acquire a lock
						try:
							pan_amt.value = 0
							tilt_amt.value = 0

						finally:
							lock.release()			# release the lock

						# there are no faces, so put the system out of high alert
						is_system_on_high_alert.value = 0
				'''

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

				# debug print every 100 frames
				if fps._numFrames > 100:
					# stop the timer
					fps.stop()
					print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
					print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

					# restart the timer
					fps = FPS().start()

		finally:
			# do a bit of cleanup
			# processPTZ.terminate
			# processPTZ.join(timeout=1.0)
			fps.stop()
			cv2.destroyAllWindows()
			camera.close_video()


def toggle_auto_tracking(auto_track_enabled):
	return not auto_track_enabled


def start_PTZ_thread(lock, camera, pan_amt, tilt_amt, is_system_on_high_alert, cam_name):
	# Initialise threaded PTZ controller
	processPTZ = Process(target=PTZ_task,
						 args=(lock, camera, pan_amt, tilt_amt, is_system_on_high_alert))
	processPTZ.name = "PTZ_Controller_" + cam_name
	processPTZ.daemon = True  # run the watchdog as daemon so it terminates with the main process
	processPTZ.start()

	return processPTZ


def dmprint(debug_message):
	logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

	logging.debug(debug_message)


def exprint(error):
	logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

	logging.error("error:", error)


def frame_add_watermark_text(frame, camera):
	# put watermark at top of frame
	if camera.auto_track_enabled == False:
		autotrack_text = "OFF"

	else:
		autotrack_text = "ON"

	if camera.isContinuousRecording:
		recording_text = "ON"

	else:
		recording_text = "OFF"

	if camera.isContinuousRecording:
		rgb_colour = (0, 0, 255)

	elif camera.auto_track_enabled == False:
		rgb_colour = (0, 255, 0)

	else:
		rgb_colour = (0, 255, 255)

	watermark_text = "Auto Tracking: {}   Continuous Recording: {}".format(autotrack_text, recording_text)

	cv2.putText(frame, watermark_text, (10, 12),
				cv2.FONT_HERSHEY_SIMPLEX, 0.45, rgb_colour, 2)

	return frame
