import os
import pickle

import cv2
import imutils
import numpy

from base_detector_classes.base_detector_face import base_detector_face


# an openface face detector class
class openface_nn4_detector(base_detector_face):

	# constructor
	def __init__(self, minconfidence, detector_path, proto_file, detector_model_file, embedding_model_file,
				 recogniser_model_file, label_encoder_file):
		base_detector_face.__init__(self, minconfidence)

		self._detector_path = detector_path
		self._proto_file = proto_file
		self._detector_model_file = detector_model_file
		self._embedding_model_file = embedding_model_file
		self._recogniser_model_file = recogniser_model_file
		self._label_encoder_file = label_encoder_file

		# DNN
		protoPath = os.path.sep.join([self._detector_path, self._proto_file])
		modelPath = os.path.sep.join([self._detector_path, self._detector_model_file])
		self._detector = cv2.dnn.readNetFromCaffe(protoPath, modelPath)

		# load the serialized face embedding model from disk/
		embedderpath = os.path.sep.join([self._detector_path, self._embedding_model_file])
		self._embedder = cv2.dnn.readNetFromTorch(embedderpath)

		# load the actual face recognition model along with the label encoder
		self._recognizer = pickle.loads(open(self._recogniser_model_file, "rb").read())
		self._labelencoder = pickle.loads(open(self._label_encoder_file, "rb").read())

	# overrides

	def _get_faces(self, frame):
		# grab the frame dimensions and convert it to a blob
		(h, w) = frame.shape[:2]

		imageblob = cv2.dnn.blobFromImage(imutils.resize(frame, width=640, inter=cv2.INTER_CUBIC), 1.0, (300, 300),
										  (104.0, 177.0, 123.0), swapRB=False, crop=False)

		# apply OpenCV's deep learning-based face detector to localize
		# faces in the input image
		self._detector.setInput(imageblob)
		detections = self._detector.forward()

		if detections.shape[2] == 0:
			return None

		else:
			rectlist = []

			# loop over the detections
			for i in range(0, detections.shape[2]):
				# extract the confidence (i.e., probability) associated with the
				# prediction
				confidence = detections[0, 0, i, 2]

				# filter out weak detections by ensuring the `confidence` is
				# greater than the minimum confidence
				if confidence < self._minconfidence:
					continue

				# compute the (x, y)-coordinates of the bounding box for the
				# object
				box = detections[0, 0, i, 3:7] * numpy.array([w, h, w, h])
				(startX, startY, endX, endY) = box.astype("int")

				# extract the face ROI
				face = frame[startY:endY, startX:endX]
				(fH, fW) = face.shape[:2]

				# ensure the face width and height are sufficiently large
				if fW < 20 or fH < 20:
					continue

				# construct a blob for the face ROI, then pass the blob
				# through our face embedding model to obtain the 128-d
				# quantification of the face
				faceBlob = cv2.dnn.blobFromImage(face, 1.0 / 255,
												 (96, 96), (0, 0, 0), swapRB=True, crop=False)
				self._embedder.setInput(faceBlob)
				vec = self._embedder.forward()

				# perform classification to recognize the face
				preds = self._recognizer.predict_proba(vec)[0]
				j = numpy.argmax(preds)
				proba = preds[j]

				if confidence >= 0.9:
					name = self._labelencoder.classes_[j]
				else:
					name = "unknown (low confidence)"

				# add the face attributes to the collection of faces.
				face_center_x = int((startX + (fW / 2)))
				face_center_y = int((startY + (fH / 2)))
				rect = (startX, startY, fW, fH)
				rectlist.append(((face_center_x, face_center_y), rect, confidence, name))

			if len(rectlist) == 0:
				return None
			else:
				return rectlist
