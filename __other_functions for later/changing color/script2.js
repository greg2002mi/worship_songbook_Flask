function changeColor(color) {
  document.body.style.backgroundColor = color;
}

function changeFontSize(size) {
  document.getElementById("myText").style.fontSize = size + "px";
}

function adjustBrightness(value) {
  var brightnessValue = (value - 50) / 50;
  var invertedValue = 1 - Math.abs(brightnessValue);
  var brightnessPercentage = invertedValue * 100;
  document.body.style.background = "hsl(0, 0%, " + brightnessPercentage + "%)";
}
