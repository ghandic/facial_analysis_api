#!/usr/bin/env python3
"""Flask REST API for Facial Analysis"""
__author__ = "Andy Challis"
__maintainer__ = "Andy Challis"
__email__ = "andrewchallis@hotmail.co.uk"
__status__ = "Development"

from flask import Flask, request, Response
from flask_cors import CORS
import os

import helpers
import settings
from face import FaceAPI as FaceAPIv1

# Initialize the Flask application
app = Flask(__name__); CORS(app, resources=r'/api/*')


@helpers.abort_on_fail
@app.route('/api/v1/face', methods=['POST'])
def check_image():
    face = FaceAPIv1(blob=request.files['image'], upsample_bb=settings.upscale_bb)
    payload = face.get_payload(verbose=False)
    return Response(response=payload, status=200, mimetype="application/json")


# start flask app (tried processes=8 threaded was much better)
app.run(host="0.0.0.0", port=int(os.getenv('PORT')), debug=True, threaded=True)
