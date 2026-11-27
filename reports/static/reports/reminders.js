(function () {
  var cfg = window.REMINDER_URLS;
  if (!cfg) return;

  var box = document.getElementById("reminder");
  var timeEl = document.getElementById("reminder-time");
  var msgEl = document.getElementById("reminder-msg");
  var statEl = document.getElementById("reminder-stat");
  var closeBtn = document.getElementById("reminder-close");
  var goLink = document.getElementById("reminder-go");
  var current = null;
  var baseTitle = document.title;
  var blinkTimer = null;

  function beep() {
    try {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      var ctx = new Ctx();
      [0, 0.28].forEach(function (offset) {
        var o = ctx.createOscillator();
        var g = ctx.createGain();
        o.type = "sine";
        o.frequency.value = 880;
        g.gain.setValueAtTime(0.0001, ctx.currentTime + offset);
        g.gain.exponentialRampToValueAtTime(0.25, ctx.currentTime + offset + 0.03);
        g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + offset + 0.22);
        o.connect(g);
        g.connect(ctx.destination);
        o.start(ctx.currentTime + offset);
        o.stop(ctx.currentTime + offset + 0.25);
      });
    } catch (e) { /* brauzer ovozni bloklagan bo'lishi mumkin */ }
  }

  function startBlink(text) {
    stopBlink();
    var on = false;
    blinkTimer = setInterval(function () {
      document.title = on ? baseTitle : "🔔 " + text;
      on = !on;
    }, 1000);
  }

  function stopBlink() {
    if (blinkTimer) clearInterval(blinkTimer);
    blinkTimer = null;
    document.title = baseTitle;
  }

  function show(data) {
    current = data.slot_id;
    timeEl.textContent = data.time;
    msgEl.textContent = data.message;
    statEl.textContent = data.entries_today > 0
      ? "Bugun kiritilgan: " + data.entries_today + " ta yozuv" + (parseFloat(data.hours_today) > 0 ? ", " + data.hours_today + " soat." : ".")
      : "Bugun hali yozuv kiritilmagan.";
    box.hidden = false;
    beep();
    startBlink("Hisobot eslatmasi " + data.time);
  }

  function ack() {
    if (current === null) return;
    var body = new URLSearchParams();
    body.set("slot_id", current);
    fetch(cfg.ack, {
      method: "POST",
      headers: { "X-CSRFToken": cfg.csrf, "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
      credentials: "same-origin"
    }).catch(function () {});
    current = null;
    box.hidden = true;
    stopBlink();
  }

  function check() {
    if (current !== null) return; // oyna allaqachon ochiq
    fetch(cfg.check, { credentials: "same-origin", headers: { "Accept": "application/json" } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) { if (data && data.due) show(data); })
      .catch(function () {});
  }

  closeBtn.addEventListener("click", ack);
  goLink.addEventListener("click", ack);

  check();
  setInterval(check, 30000);
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) check();
  });
})();
