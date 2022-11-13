// Show extra options depending on which algorithm is chosen
function buttonCheck() {
  var boxes = document.getElementsByClassName('ifGa'),
    i = boxes.length;
  if (document.getElementById('ga').checked) { var hide = 'block' }
  else { var hide = 'none' }
  while (i--) { boxes[i].style.display = hide; }

  var boxes = document.getElementsByClassName('ifMulti'),
    i = boxes.length;
  if (document.getElementById('multi').checked) { var hide = 'block' }
  else { var hide = 'none' }
  while (i--) { boxes[i].style.display = hide; }

  var boxes = document.getElementsByClassName('ifNotSingle'),
    i = boxes.length;
  if (document.getElementById('single').checked) { var hide = 'none' }
  else { var hide = 'block' }
  while (i--) { boxes[i].style.display = hide; }
}

$(document).ready(function () {
  // On page loads:

  // Run the button check after page finishes loading
  // This ensures a consistent state after clicking the back button
  buttonCheck();

  // Explicitly reset the loading popup after pressing back (needed for Firefox)
  $(window).bind("pageshow", function(event) {
    $("#processing").css({ "display": "none" });
  });

  // On actions:

  // Detect clicks on the algorithm radio buttons
  const algoButtons = document.getElementsByClassName('algoButton');
  for (let i = 0; i < algoButtons.length; i++) {
    algoButtons[i].addEventListener("click", buttonCheck)
  }

  // Show loading popup when the "run" button has been clicked
  $("#run").click(function () {
    $("#processing").css({ "display": "table" });
  });

});
