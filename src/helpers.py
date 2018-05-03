#!/usr/bin/env python3
"""Helper functions for the Facial Analysis API"""
__author__ = "Andy Challis"
__maintainer__ = "Andy Challis"
__email__ = "andrewchallis@hotmail.co.uk"
__status__ = "Development"

from werkzeug.datastructures import FileStorage
import numpy as np
import json
import cv2
import os
from functools import wraps
from time import time

import settings


def load_blob(blob):
    '''Loads a blob into FileStorage if it is a string via path'''
    if isinstance(blob, FileStorage):
        return blob
    else:
        fp = open(blob, 'rb')
        return FileStorage(fp)
        

def timing(enabled):
    def actual_dec(f):
        """
        Wrapper to time a function and print to stdout
        """
        @wraps(f)
        def wrapper(*args, **kwargs):
            start = time()
            result = f(*args, **kwargs)
            timed = time()-start
            color = "\033[31m" if timed > 0.05 else "\033[32m"
            function_color = "\033[31m" if f.__name__ == "main" else '\033[36m'
            if enabled:
                print("Function {}{}\033[37m took: {}{:05.2f}\033[37m".format(function_color, f.__name__, color, timed))
                if f.__name__ == "main":
                    print("")
            return result
        return wrapper
    return actual_dec


def abort_on_fail(f):
    """
    Wrapper to abort on fail
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
        except:
            abort(400, "API failed to process request, see python traceback: {}".format(traceback.format_exc()))
        return result
    return wrapper


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool):
            return bool(obj)
        else:
            return super(NumpyEncoder, self).default(obj)


def prettify_bb(rect):
    '''Take a bounding predicted by dlib and convert it to the format
    (x, y, w, h) as we would normally do with OpenCV'''
    return {"Top": rect.top(),
            "Left": rect.left(),
            "Width": rect.right() - rect.left(),
            "Height": rect.bottom() - rect.top()}


def shape_to_np(shape):
    # initialize the list of (x, y)-coordinates
    coords = np.zeros((68, 2), dtype="int")

    # loop over the 68 facial landmarks and convert them
    # to a 2-tuple of (x, y)-coordinates
    for i in range(0, 68):
        coords[i] = (shape.part(i).x, shape.part(i).y)

    # return the list of (x, y)-coordinates
    return coords


def load_image(blob):
    nparr = np.fromstring(blob.read(), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


def save_image(blob, path):
    nparr = np.fromstring(blob.read(), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    cv2.imwrite(path, img)


def polygon_area(corners):
    n = len(corners) # of corners
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += corners[i][0] * corners[j][1]
        area -= corners[j][0] * corners[i][1]
    area = abs(area) / 2.0
    return area


def get_line_coef(p1, p2):
    # line is defined as y = mx + c
    points = [p1, p2]
    x_coords, y_coords = zip(*points)
    A = np.vstack([x_coords,np.ones(len(x_coords))]).T
    m, c = np.linalg.lstsq(A, y_coords, rcond=None)[0]
    return m, c


def reflect_point_by_line(point, m, c):
    # line is defined as y = mx + c
    d = (point[0] + (point[1] - c)*m)/(1 + m**2)
    reflected_point = (int(2*d - point[0]), int(2*d*m - point[1] + 2*c))
    return reflected_point


def count_outside_thresh(vec, pd_thresh=2, sd_thresh=3):
    '''
    Attempts to do something like this Stack Overflow response suggests
    https://stackoverflow.com/questions/14418983/how-to-detect-if-an-image-is-pixelated?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    '''
    # Find the Standard Deviation and the Mean
    sd = vec.std(); mean = vec.mean()
    # Find any outliers based on sd_threshold
    cond = np.logical_or(vec > mean + sd_thresh*sd, vec < mean - sd_thresh*sd)
    t = np.arange(len(vec))
    ix = [y for y, u in zip(t, cond) if u]
    # Peak differences
    pd = np.ediff1d(ix)
    # Find where the peaks are close together (<= pd_thresh)
    cond_pd = len(np.where(pd <= pd_thresh)[0])
    return cond_pd


def euclidean_distance(a, b):
    return np.sqrt(np.sum((a-b)**2))


def calculate_EAR(eye):
    # compute the euclidean distances between the two sets of
	# vertical eye landmarks (x, y)-coordinates
	A = euclidean_distance(eye[1], eye[5])
	B = euclidean_distance(eye[2], eye[4])

	# compute the euclidean distance between the horizontal
	# eye landmark (x, y)-coordinates
	C = euclidean_distance(eye[0], eye[3])

	# compute the eye aspect ratio
	ear = (A + B) / (2.0 * C)

	# return the eye aspect ratio
	return np.round(ear, settings.payload_scores_dp)


def estimate_top_of_head(left_eye_left, right_eye_right, chin_tip):
    # First off we want to make a line between the eye corners
    m, c = get_line_coef(left_eye_left, right_eye_right)
    # We want to reflect the chin tip by this line
    head_top = reflect_point_by_line(chin_tip, m, c)
    return head_top


def get_contrast(image):
    return np.round(100*np.mean(image)/255, settings.payload_scores_dp)
