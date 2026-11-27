/* Baixa visió en xarxa — assistent de recursos (cercador conversacional tancat)
   Segueix l'arbre de decisions acordat a les sessions de cocreació (informe V2, apartat 4.2):
     Node 1: classificació del perfil (pacient, familiar o persona interessada, professional)
     Node 2: detecció de la necessitat (diagnòstic recent, patologia o símptoma, solucions pràctiques)
     Sortida: resposta empàtica i realista amb un màxim de 3 enllaços verificats.
   El corpus és exclusivament el contingut validat d'aquesta web (index-<idioma>.js, generat per
   build.py). No es fa servir cap model generatiu ni servei extern: cada frase de la resposta ha
   estat redactada i revisada per l'equip (src/data/assistant.json), de manera que no hi pot haver
   «al·lucinacions». La consulta no surt del navegador (excepte el dictat per veu, que gestiona
   el mateix navegador). */
(function () {
  "use strict";
  var IDX = window.BVX_INDEX || [];
  var A = window.BVX_ASSISTANT || {};
  var C = A.cfg || {};
  var root = document.querySelector("[data-assistant]");
  if (!root || !IDX.length) return;

  function norm(s) {
    return String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
      .replace(/l·l/g, "ll").replace(/[^a-z0-9]+/g, " ").trim();
  }
  var STOP = {};
  (C.stopwords || []).forEach(function (w) { STOP[norm(w)] = 1; });
  function tokens(s) {
    return norm(s).split(" ").filter(function (t) { return t.length > 2 && !STOP[t]; });
  }
  // Coincidència per arrel: «glaucomes» ~ «glaucoma», «il·luminació» ~ «il·luminar»
  function stemEq(a, b) {
    if (a === b) return true;
    var n = Math.min(a.length, b.length);
    if (n < 4) return false;
    var k = Math.max(4, Math.min(n, 6));
    return a.slice(0, k) === b.slice(0, k) && Math.abs(a.length - b.length) <= 4;
  }
  IDX.forEach(function (e) {
    e._t = tokens(e.t);
    e._x = tokens(e.x);
  });
  function has(list, tok) {
    for (var i = 0; i < list.length; i++) if (stemEq(list[i], tok)) return true;
    return false;
  }
  function countHits(q, words) {
    var nq = " " + norm(q) + " ", n = 0;
    (words || []).forEach(function (w) {
      var nw = norm(w);
      if (nw && nq.indexOf(" " + nw) >= 0) n += nw.indexOf(" ") > 0 ? 2 : 1;
    });
    return n;
  }
  function expand(qt) {
    var out = qt.slice();
    var syn = C.synonyms || {};
    Object.keys(syn).forEach(function (k) {
      var group = [k].concat(syn[k]).map(norm);
      if (qt.some(function (t) { return group.some(function (g) { return g.indexOf(" ") < 0 && stemEq(g, t); }); })) {
        group.forEach(function (g) { g.split(" ").forEach(function (p) { if (p.length > 2 && out.indexOf(p) < 0) out.push(p); }); });
      }
    });
    return out;
  }

  var form = root.querySelector("form");
  var input = root.querySelector("#as-q");
  var answer = root.querySelector("#as-answer");
  var micBtn = root.querySelector("#as-mic");

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function link(key, frag) {
    return (A.pages[key] || "") + (frag ? "#" + frag : "");
  }

  function run(q) {
    q = (q || "").trim();
    answer.innerHTML = "";
    if (!q) { answer.appendChild(el("p", "note", C.empty)); return; }

    // Node 1: perfil
    var chosen = (root.querySelector('input[name="as-profile"]:checked') || {}).value || "auto";
    var profile = chosen;
    if (chosen === "auto") {
      profile = "patient";
      var best = 0;
      ["family", "pro"].forEach(function (p) {
        var h = countHits(q, C.profiles[p].keywords);
        if (h > best) { best = h; profile = p; }
      });
    }
    var P = C.profiles[profile];

    // Node 2: necessitat (dins de l'àrea del perfil)
    var needs = P.needs || {};
    var need = null, bestN = 0;
    Object.keys(needs).forEach(function (n) {
      var h = countHits(q, needs[n].keywords);
      if (h > bestN) { bestN = h; need = n; }
    });

    // Recuperació sobre el corpus validat
    var qt = expand(tokens(q));
    var area = P.area;
    var needPages = need ? needs[need].pages : [];
    var scored = IDX.map(function (e) {
      var s = 0;
      qt.forEach(function (t) { if (has(e._t, t)) s += 3; else if (has(e._x, t)) s += 1; });
      if (s > 0) {
        if (e.z && e.z === area) s += 2;
        if (needPages.indexOf(e.k) >= 0) s += 3;
        if (e.u.indexOf("#") < 0) s -= 1; // millor una secció concreta que la pàgina sencera
      }
      return { e: e, s: s };
    }).filter(function (r) { return r.s >= 2; }).sort(function (a, b) { return b.s - a.s; });

    // Sense necessitat explícita: la dedueix del millor resultat
    if (!need && scored.length) {
      Object.keys(needs).forEach(function (n) {
        if (!need && needs[n].pages.indexOf(scored[0].e.k) >= 0) need = n;
      });
    }
    var N = need ? needs[need] : null;

    // Màxim 3 enllaços, preferentment de pàgines diferents; si cal, es completen amb la ruta acordada
    var picks = [], seenPages = {}, seenUrls = {};
    // Fins a 2 enllaços de la mateixa pàgina, perquè la resposta no quedi limitada a un sol tema
    scored.forEach(function (r) {
      if (picks.length < 3 && (seenPages[r.e.k] || 0) < 2 && !seenUrls[r.e.u]) {
        picks.push(r.e); seenPages[r.e.k] = (seenPages[r.e.k] || 0) + 1; seenUrls[r.e.u] = 1;
      }
    });
    var route = (N ? N.route : P.route) || [];
    route.forEach(function (ref) {
      if (picks.length >= 3) return;
      var parts = ref.split("#"), url = link(parts[0], parts[1]);
      if (seenUrls[url] || seenPages[parts[0]]) return;
      var hit = IDX.filter(function (e) { return e.u === url; })[0] || IDX.filter(function (e) { return e.k === parts[0]; })[0];
      if (hit) { picks.push(hit); seenPages[parts[0]] = 1; seenUrls[url] = 1; }
    });

    // Resposta
    var urgent = countHits(q, C.urgent_keywords) > 0;
    if (urgent) {
      var u = el("div", "callout callout--small");
      u.setAttribute("role", "note");
      var up = el("p");
      up.appendChild(el("strong", null, C.urgent_title + " "));
      up.appendChild(document.createTextNode(C.urgent_text + " "));
      var ua = el("a", null, C.urgent_link);
      ua.href = link(C.urgent_target.split("#")[0], C.urgent_target.split("#")[1]);
      up.appendChild(ua);
      u.appendChild(up);
      answer.appendChild(u);
    }
    var h = el("h2", null, C.answer_title);
    h.id = "as-answer-title";
    answer.appendChild(h);
    var meta = el("p", "assistant__route");
    meta.textContent = C.route_label + " " + P.label + (N ? " · " + N.label : "") + ". " + C.route_change;
    answer.appendChild(meta);
    answer.appendChild(el("p", "assistant__intro-answer", (N ? N.intro : P.intro)));
    if (picks.length) {
      var ol = el("ol", "assistant__results");
      picks.forEach(function (e) {
        var li = el("li");
        var a = el("a", null, e.t);
        a.href = e.u;
        li.appendChild(a);
        if (e.t !== e.p) li.appendChild(el("span", "assistant__page", " — " + e.p));
        li.appendChild(el("p", null, e.s));
        ol.appendChild(li);
      });
      answer.appendChild(ol);
    } else {
      answer.appendChild(el("p", null, C.no_results));
    }
    answer.appendChild(el("p", "note", C.closing));
    answer.focus();
  }

  form.addEventListener("submit", function (e) { e.preventDefault(); run(input.value); });
  root.querySelectorAll("[data-example]").forEach(function (b) {
    b.addEventListener("click", function () { input.value = b.textContent; run(input.value); });
  });
  root.querySelectorAll('input[name="as-profile"]').forEach(function (r) {
    r.addEventListener("change", function () { if (input.value.trim()) run(input.value); });
  });
  var m = location.search.match(/[?&]q=([^&#]*)/);
  if (m) { input.value = decodeURIComponent(m[1].replace(/\+/g, " ")); run(input.value); }

  // Entrada per veu (si el navegador la permet)
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SR && micBtn) {
    micBtn.hidden = false;
    var rec = null;
    micBtn.addEventListener("click", function () {
      if (rec) { rec.stop(); return; }
      rec = new SR();
      rec.lang = { ca: "ca-ES", es: "es-ES", en: "en-GB" }[document.documentElement.lang] || "ca-ES";
      rec.interimResults = false;
      rec.maxAlternatives = 1;
      micBtn.setAttribute("aria-pressed", "true");
      micBtn.querySelector("span").textContent = C.mic_listening;
      rec.onresult = function (ev) { input.value = ev.results[0][0].transcript; run(input.value); };
      rec.onend = rec.onerror = function () {
        rec = null;
        micBtn.setAttribute("aria-pressed", "false");
        micBtn.querySelector("span").textContent = C.mic;
      };
      rec.start();
    });
  }
})();
