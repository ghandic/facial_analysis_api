#!/usr/bin/env python3
'''Settings abstracted for the API'''
__author__ = "Andy Challis"
__maintainer__ = "Andy Challis"
__email__ = "andrewchallis@hotmail.co.uk"
__status__ = "Development"


# Set this variable to the number or decimal places accuracy to return in payload
payload_scores_dp = 4

# Set this variable to True to show the times on each of the methods used in the Object
#   - it can be used to find bottlenecks
TIMIT = False

# The path to the facial landmark model
facial_landmarks_model = '/app/data/models/shape_predictor_68_face_landmarks.dat'

# Whether to up sample of not, 0 = No upsampling, 1 = Upsample, this is an expensive operation
upscale_bb = 0

# Eyes Closed Score Threshold
ECST=0.25

# Mouth Open Score Threshold
MOST=20
