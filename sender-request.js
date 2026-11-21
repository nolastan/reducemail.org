// "Request a sender" form. Posts to the Reduce Mail server, which emails Stan.
// Progressive enhancement: without JS the form still posts and the server redirects back.
(function () {
  var form = document.getElementById("request-form");
  if (!form) return;

  var name = form.elements.name;
  var status = document.getElementById("request-status");
  var thanks = document.getElementById("request-thanks");
  var thanksName = document.getElementById("request-thanks-name");
  var button = form.querySelector("button[type=submit]");
  var section = document.getElementById("request-a-sender");

  form.elements.source.value = location.pathname;
  form.elements["return"].value = location.origin + location.pathname;

  function showThanks(sender) {
    thanksName.textContent = sender || "that sender";
    form.hidden = true;
    thanks.hidden = false;
    thanks.focus();
  }

  // Pre-fill from ?sender=… (links from other pages) or show thanks after a no-JS post.
  var params = new URLSearchParams(location.search);
  if (params.get("sender")) name.value = params.get("sender").slice(0, 120);
  if (params.get("requested")) showThanks("");

  // Called by directory-filter.js when a search finds nothing.
  window.requestSender = function (query, focus) {
    if (query) name.value = query;
    form.hidden = false;
    thanks.hidden = true;
    if (focus) {
      section.scrollIntoView({ behavior: "smooth", block: "center" });
      (query ? form.elements.website : name).focus({ preventScroll: true });
    }
  };

  document.getElementById("request-another").addEventListener("click", function () {
    form.reset();
    form.elements.source.value = location.pathname;
    form.elements["return"].value = location.origin + location.pathname;
    window.requestSender("", true);
  });

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    status.textContent = "";
    var sender = name.value.trim();
    if (!sender) {
      status.textContent = "Please enter the sender's name.";
      name.focus();
      return;
    }
    button.disabled = true;
    button.textContent = "Sending…";

    var data = {};
    new FormData(form).forEach(function (value, key) {
      data[key] = value;
    });

    fetch(form.action, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })
      .then(function (res) {
        return res.json().then(function (body) {
          if (!res.ok) throw new Error(body.error || "Something went wrong.");
        });
      })
      .then(function () {
        showThanks(sender);
        form.reset();
      })
      .catch(function (err) {
        status.textContent =
          (err && err.message && err.message !== "Failed to fetch"
            ? err.message
            : "We couldn't send that. Check your connection and try again.");
      })
      .then(function () {
        button.disabled = false;
        button.textContent = "Send request";
      });
  });
})();
