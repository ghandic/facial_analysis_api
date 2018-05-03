#!/usr/bin/env python3
'''Facial Analysis API Object used to access the facial quality of an image'''
__author__ = "Andy Challis"
__maintainer__ = "Andy Challis"
__email__ = "andrewchallis@hotmail.co.uk"
__status__ = "Development"

from threading import Thread
from time import time
import numpy as np
import dlib
import math
import json
import cv2

import helpers
import settings

# Load the face detector and the facial landmark predictor and cache them for fast calls
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(settings.facial_landmarks_model)

class FaceAPI(object):
    '''This class will analyze a given photo (tested formats: jpg) and return
    a payload of information it found regarding the image supplied.

    Example:
        ```python3
        face = FaceAPI(blob=request.files['image'])
        pl = face.get_payload(verbose=True)
        ```

    Profiling: ~10ms per image

    '''


    @helpers.timing(settings.TIMIT)
    def __init__(self, blob, upsample_bb=0):
        '''
        Set upsample_bb=1 to upsample the image during face detection on
        bounding box method, note that it comes with a time cost
        '''
        self.start_time = time()
        self.upsample_bb = upsample_bb

        # Loads FileStorage object from flask or path
        self.blob = helpers.load_blob(blob)
        self.file_name = self.blob.filename

        # Load the image from byte string, get attributes and greyscale
        self.original_image = helpers.load_image(self.blob)
        self.grey_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        self.height, self.width, _ = self.original_image.shape

        # Initial settings for vars
        self.BoundingBoxContained = False
        self.Reason = ''

        self.main()


    @helpers.timing(settings.TIMIT)
    def get_bounding_box(self):
        '''
        Detects all faces within the supplied image if there is only 1 face
        detected then it will add a bounding box to the data using DLIB's
        face detector

        Example: http://dlib.net/face_detector.py.html
        '''
        rects = detector(self.grey_image, self.upsample_bb)
        self.FacesCount = len(rects)

        if self.FacesCount < 1:
            self.Reason += 'No faces detected'
        elif self.FacesCount > 1:
            self.Reason += 'Detected {} faces'.format(self.FacesCount)
        else:
            self._bounding_box = rects[0]
            self.BoundingBox = helpers.prettify_bb(rects[0])

            self.BoundingBoxContained = self.BoundingBox['Left'] > 0 and \
                   self.BoundingBox['Left'] + self.BoundingBox['Width'] <  self.width and \
                   self.BoundingBox['Top'] > 0 and \
                   self.BoundingBox['Top'] + self.BoundingBox['Height'] < self.height
            self.Reason += "Bounding box wasn't contained" if not self.BoundingBoxContained else ''

        self.Success = bool(self.FacesCount) and self.BoundingBoxContained


    @helpers.timing(settings.TIMIT)
    def get_facial_landmarks(self):
        '''
        Adds facial landmarks to the data using DLIB's facial landmark predictor

        Example: http://dlib.net/face_landmark_detection.py.html
        '''
        self.facial_landmarks = helpers.shape_to_np(predictor(self.grey_image, self._bounding_box))
        self.PointChin = self.facial_landmarks[8]
        self.PointNose = self.facial_landmarks[30]
        self.PointLeftEyeLeft = self.facial_landmarks[36]
        self.PointRightEyeRight = self.facial_landmarks[45]
        self.PointMouthLeft = self.facial_landmarks[48]
        self.PointMouthRight = self.facial_landmarks[54]
        self.PointCheekLeft = self.facial_landmarks[0]
        self.PointCheekRight = self.facial_landmarks[16]



    @helpers.timing(settings.TIMIT)
    def get_pose(self):
        '''
        Uses the Facial landmarks to make an approximation to the persons pose
        obviously we need to make some assumptions on the camera angle, position
        focal length etc
        We also use an appoximated 3d facial model found from:
        (https://www.learnopencv.com/head-pose-estimation-using-opencv-and-dlib/)
        The projections found come from:
        (https://github.com/jerryhouuu/Face-Yaw-Roll-Pitch-from-Pose-Estimation-using-OpenCV)
        '''
        #2D image points.
        image_points = np.array([
            self.PointNose, self.PointChin, self.PointLeftEyeLeft,
            self.PointRightEyeRight, self.PointMouthLeft, self.PointMouthRight
                                ], dtype='double')
        # 3D model points.
        model_points = np.array([
                                    (0.0, 0.0, 0.0),             # Nose tip
                                    (0.0, -330.0, -65.0),        # Chin
                                    (-225.0, 170.0, -135.0),     # Left eye left corner
                                    (225.0, 170.0, -135.0),      # Right eye right corne
                                    (-150.0, -150.0, -125.0),    # Left Mouth corner
                                    (150.0, -150.0, -125.0)      # Right mouth corner

                                ])

        # Camera internals
        center = (self.width/2, self.height/2)
        focal_length = center[0] / np.tan(60/2 * np.pi / 180)
        camera_matrix = np.array(
                             [[focal_length, 0, center[0]],
                             [0, focal_length, center[1]],
                             [0, 0, 1]], dtype = 'double'
                             )

        dist_coeffs = np.zeros((4,1)) # Assuming no lens distortion
        (success, rotation_vector, translation_vector) = cv2.solvePnP(model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)

        axis = np.float32([[500,0,0], [0,500,0], [0,0,500]])

        imgpts, jac = cv2.projectPoints(axis, rotation_vector, translation_vector, camera_matrix, dist_coeffs)
        modelpts, jac2 = cv2.projectPoints(model_points, rotation_vector, translation_vector, camera_matrix, dist_coeffs)
        rvec_matrix = cv2.Rodrigues(rotation_vector)[0]

        proj_matrix = np.hstack((rvec_matrix, translation_vector))
        eulerAngles = cv2.decomposeProjectionMatrix(proj_matrix)[6]

        pitch, yaw, roll = [math.radians(theta) for theta in eulerAngles]

        self.Roll = np.round(-math.degrees(roll), settings.payload_scores_dp); self.RollPFN = [int(x) for x in np.round(imgpts[0].ravel())]
        self.Pitch = np.round(math.degrees(pitch), settings.payload_scores_dp); self.PitchPFN = [int(x) for x in np.round(imgpts[1].ravel())]
        self.Yaw = np.round(math.degrees(yaw), settings.payload_scores_dp); self.YawPFN = [int(x) for x in np.round(imgpts[2].ravel())]


    @helpers.timing(settings.TIMIT)
    def get_distance_between_eyes(self):
        '''Gets the euclidean distance between the let eye left and right eye right'''
        self.EyeDistance = int(np.round(helpers.euclidean_distance(self.PointRightEyeRight,self.PointLeftEyeLeft)))


    @helpers.timing(settings.TIMIT)
    def get_mouth_open_score(self, thresh=20):
        '''Attempts to detect if the mouth is open'''
        inner_mouth_area = helpers.polygon_area(self.facial_landmarks[60:68])
        outer__mouth_area = helpers.polygon_area(self.facial_landmarks[48:60])
        lip_area = outer__mouth_area-inner_mouth_area

        self.MouthOpenScore = np.round(inner_mouth_area/lip_area*100, settings.payload_scores_dp)
        self.MouthOpen = self.MouthOpenScore > thresh


    @helpers.timing(settings.TIMIT)
    def get_eyes_closed_score(self, thresh=0.3):
        '''Attempts to detect if the eyes are open, left right both or none'''
        # From initial inspection it looks like > 0.3 is eyes open
        # See here for more info https://www.pyimagesearch.com/2017/04/24/eye-blink-detection-opencv-python-dlib/

        self.LeftEyeArea = helpers.polygon_area(self.facial_landmarks[36:41])
        self.RightEyeArea = helpers.polygon_area(self.facial_landmarks[42:47])
        self.LeftEyeEAR = helpers.calculate_EAR(self.facial_landmarks[36:42])
        self.RightEyeEAR = helpers.calculate_EAR(self.facial_landmarks[42:48])
        self.EyesClosedScore = (self.LeftEyeEAR, self.RightEyeEAR)

        if self.LeftEyeEAR < thresh and self.RightEyeEAR < thresh:
            self.EyesClosed = 'both'
        elif self.LeftEyeEAR < thresh:
            self.EyesClosed = 'left'
        elif self.RightEyeEAR < thresh:
            self.EyesClosed = 'right'
        else:
            self.EyesClosed = 'none'


    @helpers.timing(settings.TIMIT)
    def get_payload(self, verbose=False):
        '''Gets the payload in a nice formatted manner'''
        pl = json.dumps(self.payload, indent=2, sort_keys=True, cls=helpers.NumpyEncoder)
        if verbose:
            print(pl)
        return pl


    @helpers.timing(settings.TIMIT)
    def create_payload(self):
        '''Creates the payload to send back to the client with all information about the image'''

        self.payload ={
            'FileName': self.file_name,
            'Success': self.Success,
            'Reason': self.Reason,
            'FacesCount' : self.FacesCount,
            'TimeElapsed': '{} seconds'.format(self.TimeElapsed)
            }

        if self.Success:
            self.payload['FaceDetails'] = {
                'FullFacialLandmarks': self.facial_landmarks,
                'EyeDistance': self.EyeDistance,
                'BoundingBox': self.BoundingBox,
                'MouthOpen': {'Score': self.MouthOpenScore, 'Status': self.MouthOpen},
                'Landmarks': {
                    'Chin': self.PointChin,
                    'Nose': self.PointNose,
                    'LeftEyeLeft': self.PointLeftEyeLeft,
                    'RightEyeRight': self.PointRightEyeRight,
                    'MouthLeft': self.PointMouthLeft,
                    'MouthRight': self.PointMouthRight
                    },
                'Pose': {
                    'Roll': {'Degrees': self.Roll, 'PFN': self.RollPFN},
                    'Pitch': {'Degrees': self.Pitch, 'PFN': self.PitchPFN},
                    'Yaw': {'Degrees': self.Yaw, 'PFN': self.YawPFN}
                    },
                'EyesClosed': {
                    'RightEyeArea': self.RightEyeArea,
                    'LeftEyeArea': self.LeftEyeArea,
                    'Status': self.EyesClosed,
                    'Score': self.EyesClosedScore
                    }
                }


    def step_one(self):
        '''Split out due to dependancies'''
        threads = [
        Thread(target = self.get_bounding_box())
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()



    def step_two(self):
        '''Split out due to dependancies'''
        if self.Success:
            threads = [
            Thread(target = self.get_facial_landmarks())
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()


    def step_three(self):
        '''Split out due to dependancies'''
        if self.Success:
            threads = [
            Thread(target = self.get_pose()),
            Thread(target = self.get_eyes_closed_score(thresh=settings.ECST)),
            Thread(target = self.get_mouth_open_score(thresh=settings.MOST)),
            Thread(target = self.get_distance_between_eyes())
            ]

            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()


    @helpers.timing(settings.TIMIT)
    def main(self):

        self.step_one()
        self.step_two()
        self.step_three()
        self.TimeElapsed = np.round(time() - self.start_time, settings.payload_scores_dp)
        self.create_payload()


if __name__ == '__main__':

    import glob
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default='../data/test/*.jpg')
    args = parser.parse_args()

    for image_path in glob.glob(args.p):
        face = FaceAPI(image_path)
        pl = face.get_payload(True)
