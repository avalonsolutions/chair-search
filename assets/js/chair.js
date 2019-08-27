$(document).ready(function () {
  $("#submit").click(function () {
    canvasToImg()
    $(".submit").addClass("loading");
    // Fire off vanvas request

    //    setTimeout(function () {
    //      $(".submit").addClass("hide-loading");
    // For failed icon just replace ".done" with ".failed"
    //      $(".done").addClass("finish");
    //    }, 3000);
    //    setTimeout(function () {
    //      $(".submit").removeClass("loading");
    //      $(".submit").removeClass("hide-loading");
    //      $(".done").removeClass("finish");
    //      $(".failed").removeClass("finish");
    //    }, 5000);  // Wait for response instead of timeout
  })
  $("#clean").click(function () {
    // $('#img1').attr("hidden", true);
    $('.image').each(function (index) {
      var img = $(this).find('img')[0];
      img.setAttribute('hidden', true);
      img.setAttribute('src', '');
      var title = $(this).find('h4')[0]
      title.innerHTML = "";
    })
    $('#generated').attr('src', '');
    $('#generated-title').attr('hidden', 'true');
    clickX.length = 0;
    clickY.length = 0;
    clickDrag.length = 0;
    redraw();
  })


  $("#random").click(function () {
    // Ask server for files in folder
    $.ajax({
      type: "GET",
      url: "autoDraw",
      success: function (data) {
        if (data.success) {
          $.getJSON(data.filepath, function (json) {
            clickX = (json['x']);
            clickY = (json['y']);
            clickDrag = (json['drag']);
            redraw();
          });
          // Draw chair with coordinates
        } else {
          console.log('ERRROR');
        }
      },
      error: function (data) {
      }
    }).done(function () {
      console.log("Sent");
    });
  })

  canvas = document.getElementById('canvas');
  context = document.getElementById('canvas').getContext("2d");
  var length = 0;
  $('#canvas').mousedown(function (e) {
    length = 0;
    paint = true;
    var rect = canvas.getBoundingClientRect();  // get element's abs. position
    var x = e.clientX - rect.left;              // get mouse x and adjust for el.
    var y = e.clientY - rect.top;               // get mouse y and adjust for el.
    addClick(x, y, false);
    console.log(x)
    console.log(y)
    redraw();

    // var BB=canvas.getBoundingClientRect();
    // console.log(BB.top);
    // console.log(canvas.offsetTop);
    // console.log(e.pageY);
    // addClick(e.pageX - BB.left, e.pageY - BB.top, false);
    // length = length + 1;
    // redraw();
  });

  $('#canvas').mousemove(function (e) {
    if (paint) {
      var rect = canvas.getBoundingClientRect();  // get element's abs. position
      var x = e.clientX - rect.left;              // get mouse x and adjust for el.
      var y = e.clientY - rect.top;               // get mouse y and adjust for el.
      addClick(x, y, true);
      length = length + 1;
      redraw();
    }
  });

  $('#canvas').mouseup(function (e) {
    paint = false;
  });

  $('#canvas').mouseleave(function (e) {
    paint = false;
  });

  $("#undo").click(function () {
    undoLastPoint();
  });


  document.addEventListener('touchstart', function (e) {
    if (e.target == canvas) {
      e.preventDefault();
      length = 0;
      var e = e.touches[0]
      paint = true;
      addClick(e.pageX - this.offsetLeft, e.pageY - this.offsetTop, false);
      length = length + 1;
      redraw();
    }
  }, false);

  document.addEventListener('touchmove', function (e) {
    if (e.target == canvas) {
      e.preventDefault();
      var e = e.touches[0];
      if (paint) {
        addClick(e.pageX - canvas.offsetLeft, e.pageY - canvas.offsetTop, true);
        length = length + 1;
        redraw();
      }
    }

  }, false);

  document.addEventListener('touchend', function (e) {
    if (e.target == canvas) {
      e.preventDefault();
      paint = false;
    }
  }, false);

  document.addEventListener('touchcancel', function (e) {
    if (e.target == canvas) {
      e.preventDefault();
      paint = false;
    }

  }, false);


  function undoLastPoint() {
    console.log("UNDO")
    // remove the last drawn point from the drawing array
    for (var i = 0; i < length; i++) {
      clickX.pop();
      clickY.pop();
      clickDrag.pop();
    }
    // add the "undone" point to a separate redo array
    // redoStack.unshift(lastPoint);
    redraw();
  }

  function KeyPress(e) {
    var evtobj = window.event ? event : e
    if (evtobj.keyCode == 90 && evtobj.ctrlKey) {
      undoLastPoint();
    };
  }

  var clickX = new Array();
  var clickY = new Array();
  var clickDrag = new Array();
  var paint;

  function addClick(x, y, dragging) {
    clickX.push(x);
    clickY.push(y);
    clickDrag.push(dragging);
  }

  function redraw() {
    context.clearRect(0, 0, context.canvas.width, context.canvas.height); // Clears the canvas
    context.strokeStyle = "#000000";
    context.lineJoin = "round";
    context.lineWidth = 1;
    for (var i = 0; i < clickX.length; i++) {
      context.beginPath();
      if (clickDrag[i] && i) {
        context.moveTo(clickX[i - 1], clickY[i - 1]);
      } else {
        context.moveTo(clickX[i] - 1, clickY[i]);
      }
      context.lineTo(clickX[i], clickY[i]);
      context.closePath();
      context.stroke();
    }
  }

  function canvasToImg() {
    // "Hack" to get a white background for the exported canvas DataURL
    //create a dummy CANVAS
    destinationCanvas = document.createElement("canvas");
    destinationCanvas.width = canvas.width;
    destinationCanvas.height = canvas.height;

    destCtx = destinationCanvas.getContext('2d');

    //create a rectangle with the desired color
    destCtx.fillStyle = "#FFFFFF";
    destCtx.fillRect(0, 0, canvas.width, canvas.height);

    //draw the original canvas onto the destination canvas
    destCtx.drawImage(canvas, 0, 0);

    //finally use the destinationCanvas.toDataURL() method to get the desired output;
    var imgURL = destinationCanvas.toDataURL();

    // console.log(imgURL)
    $.ajax({
      type: "POST",
      url: "generate",
      headers: { 'Content-Type': 'application/json' },
      data: JSON.stringify({
        imgBase64: imgURL,
        // x: clickX,
        // y: clickY,
        // drag: clickDrag
      }),
      success: function (data) {
        if (data.success) {
          console.log('Your file was successfully uploaded!');
          // Add new b64 encoded chairs to page
          // var a = ["a", "b", "c"];
          console.log(data)
          $('#generated-title').removeAttr('hidden');
          $('#generated').attr('src', data['generated_chair']);
          $('.image').each(function (index) {
            var img = $(this).find('img')[0]
            var title = $(this).find('h4')[0]
            img.setAttribute("src", data.results[index]['src'])
            img.removeAttribute('hidden')
            title.innerHTML = data.results[index]['name'];
            img.setAttribute("src", data.results[index]['src'])
            console.log(img);
          });

        } else {
          console.log('There was an error uploading your file!');
        }
      },
      error: function (data) {
        console.log('There was an error uploading your file!');
      }
    }).done(function () {
      console.log("Sent");
    });
  }
  document.onkeydown = KeyPress;
})
