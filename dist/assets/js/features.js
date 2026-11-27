/* Baixa visió en xarxa — eines de contingut
   - Guies en àudio: botó «Escolta aquesta guia» a les seccions marcades amb data-listen.
   - Simulador de visió (Familiars i interessats).
   - Filtres del repositori de testimonis.
   - Generador de recursos per a la consulta (caselles → PDF accessible + codi QR) i
     pàgina del paquet que obre el QR.
   - Formulari de validació participativa (REQ-12).
   Tot funciona sense servidor i sense enviar dades a tercers. */
(function () {
  "use strict";
  var T = {};
  try { T = JSON.parse(document.getElementById("ui-strings").textContent); } catch (e) {}
  var hasTts = !!(window.speechSynthesis && window.SpeechSynthesisUtterance);

  /* ---------- Guies en text i àudio ---------- */
  var activeListen = null;
  function resetListen() {
    if (!activeListen) return;
    activeListen.setAttribute("aria-pressed", "false");
    activeListen.querySelector("span").textContent = T.listen || "Listen";
    activeListen = null;
  }
  document.addEventListener("bvx:tts-end", resetListen);
  if (hasTts) {
    document.querySelectorAll("[data-listen]").forEach(function (sec) {
      var h = sec.querySelector("h2, h3");
      if (!h) return;
      var b = document.createElement("button");
      b.type = "button";
      b.className = "btn btn--ghost btn--sm listen-btn";
      b.setAttribute("aria-pressed", "false");
      b.innerHTML = '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M4 9v6h4l5 4V5L8 9H4z"/><path d="M16.5 8.5a5 5 0 0 1 0 7M19 6a8.5 8.5 0 0 1 0 12"/></svg><span></span>';
      b.querySelector("span").textContent = T.listen || "Listen";
      b.setAttribute("aria-describedby", h.id || "");
      h.insertAdjacentElement("afterend", b);
      b.addEventListener("click", function () {
        if (!window.BVX || !window.BVX.read) return;
        if (activeListen === b) { window.BVX.stop(); resetListen(); return; }
        window.BVX.read(sec);
        activeListen = b;
        b.setAttribute("aria-pressed", "true");
        b.querySelector("span").textContent = T.stopListen || "Stop";
      });
    });
  }

  /* ---------- Simulador de visió ---------- */
  document.querySelectorAll("[data-simulator]").forEach(function (sim) {
    var view = sim.querySelector(".sim__view");
    var desc = sim.querySelector("#sim-desc");
    sim.querySelectorAll('input[name="sim-mode"]').forEach(function (r) {
      r.addEventListener("change", function () {
        view.setAttribute("data-mode", r.value);
        desc.textContent = r.getAttribute("data-desc");
      });
    });
  });

  /* ---------- Filtres de testimonis ---------- */
  var tf = document.querySelector("[data-testimonial-filters]");
  if (tf) {
    var list = document.querySelector("[data-testimonials]");
    tf.addEventListener("change", function () {
      var f = {};
      tf.querySelectorAll("[data-filter]").forEach(function (s) { f[s.getAttribute("data-filter")] = s.value; });
      list.querySelectorAll("li[data-pathology]").forEach(function (li) {
        li.hidden = (f.pathology && li.getAttribute("data-pathology") !== f.pathology) ||
                    (f.age && li.getAttribute("data-age") !== f.age);
      });
    });
  }

  /* ---------- Codi QR ---------- */
  function packUrl(box, ids) {
    var base = box.getAttribute("data-base");
    var pack = box.getAttribute("data-pack");
    var q = ids.length ? "?r=" + ids.join(".") : "";
    var lang = document.documentElement.lang;
    if (base) return base + "/" + lang + "/" + pack + q;
    if (/^https?:$/.test(location.protocol)) return new URL(pack + q, location.href).href;
    return pack + q; // obert des del disc: el QR no serviria fora d'aquest ordinador
  }
  function drawQr(box, url) {
    var holder = box.querySelector("[data-qr-code]");
    var link = box.querySelector("[data-qr-link]");
    var local = box.querySelector("[data-qr-local]");
    if (link) { link.href = url; link.textContent = url; }
    var absolute = /^https?:/.test(url);
    if (local) local.hidden = absolute;
    if (!holder || typeof window.qrcode !== "function") return;
    var qr = window.qrcode(0, "M");
    qr.addData(absolute ? url : location.href.split("?")[0]);
    qr.make();
    var n = qr.getModuleCount(), m = 4, size = n + m * 2, d = "";
    for (var r = 0; r < n; r++) for (var c = 0; c < n; c++) if (qr.isDark(r, c)) d += "M" + (c + m) + " " + (r + m) + "h1v1h-1z";
    // Sempre negre sobre blanc (amb marge) perquè el llegeixi qualsevol càmera, en tots els temes
    holder.innerHTML = '<svg viewBox="0 0 ' + size + " " + size + '" shape-rendering="crispEdges" aria-hidden="true" focusable="false">' +
      '<rect width="' + size + '" height="' + size + '" fill="#fff"/><path d="' + d + '" fill="#000"/></svg>';
  }

  function showSheets(ids) {
    document.querySelectorAll("[data-sheet]").forEach(function (s) {
      s.hidden = ids.indexOf(s.getAttribute("data-sheet")) < 0;
    });
  }

  /* ---------- Generador per a la consulta ---------- */
  var gen = document.querySelector("[data-generator]");
  if (gen) {
    var box = document.querySelector("[data-qr]");
    var count = gen.querySelector("[data-count]");
    var printBtn = gen.querySelector("[data-print]");
    var empty = gen.querySelector("[data-empty]");
    var noteIn = gen.querySelector("#gen-note");
    var noteOut = document.querySelector("[data-note-out]");
    var noteWrap = document.querySelector("[data-note-wrap]");
    var dateOut = document.querySelector("[data-date]");
    if (dateOut) dateOut.textContent = new Date().toLocaleDateString(document.documentElement.lang);
    var update = function () {
      var ids = [];
      gen.querySelectorAll('input[name="r"]:checked').forEach(function (c) { ids.push(c.value); });
      showSheets(ids);
      if (count) count.textContent = String(ids.length);
      if (printBtn) printBtn.disabled = !ids.length;
      if (empty) empty.hidden = !!ids.length;
      if (box) drawQr(box, packUrl(box, ids));
      if (noteOut) {
        var v = noteIn ? noteIn.value.trim() : "";
        noteOut.textContent = v;
        if (noteWrap) noteWrap.hidden = !v;
      }
    };
    gen.addEventListener("change", update);
    if (noteIn) noteIn.addEventListener("input", update);
    gen.querySelectorAll("[data-select]").forEach(function (b) {
      b.addEventListener("click", function () {
        var on = b.getAttribute("data-select") === "all";
        gen.querySelectorAll('input[name="r"]').forEach(function (c) { c.checked = on; });
        update();
      });
    });
    if (printBtn) printBtn.addEventListener("click", function () { window.print(); });
    gen.addEventListener("submit", function (e) { e.preventDefault(); if (!printBtn.disabled) window.print(); });
    window.addEventListener("load", update);
    update();
  }

  /* ---------- Pàgina del paquet (la que obre el QR) ---------- */
  var pack = document.querySelector("[data-pack-page]");
  if (pack) {
    var m = location.search.match(/[?&]r=([a-z0-9.\-]+)/i);
    var ids = m ? m[1].split(".") : [];
    var valid = [];
    ids.forEach(function (id) { if (document.querySelector('[data-sheet="' + id + '"]')) valid.push(id); });
    var all = document.querySelector("[data-pack-all]");
    if (valid.length) { showSheets(valid); if (all) all.hidden = true; }
    var pbox = document.querySelector("[data-qr]");
    var drawPack = function () { if (pbox) drawQr(pbox, packUrl(pbox, valid)); };
    window.addEventListener("load", drawPack);
    drawPack();
    var pp = document.querySelector("[data-print]");
    if (pp) pp.addEventListener("click", function () { window.print(); });
  }

  /* ---------- Formulari de validació participativa ---------- */
  var fb = document.querySelector("[data-feedback]");
  if (fb) {
    fb.addEventListener("submit", function (e) {
      var errors = [];
      fb.querySelectorAll("[required]").forEach(function (f) {
        var ok = f.type === "radio" ? !!fb.querySelector('input[name="' + f.name + '"]:checked') : !!f.value.trim();
        f.setAttribute("aria-invalid", String(!ok));
        if (!ok && errors.indexOf(f.name) < 0) errors.push(f.name);
      });
      var errBox = fb.querySelector("[data-errors]");
      if (errors.length) {
        e.preventDefault();
        var first = fb.querySelector('[name="' + errors[0] + '"]');
        errBox.hidden = false;
        errBox.focus();
        if (first) first.setAttribute("aria-describedby", "fb-errors");
        return;
      }
      errBox.hidden = true;
      if (fb.getAttribute("action")) return; // s'envia al servidor configurat (FEEDBACK_ENDPOINT)
      e.preventDefault();
      var lines = [];
      fb.querySelectorAll("input, select, textarea").forEach(function (f) {
        if (!f.name || (f.type === "radio" && !f.checked) || (f.type === "checkbox" && !f.checked)) return;
        var label = "";
        var fs = f.closest("fieldset");
        if (f.type === "radio" || f.type === "checkbox") label = fs ? fs.querySelector("legend").textContent.trim() : f.name;
        else { var l = fb.querySelector('label[for="' + f.id + '"]'); label = l ? l.textContent.trim() : f.name; }
        var val = f.type === "radio" || f.type === "checkbox" ? f.closest("label").textContent.trim() : f.value.trim();
        if (val) lines.push(label + ": " + val);
      });
      var text = lines.join("\n");
      var out = document.querySelector("[data-feedback-out]");
      var ta = out.querySelector("textarea");
      ta.value = text;
      var mail = out.querySelector("[data-mail]");
      var email = fb.getAttribute("data-email");
      if (mail && email) {
        mail.href = "mailto:" + email + "?subject=" + encodeURIComponent(fb.getAttribute("data-subject") || "") + "&body=" + encodeURIComponent(text);
        mail.hidden = false;
      }
      out.hidden = false;
      var h = out.querySelector("h2");
      if (h) { h.setAttribute("tabindex", "-1"); h.focus(); }
    });
    var copy = document.querySelector("[data-copy]");
    if (copy) copy.addEventListener("click", function () {
      var ta = document.querySelector("[data-feedback-out] textarea");
      ta.select();
      var done = function () { copy.querySelector("span").textContent = copy.getAttribute("data-done"); };
      if (navigator.clipboard) navigator.clipboard.writeText(ta.value).then(done, function () { document.execCommand("copy"); done(); });
      else { document.execCommand("copy"); done(); }
    });
  }
})();
