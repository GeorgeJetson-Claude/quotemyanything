/*
 * QMA Chat Widget — free, self-contained, no backend, no monthly fee.
 * Rule-based assistant that answers common questions and routes visitors
 * straight to the right quote form. Replaces paid chat tools (e.g. Tidio).
 *
 * USAGE: add to any page before </body>:
 *   <script src="assets/js/qma-chat.js"></script>
 *
 * UPGRADE PATH (when revenue covers it):
 *   Swap answerFor() to call Grok or Claude API for free-form replies.
 *   Pipe transcripts to Zapier (already connected) for lead capture/CRM.
 *   Keep the rule-based answers as instant fallbacks (lean + fast).
 */
(function () {
  "use strict";

  var SERVICES = {
    roof: "roofing.html", hail: "roofing.html", shingle: "roofing.html",
    hvac: "hvac.html", "ac": "hvac.html", "air condition": "hvac.html", furnace: "hvac.html",
    plumb: "plumbing.html", leak: "plumbing.html", "water heater": "plumbing.html",
    solar: "solar.html", lawn: "lawn-care.html", landscap: "lawn-care.html",
    paint: "painting.html", electric: "electrical.html", outlet: "electrical.html",
    pest: "pest-control.html", roach: "pest-control.html", termite: "pest-control.html",
    tree: "tree-service.html", stump: "tree-service.html",
    moving: "moving.html", mover: "moving.html",
    clean: "house-cleaning.html", pool: "index.html#quick-form"
  };

  function answerFor(text) {
    var t = text.toLowerCase();
    if (/free|cost|price|how much|charge/.test(t))
      return "It's <b>100% free for homeowners</b> — no signup, no credit card. " +
             "Up to 3 local licensed pros compete for your job, and you pick the best price.";
    if (/how|work|process|step/.test(t))
      return "Easy: tell us what you need + your ZIP, we match you with up to 3 local pros, " +
             "and they send competing quotes — usually same day. Takes about 60 seconds.";
    if (/spam|safe|privacy|data|sell/.test(t))
      return "No spam ever. Your info only goes to the pros matched for your job. " +
             "We never sell your data. Reply STOP anytime.";
    if (/contractor|pro|business|sign up|leads/.test(t))
      return "Service pros: get pre-qualified local leads on <b>for-pros.html</b> — " +
             "pay per real lead or a flat monthly plan. <a href='for-pros.html'>See pro plans →</a>";
    for (var kw in SERVICES) {
      if (t.indexOf(kw) !== -1)
        return "Great — for that, head to our quick form here: " +
               "<a href='" + SERVICES[kw] + "'>Get free " + kw + " quotes →</a> (60 seconds, free).";
    }
    return "I can get you free quotes on roofing, HVAC, plumbing, solar, lawn, painting, " +
           "electrical, pest, tree, moving, cleaning and more. What do you need a quote for?";
  }

  function el(tag, css, html) {
    var e = document.createElement(tag);
    if (css) e.style.cssText = css;
    if (html != null) e.innerHTML = html;
    return e;
  }

  function init() {
    var open = false;
    var bubble = el("button", "position:fixed;bottom:84px;right:16px;z-index:60;width:56px;height:56px;border-radius:50%;border:none;cursor:pointer;background:#10b981;color:#fff;font-size:24px;box-shadow:0 8px 24px rgba(16,185,129,.4)", "💬");
    bubble.setAttribute("aria-label", "Chat with QMA");

    var panel = el("div", "display:none;position:fixed;bottom:150px;right:16px;z-index:60;width:320px;max-width:90vw;background:#1e293b;border:1px solid #334155;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,.5);overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif");
    var head = el("div", "background:#0f172a;color:#f1f5f9;padding:14px 16px;font-weight:700;font-size:14px;border-bottom:1px solid #334155", "QMA Assistant <span style='color:#94a3b8;font-weight:400'>· Free Quotes On Anything!</span>");
    var log = el("div", "padding:14px;height:260px;overflow:auto;font-size:13px;color:#f1f5f9;line-height:1.5");
    var row = el("div", "display:flex;border-top:1px solid #334155");
    var input = el("input", "flex:1;padding:12px;background:#0f172a;border:none;color:#f1f5f9;font-size:14px;outline:none");
    input.placeholder = "Ask or type a service…";
    var send = el("button", "background:#10b981;color:#fff;border:none;padding:0 16px;cursor:pointer;font-weight:700", "→");

    function add(who, html) {
      var m = el("div", "margin-bottom:10px;" + (who === "you" ? "text-align:right" : ""));
      m.innerHTML = "<span style='display:inline-block;padding:8px 12px;border-radius:12px;background:" +
        (who === "you" ? "#10b981;color:#fff" : "#0f172a;color:#f1f5f9") + "'>" + html + "</span>";
      log.appendChild(m); log.scrollTop = log.scrollHeight;
    }
    function ask() {
      var v = input.value.trim(); if (!v) return;
      add("you", v); input.value = "";
      setTimeout(function () { add("bot", answerFor(v)); }, 250);
    }
    send.onclick = ask;
    input.addEventListener("keydown", function (e) { if (e.key === "Enter") ask(); });
    bubble.onclick = function () {
      open = !open; panel.style.display = open ? "block" : "none";
      if (open && !log.childNodes.length)
        add("bot", "Hey! 👋 I'm the QMA assistant. Tell me what you need a quote for — it's free and takes 60 seconds.");
    };

    row.appendChild(input); row.appendChild(send);
    panel.appendChild(head); panel.appendChild(log); panel.appendChild(row);
    document.body.appendChild(bubble); document.body.appendChild(panel);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
