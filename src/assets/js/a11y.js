/* Baixa visió en xarxa — eines d'accessibilitat
   - Barra d'accessibilitat persistent (mida del text, contrast clar/fosc, lectura en veu alta)
     i panell complet: mida del text fins al 300 %, set esquemes de color (fons fosc o clar),
     interlineat i espaiat ajustables, escala de grisos, enllaços destacats, cursor gran,
     aturar animacions, guia de lectura i lectura en veu alta.
   - Les preferències es desen al navegador (localStorage) i s'apliquen abans de pintar
     la pàgina amb el petit script en línia del <head>. Quan la web s'obre des del disc
     (file://), cada fitxer té un emmagatzematge separat; en aquest cas les preferències
     s'afegeixen als enllaços interns (?bvx=...) perquè es mantinguin en canviar de pàgina.
   - Cada canvi s'anuncia als lectors de pantalla (aria-live) i també amb un avís visual. */
(function () {
  "use strict";

  var KEY = "bvx-prefs";
  var SIZES = [100, 125, 150, 175, 200, 250, 300];
  var BASE = 112.5; // mida base del document (%), equivalent a 18 px
  var TOGGLES = ["grayscale", "links", "cursor", "motion"];
  var LEVELS = ["lh", "sp"]; // interlineat i espaiat entre lletres i paraules (0, 1, 2)
  var root = document.documentElement;
  var T = {};
  try { T = JSON.parse(document.getElementById("ui-strings").textContent); } catch (e) {}

  function load() {
    if (window.__bvxPrefs && typeof window.__bvxPrefs === "object") return window.__bvxPrefs;
    try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; }
  }
  function save(p) {
    try { localStorage.setItem(KEY, JSON.stringify(p)); } catch (e) {}
    decorateLinks();
  }

  /* Amb file:// cada pàgina té el seu propi localStorage: passem les preferències
     a la pàgina següent a través de l'enllaç. Amb http(s) no cal i els enllaços no es toquen. */
  var INTERNAL = /^(?![a-z][a-z0-9+.-]*:|\/\/|#)([^?#]*\.html)(#.*)?$/i;
  function decorateLinks() {
    if (location.protocol !== "file:") return;
    var param = "?bvx=" + encodeURIComponent(JSON.stringify(prefs));
    document.querySelectorAll("a[href]").forEach(function (a) {
      var orig = a.getAttribute("data-href") || a.getAttribute("href");
      var m = orig.match(INTERNAL);
      if (!m) return;
      a.setAttribute("data-href", orig);
      a.setAttribute("href", m[1] + param + (m[2] || ""));
    });
  }
  var prefs = load();

  /* ---------- Avisos: lector de pantalla + visual ---------- */
  var live = document.getElementById("live-region");
  var toast = document.getElementById("toast");
  var toastText = toast ? toast.querySelector("[data-toast-text]") : null;
  var toastTimer;
  function announce(msg) {
    if (live) { live.textContent = ""; setTimeout(function () { live.textContent = msg; }, 50); }
    if (toast && toastText) {
      toastText.textContent = msg;
      toast.hidden = false;
      clearTimeout(toastTimer);
      toastTimer = setTimeout(function () { toast.hidden = true; }, 4000);
    }
  }

  /* ---------- Aplicar preferències ---------- */
  function apply() {
    var size = SIZES.indexOf(prefs.size) >= 0 ? prefs.size : 100;
    root.style.fontSize = (BASE * size / 100) + "%";
    if (prefs.theme && prefs.theme !== "auto") root.setAttribute("data-theme", prefs.theme);
    else root.setAttribute("data-theme", "auto");
    TOGGLES.forEach(function (t) { root.classList.toggle("opt-" + t, !!prefs[t]); });
    root.classList.remove("opt-spacing");
    LEVELS.forEach(function (n) {
      [1, 2].forEach(function (v) { root.classList.toggle(n + "-" + v, prefs[n] === v); });
    });
    document.querySelectorAll("[data-size-value]").forEach(function (o) { o.textContent = size + "%"; });
    guide(!!prefs.guide);
    if (typeof updateSticky === "function") updateSticky();
  }

  /* ---------- Guia de lectura (banda que segueix el punter) ---------- */
  var guideEl = document.getElementById("reading-guide");
  function moveGuide(e) {
    var y = e.touches ? e.touches[0].clientY : e.clientY;
    guideEl.style.top = (y - guideEl.offsetHeight / 2) + "px";
  }
  function guide(on) {
    if (!guideEl) return;
    guideEl.hidden = !on;
    if (on) {
      document.addEventListener("mousemove", moveGuide, { passive: true });
      document.addEventListener("touchmove", moveGuide, { passive: true });
      if (!guideEl.style.top) guideEl.style.top = "40vh";
    } else {
      document.removeEventListener("mousemove", moveGuide);
      document.removeEventListener("touchmove", moveGuide);
    }
  }

  /* ---------- Panell ---------- */
  var toggleBtn = document.getElementById("a11y-toggle");
  var panel = document.getElementById("a11y-panel");

  function openPanel(open) {
    panel.hidden = !open;
    toggleBtn.setAttribute("aria-expanded", String(open));
    if (open) {
      var h = panel.querySelector("h2");
      if (h) { h.setAttribute("tabindex", "-1"); h.focus(); }
    }
  }
  if (toggleBtn && panel) {
    toggleBtn.addEventListener("click", function () { openPanel(panel.hidden); });
    panel.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { openPanel(false); toggleBtn.focus(); }
    });
    var closeBtn = document.getElementById("a11y-close");
    if (closeBtn) closeBtn.addEventListener("click", function () { openPanel(false); toggleBtn.focus(); });
  }

  function syncControls() {
    var size = prefs.size || 100;
    document.querySelectorAll("[data-size-step]").forEach(function (b) {
      var step = parseInt(b.getAttribute("data-size-step"), 10);
      b.disabled = step < 0 ? size <= SIZES[0] : size >= SIZES[SIZES.length - 1];
    });
    document.querySelectorAll('input[name="theme"]').forEach(function (r) {
      r.checked = r.value === (prefs.theme || "auto");
    });
    document.querySelectorAll("[data-theme-quick]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-theme-quick") === (prefs.theme || "auto")));
    });
    LEVELS.forEach(function (n) {
      document.querySelectorAll('input[name="' + n + '"]').forEach(function (r) {
        r.checked = parseInt(r.value, 10) === (prefs[n] || 0);
      });
    });
    TOGGLES.concat(["guide"]).forEach(function (t) {
      var c = document.getElementById("opt-" + t);
      if (c) c.checked = !!prefs[t];
    });
  }

  function setSize(step) {
    var i = SIZES.indexOf(prefs.size || 100);
    i = Math.max(0, Math.min(SIZES.length - 1, i + step));
    prefs.size = SIZES[i];
    save(prefs); apply(); syncControls();
    announce((T.sizeNow || "Text size") + ": " + prefs.size + "%");
  }
  var resetSize = document.getElementById("size-reset");
  document.querySelectorAll("[data-size-step]").forEach(function (b) {
    b.addEventListener("click", function () { setSize(parseInt(b.getAttribute("data-size-step"), 10)); });
  });
  if (resetSize) resetSize.addEventListener("click", function () {
    prefs.size = 100; save(prefs); apply(); syncControls();
    announce((T.sizeNow || "Text size") + ": 100%");
  });

  document.querySelectorAll('input[name="theme"]').forEach(function (r) {
    r.addEventListener("change", function () {
      prefs.theme = r.value; save(prefs); apply(); syncControls();
      var label = r.closest("label");
      var text = label ? (label.querySelector(".choice__text") || label) : null;
      announce((T.themeNow || "Theme") + ": " + (text ? text.textContent.trim() : r.value));
    });
  });

  document.querySelectorAll("[data-theme-quick]").forEach(function (b) {
    b.addEventListener("click", function () {
      prefs.theme = b.getAttribute("data-theme-quick"); save(prefs); apply(); syncControls();
      announce((T.themeNow || "Theme") + ": " + b.textContent.trim());
    });
  });

  LEVELS.forEach(function (n) {
    document.querySelectorAll('input[name="' + n + '"]').forEach(function (r) {
      r.addEventListener("change", function () {
        prefs[n] = parseInt(r.value, 10) || 0; delete prefs.spacing;
        save(prefs); apply();
        var fs = r.closest("fieldset"), lg = fs ? fs.querySelector("legend") : null;
        var label = r.closest("label");
        announce((lg ? lg.textContent.trim() + ": " : "") + (label ? label.textContent.trim() : r.value));
      });
    });
  });

  TOGGLES.concat(["guide"]).forEach(function (t) {
    var c = document.getElementById("opt-" + t);
    if (!c) return;
    c.addEventListener("change", function () {
      prefs[t] = c.checked; save(prefs); apply();
      var label = c.closest("label");
      announce((label ? label.textContent.trim() : t) + ": " + (c.checked ? (T.on || "on") : (T.off || "off")));
    });
  });

  var resetAll = document.getElementById("a11y-reset");
  if (resetAll) resetAll.addEventListener("click", function () {
    prefs = {}; save(prefs); apply(); syncControls(); stopSpeech(true);
    announce(T.resetDone || "Settings restored");
  });

  /* ---------- Lectura en veu alta (Web Speech API) ---------- */
  var synth = window.speechSynthesis;
  var speakBtn = document.getElementById("tts-play");
  var pauseBtn = document.getElementById("tts-pause");
  var stopBtn = document.getElementById("tts-stop");
  var rateSel = document.getElementById("tts-rate");
  var ttsStatus = document.getElementById("tts-status");
  var queue = [];
  var speaking = false;

  function setStatus(msg) { if (ttsStatus) ttsStatus.textContent = msg; }

  function pickVoice(lang) {
    if (!synth) return null;
    var voices = synth.getVoices();
    var exact = voices.filter(function (v) { return v.lang && v.lang.toLowerCase().indexOf(lang) === 0; });
    return exact[0] || null;
  }

  function textChunks(el) {
    var sel = window.getSelection ? String(window.getSelection()) : "";
    var text;
    if (!el && sel && sel.trim().length > 2) {
      text = sel;
    } else {
      var main = el || document.getElementById("main");
      var clone = main.cloneNode(true);
      clone.querySelectorAll("[aria-hidden='true'], .visually-hidden, script, style, .breadcrumbs, .listen-btn, [hidden], .print-only").forEach(function (n) { n.remove(); });
      // separa blocs perquè les pauses siguin naturals
      clone.querySelectorAll("h1,h2,h3,h4,p,li,dt,dd,summary,td,th,caption").forEach(function (n) { n.append(". "); });
      text = clone.textContent;
    }
    text = text.replace(/\s+/g, " ").replace(/(\.\s*){2,}/g, ". ").trim();
    // trossos curts: alguns navegadors tallen frases molt llargues
    return text.match(/[^.!?;:]+[.!?;:]*\s*/g) || [];
  }

  function speakNext() {
    if (!queue.length) { speaking = false; updateTtsButtons(); setStatus(T.ttsDone || ""); document.dispatchEvent(new CustomEvent("bvx:tts-end")); return; }
    var u = new SpeechSynthesisUtterance(queue.shift());
    var lang = root.lang || "ca";
    u.lang = { ca: "ca-ES", es: "es-ES", en: "en-GB" }[lang] || lang;
    var v = pickVoice(lang);
    if (v) u.voice = v;
    u.rate = parseFloat(rateSel ? rateSel.value : "1") || 1;
    u.onend = speakNext;
    u.onerror = function () { speaking = false; updateTtsButtons(); document.dispatchEvent(new CustomEvent("bvx:tts-end")); };
    synth.speak(u);
  }

  var barPlay = document.getElementById("bar-tts-play");
  var barStop = document.getElementById("bar-tts-stop");
  function updateTtsButtons() {
    if (barPlay && barStop) {
      var focusStop = speaking && document.activeElement === barPlay;
      var focusPlay = !speaking && document.activeElement === barStop;
      barPlay.hidden = speaking; barStop.hidden = !speaking;
      if (focusStop) barStop.focus();
      if (focusPlay) barPlay.focus();
    }
    if (pauseBtn) pauseBtn.disabled = !speaking;
    if (stopBtn) stopBtn.disabled = !speaking;
    if (pauseBtn) pauseBtn.setAttribute("aria-pressed", String(!!(synth && synth.paused)));
  }

  function stopSpeech(silent) {
    if (!synth) return;
    queue = []; synth.cancel(); speaking = false; updateTtsButtons();
    document.dispatchEvent(new CustomEvent("bvx:tts-end"));
    if (!silent) { setStatus(T.ttsStopped || ""); announce(T.ttsStopped || "Stopped"); }
  }

  if (!synth || !window.SpeechSynthesisUtterance) {
    document.querySelectorAll("[data-tts]").forEach(function (n) { n.hidden = true; });
    var noTts = document.getElementById("tts-unsupported");
    if (noTts) noTts.hidden = false;
  } else {
    var startReading = function (el) {
      synth.cancel();
      document.dispatchEvent(new CustomEvent("bvx:tts-end"));
      queue = textChunks(el);
      speaking = true; updateTtsButtons();
      var lang = root.lang || "ca";
      var msg = T.ttsReading || "Reading";
      if (!pickVoice(lang) && T.ttsNoVoice) msg += ". " + T.ttsNoVoice;
      setStatus(msg); announce(msg);
      // pausa breu perquè l'anunci no se solapi amb la lectura
      setTimeout(speakNext, 400);
    };
    // Lector integrat reutilitzable (guies en àudio de les pàgines, vegeu features.js)
    window.BVX = window.BVX || {};
    window.BVX.read = startReading;
    window.BVX.stop = function () { stopSpeech(true); };
    if (speakBtn) speakBtn.addEventListener("click", function () { startReading(); });
    if (barPlay) barPlay.addEventListener("click", function () { startReading(); });
    if (barStop) barStop.addEventListener("click", function () { stopSpeech(false); });
    if (pauseBtn) pauseBtn.addEventListener("click", function () {
      if (synth.paused) { synth.resume(); setStatus(T.ttsReading || ""); }
      else { synth.pause(); setStatus(T.ttsPaused || ""); }
      updateTtsButtons();
    });
    if (stopBtn) stopBtn.addEventListener("click", function () { stopSpeech(false); });
    if (rateSel) {
      if (prefs.rate) rateSel.value = prefs.rate;
      rateSel.addEventListener("change", function () { prefs.rate = rateSel.value; save(prefs); });
    }
    if (synth.onvoiceschanged !== undefined) synth.onvoiceschanged = function () {};
    window.addEventListener("pagehide", function () { synth.cancel(); });
    updateTtsButtons();
  }

  /* ---------- Menú principal en pantalles petites ---------- */
  var menuBtn = document.getElementById("menu-toggle");
  var menu = document.getElementById("main-menu");
  if (menuBtn && menu) {
    menu.setAttribute("data-collapsed", "true");
    menuBtn.addEventListener("click", function () {
      var open = menuBtn.getAttribute("aria-expanded") === "true";
      menuBtn.setAttribute("aria-expanded", String(!open));
      menu.setAttribute("data-collapsed", String(open));
    });
  }

  /* ---------- Preferència d'idioma ---------- */
  document.querySelectorAll(".lang-switch a[hreflang]").forEach(function (a) {
    a.addEventListener("click", function () {
      try { localStorage.setItem("bvx-lang", a.getAttribute("hreflang")); } catch (e) {}
    });
  });
  try { localStorage.setItem("bvx-lang", root.lang); } catch (e) {}

  /* ---------- Les taules desplaçables han de ser accessibles amb teclat ---------- */
  document.querySelectorAll(".table-wrap").forEach(function (w) {
    if (w.scrollWidth > w.clientWidth) {
      var cap = w.querySelector("caption");
      w.setAttribute("tabindex", "0");
      w.setAttribute("role", "region");
      if (cap) w.setAttribute("aria-label", cap.textContent.trim());
    }
  });

  /* ---------- Barra persistent: fixa a dalt només si no ocupa massa pantalla ----------
     (amb text molt gran o pantalles baixes deixa de ser fixa perquè no tapi el contingut
     ni el focus: WCAG 2.4.11) */
  var bar = document.getElementById("a11y-bar");
  function updateSticky() {
    if (!bar) return;
    bar.classList.remove("is-sticky");
    var ok = bar.offsetHeight <= window.innerHeight * 0.16 && window.innerWidth >= 640;
    bar.classList.toggle("is-sticky", ok);
    root.style.scrollPaddingTop = ok ? (bar.offsetHeight + 16) + "px" : "";
  }
  window.addEventListener("resize", updateSticky, { passive: true });

  apply();
  syncControls();
  decorateLinks();
})();
