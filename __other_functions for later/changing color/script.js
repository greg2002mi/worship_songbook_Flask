function changeColor(color) {
  document.body.style.backgroundColor = color;
}

function changeFontSize(size) {
  document.getElementById("myText").style.fontSize = size + "px";
}

function adjustBrightness(value) {
  document.body.style.filter = "brightness(" + value + "%)";
}