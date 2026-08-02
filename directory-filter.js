// Client-side filter for the brand directories.
// Progressive enhancement: without JS the full list is still rendered and usable.
(function () {
  var input = document.getElementById("brand-search");
  var list = document.getElementById("brand-list");
  var count = document.getElementById("brand-count");
  var empty = document.getElementById("brand-empty");

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
    report(visible);
  }

  input.addEventListener("input", filter);
  report(total);
})();
