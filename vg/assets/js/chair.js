canvas = document.getElementById('canvas');
ctx = document.getElementById('canvas').getContext("2d");
ctx.fillStyle = "#FFFFFF";
ctx.fillRect(0, 0, 500, 500);
var length = 0;
$('#canvas').mousedown(function (e) {
  length = 0;
  paint = true;
  addClick(e.pageX - this.offsetLeft, e.pageY - this.offsetTop, false);
  length = length + 1;
  redraw();
});

$('#canvas').mousemove(function (e) {
  if (paint) {
    addClick(e.pageX - this.offsetLeft, e.pageY - this.offsetTop, true);
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