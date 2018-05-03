FROM python:3-alpine3.6

ENV CC="/usr/bin/clang" CXX="/usr/bin/clang++" OPENCV_VERSION="3.3.0"

RUN echo -e '@edgunity http://nl.alpinelinux.org/alpine/edge/community\n\
@edge http://nl.alpinelinux.org/alpine/edge/main\n\
@testing http://nl.alpinelinux.org/alpine/edge/testing\n\
@community http://dl-cdn.alpinelinux.org/alpine/edge/community'\
  >> /etc/apk/repositories

RUN apk add --update --no-cache \
  # --virtual .build-deps \
      build-base \
      openblas-dev \
      unzip \
      wget \
      cmake \

      #Intel® TBB, a widely used C++ template library for task parallelism'
      libtbb@testing  \
      libtbb-dev@testing   \

      # Wrapper for libjpeg-turbo
      libjpeg  \

      # accelerated baseline JPEG compression and decompression library
      libjpeg-turbo-dev \

      # Portable Network Graphics library
      libpng-dev \

      # A software-based implementation of the codec specified in the emerging JPEG-2000 Part-1 standard (development files)
      jasper-dev \

      # Provides support for the Tag Image File Format or TIFF (development files)
      #tiff-dev \

      # Libraries for working with WebP images (development files)
      #libwebp-dev \

      # A C language family front-end for LLVM (development files)
      clang-dev \

      linux-headers \

      # Additional python packages
      && pip install numpy imutils requests flask

RUN mkdir /opt && cd /opt && \
  wget https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip && \
  unzip ${OPENCV_VERSION}.zip && \
  rm -rf ${OPENCV_VERSION}.zip

RUN mkdir -p /opt/opencv-${OPENCV_VERSION}/build && \
  cd /opt/opencv-${OPENCV_VERSION}/build && \
  cmake \
  -D CMAKE_BUILD_TYPE=RELEASE \
  -D CMAKE_INSTALL_PREFIX=/usr/local \
  -D WITH_FFMPEG=NO \
  -D WITH_IPP=ON \
  -D WITH_OPENEXR=NO \
  -D WITH_TBB=YES \
  -D BUILD_EXAMPLES=NO \
  -D BUILD_ANDROID_EXAMPLES=NO \
  -D INSTALL_PYTHON_EXAMPLES=NO \
  -D BUILD_DOCS=NO \
  -D BUILD_opencv_python2=NO \
  -D BUILD_opencv_python3=ON \
  -D PYTHON3_EXECUTABLE=/usr/local/bin/python \
  -D PYTHON3_INCLUDE_DIR=/usr/local/include/python3.6m/ \
  -D PYTHON3_LIBRARY=/usr/local/lib/libpython3.so \
  -D PYTHON_LIBRARY=/usr/local/lib/libpython3.so \
  -D PYTHON3_PACKAGES_PATH=/usr/local/lib/python3.6/site-packages/ \
  -D PYTHON3_NUMPY_INCLUDE_DIRS=/usr/local/lib/python3.6/site-packages/numpy/core/include/ \
  .. && \
  make VERBOSE=1 && \
  make && \
  make install && \
  rm -rf /opt/opencv-${OPENCV_VERSION}

# Making an app directory
RUN mkdir -p /app/data/models && \
    mkdir  /app/src && \
    mkdir  /app/data/input && \
    mkdir  /app/data/output

# Facial landmark detection model
RUN cd /app/data/models && \
	wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2 && \
	bzip2 -d shape_predictor_68_face_landmarks.dat.bz2

# Installing dlib
RUN apk add --no-cache git && \
	git clone https://github.com/davisking/dlib.git && \
	cd dlib/examples && mkdir build && cd build && cmake .. -DUSE_AVX_INSTRUCTIONS=ON && cmake --build . --config Release && \
	cd ../.. && python setup.py install

# Baking code into container
ADD src/*.py /app/src/

# Adding alias for the client
RUN echo 'alias client="clear && python /app/src/client.py"' >> ~/.profile && \
    source ~/.profile

RUN pip install --no-cache-dir flask-cors Flask-Uploads pytest pytest-xdist pytest-sugar

# Running our API as the entrypoint
WORKDIR /app/src
ENTRYPOINT ["python"]
CMD ["server.py"]
