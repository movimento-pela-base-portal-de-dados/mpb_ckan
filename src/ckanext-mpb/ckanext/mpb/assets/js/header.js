(function () {
  var header = document.querySelector(".masthead");
  if (!header) return;

  var lastY = window.scrollY;
  window.addEventListener("scroll", function () {
    var y = window.scrollY;
    var menuOpen = header.classList.contains("masthead-menu-open");
    header.classList.toggle("masthead-hidden", !menuOpen && y > lastY && y > header.offsetHeight);
    lastY = y;
  }, { passive: true });

  var menu = header.querySelector(".main-navbar");
  if (menu) {
    menu.addEventListener("show.bs.collapse", function () {
      header.classList.add("masthead-menu-open");
    });
    menu.addEventListener("hide.bs.collapse", function () {
      header.classList.remove("masthead-menu-open");
    });
  }

  var toggle = header.querySelector(".header-search-toggle");
  var panel = document.getElementById("header-search");
  if (!toggle || !panel) return;

  function setOpen(open) {
    panel.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", String(open));
    if (open) panel.querySelector("input").focus();
  }

  toggle.addEventListener("click", function () {
    setOpen(!panel.classList.contains("is-open"));
  });

  panel.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      setOpen(false);
      toggle.focus();
    }
  });
})();
