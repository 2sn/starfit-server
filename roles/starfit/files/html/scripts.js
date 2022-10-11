function buttonCheck() {
  var boxes = document.getElementsByClassName('ifGa'),
    i = boxes.length;
  if (document.getElementById('ga').checked) { var hide = 'block' }
  else { var hide = 'none' }
  while (i--) { boxes[i].style.display = hide; }

  var boxes = document.getElementsByClassName('ifNotSingle'),
    i = boxes.length;
  if (document.getElementById('single').checked) { var hide = 'none' }
  else { var hide = 'block' }
  while (i--) { boxes[i].style.display = hide; }
}

$(document).ready(function () {
  $("#run").click(function () {
    $("#processing").css({ "display": "table" });
  });
});
