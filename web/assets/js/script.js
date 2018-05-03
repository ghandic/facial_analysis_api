//var FACEAPI ='http://0.0.0.0:8686/api/v1/face';
var FACEAPI ='https://gentle-dusk-58307.herokuapp.com/api/v1/face'

document.addEventListener('DOMContentLoaded', function () {

    // References to all the element we will need.
    var video = document.querySelector('#camera-stream'),
        image = document.querySelector('#snap'),
        start_camera = document.querySelector('#start-camera'),
        controls = document.querySelector('.controls'),
        take_photo_btn = document.querySelector('#take-photo'),
        delete_photo_btn = document.querySelector('#delete-photo'),
        download_photo_btn = document.querySelector('#download-photo'),
        error_message = document.querySelector('#error-message');
    wakeAPI();

    var modal = new tingle.modal({
      footer: true,
      stickyFooter: false,
      closeMethods: ['overlay', 'button', 'escape'],
      closeLabel: "Close",
      cssClass: ['custom-class-1', 'custom-class-2'],
      onOpen: function() {
          console.log('modal open');
      },
      onClose: function() {
          deletePhoto();
      }
    });

    if(!navigator.mediaDevices.getUserMedia){
        displayErrorMessage("Your browser doesn't have support for the navigator.getUserMedia interface.");
    }
    else{

        // Request the camera.
      var constraints = {video: true };
      navigator.mediaDevices.getUserMedia(constraints)
        .then(function(mediaStream) {
          video.srcObject = mediaStream;
          video.onloadedmetadata = function(e) {
            video.play();
            showVideo();
          };
        })
        .catch(function(err) { console.log(err.name + ": " + err.message); });

    }



    // Mobile browsers cannot play video without user input,
    // so here we're using a button to start it manually.
    start_camera.addEventListener("click", function(e){

        e.preventDefault();

        // Start video playback manually.
        video.play();
        showVideo();

    });


    take_photo_btn.addEventListener("click", function(e){

        e.preventDefault();

        var snap = takeSnapshot();
        sendToAPI();

        // Show image.
        image.setAttribute('src', snap);
        image.classList.add("visible");

        // Enable delete and save buttons
        delete_photo_btn.classList.remove("disabled");
        download_photo_btn.classList.remove("disabled");

        // Pause video playback of stream.
        video.pause();

    });


    delete_photo_btn.addEventListener("click", function(e){
      e.preventDefault();
      deletePhoto();
    });

    function deletePhoto() {
      // Hide image.
      image.setAttribute('src', "");
      image.classList.remove("visible");

      // Disable delete and save buttons
      delete_photo_btn.classList.add("disabled");
      download_photo_btn.classList.add("disabled");

      // hide old response
      document.getElementById("response").innerHTML = '';

      // Resume playback of stream.
      video.play();
    }



    function showVideo(){
        // Display the video stream and the controls.

        hideUI();
        video.classList.add("visible");
        controls.classList.add("visible");
    }


    function takeSnapshot(){
        // Here we're using a trick that involves a hidden canvas element.

        var hidden_canvas = document.querySelector('canvas'),
            context = hidden_canvas.getContext('2d');

        var width = video.videoWidth,
            height = video.videoHeight;

        if (width && height) {

            // Setup a canvas with the same dimensions as the video.
            hidden_canvas.width = width;
            hidden_canvas.height = height;

            // Make a copy of the current frame in the video on the canvas.
            context.drawImage(video, 0, 0, width, height);

            // Turn the canvas image into a dataURL that can be used as a src for our photo.
            return hidden_canvas.toDataURL('image/png');
        }
    }


    function displayErrorMessage(error_msg, error){
        error = error || "";
        if(error){
            console.error(error);
        }

        error_message.innerText = error_msg;

        hideUI();
        error_message.classList.add("visible");
    }


    function hideUI(){
        // Helper function for clearing the app UI.

        controls.classList.remove("visible");
        start_camera.classList.remove("visible");
        video.classList.remove("visible");
        snap.classList.remove("visible");
        error_message.classList.remove("visible");
    }

    function wakeAPI() {
      var canvas = document.querySelector('canvas');
      canvas.toBlob(function (blob) {
        var formData = new FormData();
        formData.append('image', blob, 'webcam_' + (new Date).getTime().toString() + '.jpg');
        $.ajax(FACEAPI, {//'https://gentle-dusk-58307.herokuapp.com/api/v1/face', {
          method: 'POST',
          data: formData,
          processData: false,
          contentType: false,
          success: function(response) {
            console.log(response);
          },
          error: function (msg) {
            console.log(msg);
          }
        });
      });
    }

    function sendToAPI() {
      var canvas = document.querySelector('canvas');
      canvas.toBlob(function (blob) {
        var formData = new FormData();
        formData.append('image', blob, 'webcam_' + (new Date).getTime().toString() + '.jpg');
        $.ajax(FACEAPI, {//'https://gentle-dusk-58307.herokuapp.com/api/v1/face', {
          method: 'POST',
          data: formData,
          processData: false,
          contentType: false,
          success: function(response) {
            showResponse(response);
            if (response.Success) {
              drawResponse(response, canvas);
            } else {
              modal.setContent(response.Reason);
              modal.open();
            }

          },
          error: function (msg) {
            console.log(msg);
          }
        });
      });
    }

    function showResponse(response) {
      var response_ui = document.getElementById("response")
      renderjson.set_icons('', '');
      renderjson.set_show_to_level(0);
      response_ui.innerHTML = '';
      response_ui.appendChild(renderjson(response));
      response_ui.style.display = 'block';
    }

    function addBoundingBox(ctx, response) {
      var bb = response.FaceDetails.BoundingBox;
      ctx.rect(bb.Left,bb.Top,bb.Width,bb.Height);
      ctx.strokeStyle="yellow";
      ctx.lineWidth=3;
      ctx.setLineDash([3, 3]);
      ctx.stroke();
    }

    function addPose(ctx, response) {
      var pose = response.FaceDetails.Pose;
      var fl = response.FaceDetails.Landmarks;
      // pitch
      ctx.beginPath();
      ctx.moveTo(fl.Nose[0],fl.Nose[1]);
      ctx.lineTo(pose.Pitch.PFN[0],pose.Pitch.PFN[1]);
      ctx.strokeStyle="red";
      ctx.stroke();
      // roll
      ctx.beginPath();
      ctx.moveTo(fl.Nose[0],fl.Nose[1]);
      ctx.lineTo(pose.Roll.PFN[0],pose.Roll.PFN[1]);
      ctx.strokeStyle="green";
      ctx.stroke();
      // yaw
      ctx.beginPath();
      ctx.moveTo(fl.Nose[0],fl.Nose[1]);
      ctx.lineTo(pose.Yaw.PFN[0],pose.Yaw.PFN[1]);
      ctx.strokeStyle="blue";
      ctx.stroke();
    }

    function addFacialLandmarks(ctx, response) {
      var ffl = response.FaceDetails.FullFacialLandmarks;
      for (i in ffl) {
        ctx.beginPath();
        ctx.setLineDash([]);
        ctx.fillStyle = "red";
        ctx.arc(ffl[i][0],ffl[i][1],1,0,2*Math.PI);
        ctx.fill();
      }
    }

    function addMask(ctx, response) {
      var ed = response.FaceDetails.EyeDistance
      var fl = response.FaceDetails.Landmarks;
      var mask = document.getElementById("mask");
      var MaskWidth = ed*2.4;
      var MaskHeight = ed*2.6
      // x, y, w, h
      ctx.drawImage(mask, fl.LeftEyeLeft[0]-MaskWidth*0.3, fl.LeftEyeLeft[1]-MaskHeight*0.38, MaskWidth, MaskHeight);
    }



    function drawResponse(response) {

      var canvas = document.querySelector('canvas');
      var ctx = canvas.getContext('2d');
      var img = document.getElementById("snap");
      // redraw the image
      ctx.drawImage(img, 0, 0);
      // add a bounding box
      addBoundingBox(ctx, response);
      // add the facial landmarks
      addFacialLandmarks(ctx, response);
      // add Pose
      addPose(ctx, response);
      // draw mask
      //addMask(ctx, response);

      // draw the new image
      img.src = canvas.toDataURL('image/png');
      // Set the href attribute of the download button to the snap url.
      download_photo_btn.href = img.src;
    }

});
