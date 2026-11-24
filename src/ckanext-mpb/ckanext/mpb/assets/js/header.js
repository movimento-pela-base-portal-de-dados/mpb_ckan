(function () {
  var header = document.querySelector(".masthead");
  if (!header) return;
  var lastY = window.scrollY;
  window.addEventListener("scroll", function () {
    var y = window.scrollY;
    header.classList.toggle("masthead-hidden", y > lastY && y > header.offsetHeight);
    lastY = y;
  }, { passive: true });
})();
