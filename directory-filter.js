// Client-side filter for the brand directories.
// Progressive enhancement: without JS the full list is still rendered and usable.
(function () {
  var input = document.getElementById("brand-search");
  var list = document.getElementById("brand-list");
  var count = document.getElementById("brand-count");
  var empty = document.getElementById("brand-empty");
  var request = document.getElementById("brand-request");
  var requestName = document.getElementById("brand-request-name");
  var requestHref = request && request.getAttribute("href");

  if (!input || !list) return;

  var items = Array.prototype.slice.call(list.children);
  var total = items.length;

  function report(visible) {
    if (!count) return;
    count.textContent =
      visible === total
        ? total + " brands"
        : visible + " of " + total + " brands";
  }

  function filter() {
    var q = input.value.trim().toLowerCase();
    var visible = 0;

    items.forEach(function (li) {
      var name = (li.getAttribute("data-name") || li.textContent).toLowerCase();
      var match = !q || name.indexOf(q) !== -1;
      li.hidden = !match;
      if (match) visible++;
    });

    if (empty) empty.hidden = visible !== 0;
    if (request && visible === 0) {
      var raw = input.value.trim();
      requestName.textContent = raw ? "\u201c" + raw + "\u201d" : "it";
      // Same page: the click handler fills the form. Other page: carry it in the URL.
      var parts = requestHref.split("#");
      request.setAttribute(
        "href",
        parts[0] + (raw ? "?sender=" + encodeURIComponent(raw) : "") + "#" + parts[1]
      );
    }
    report(visible);
  }

  input.addEventListener("input", filter);
  if (request) {
    request.addEventListener("click", function (event) {
      if (!window.requestSender || request.pathname !== location.pathname) return;
      event.preventDefault();
      window.requestSender(input.value.trim(), true);
    });
  }
  report(total);
})();
