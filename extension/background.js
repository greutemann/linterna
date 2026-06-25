// Service worker: menú contextual + consulta a la API + inyección del panel a demanda.
//
// No usa content scripts ni permisos de host amplios (<all_urls>). El panel se inyecta
// con chrome.scripting SOLO en la pestaña donde el usuario activa el gesto, gracias a
// activeTab. Mínimo acceso posible (coherente con la privacidad de Linterna).

const DEFAULT_ENDPOINT = "http://127.0.0.1:8000";
const MENU_ID = "linterna-verify";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: MENU_ID,
    title: "Verificar con Linterna 🔦",
    contexts: ["selection"],
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== MENU_ID || !info.selectionText || !tab || !tab.id) return;

  const claim = info.selectionText.trim();
  if (!claim) return;

  await render(tab.id, { type: "loading", claim });

  try {
    const endpoint = await getEndpoint();
    const r = await fetch(endpoint + "/api/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ claim }),
    });
    if (!r.ok) throw new Error("HTTP " + r.status);
    const data = await r.json();
    await render(tab.id, { type: "result", claim, data });
  } catch (e) {
    await render(tab.id, { type: "error", claim, message: String(e && e.message ? e.message : e) });
  }
});

function render(tabId, msg) {
  return chrome.scripting.executeScript({
    target: { tabId },
    func: showPanel,
    args: [msg],
  }).catch(() => {});
}

function getEndpoint() {
  return new Promise((resolve) => {
    chrome.storage.sync.get({ endpoint: DEFAULT_ENDPOINT }, (v) => resolve(v.endpoint));
  });
}

// --- Función autocontenida que corre EN la página (se serializa e inyecta) ---------
// Crea/actualiza un panel flotante en Shadow DOM. Idempotente: reusa el panel existente.
function showPanel(msg) {
  const HOST_ID = "linterna-host";
  let host = document.getElementById(HOST_ID);

  if (!host) {
    host = document.createElement("div");
    host.id = HOST_ID;
    host.style.cssText = "position:fixed;top:16px;right:16px;z-index:2147483647;";
    const root = host.attachShadow({ mode: "open" });
    root.innerHTML = `
      <style>
        .box{width:360px;max-height:80vh;overflow:auto;background:#fff;color:#1a1a1a;
          font-family:system-ui,sans-serif;font-size:14px;line-height:1.5;border:1px solid #e5e7eb;
          border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.18);padding:16px;}
        .top{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;}
        .brand{font-weight:700;} .x{cursor:pointer;border:0;background:none;font-size:18px;color:#6b7280;}
        .asked{border-left:3px solid #2563eb;padding:4px 0 4px 12px;margin:6px 0 12px;}
        .asked .lbl{display:block;color:#6b7280;font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;}
        .lead{font-size:.74rem;text-transform:uppercase;letter-spacing:.04em;color:#6b7280;margin:0 0 8px;}
        .src{padding:8px 0;border-top:1px solid #eee;} .src:first-of-type{border-top:0;}
        .src a{color:#2563eb;text-decoration:none;font-weight:600;} .pub{color:#6b7280;font-size:.82rem;}
        .dot{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:7px;vertical-align:middle;}
        .verde{background:#16a34a;}.amarillo{background:#d97706;}.rojo{background:#dc2626;}.gris{background:#9ca3af;}
        .verdict{font-weight:700;}
        .bar{height:10px;border-radius:6px;background:#eee;overflow:hidden;margin:10px 0 4px;}
        .fill{height:100%;border-radius:6px;}
        .note{color:#6b7280;font-size:.85rem;margin-top:8px;} .muted{color:#6b7280;}
        button.ghost{margin-top:10px;padding:8px 12px;border:1px solid #2563eb;background:none;color:#2563eb;
          border-radius:8px;cursor:pointer;}
        .card{border:1px solid #e5e7eb;border-radius:10px;padding:12px 14px;margin-top:8px;}
      </style>
      <div class="box">
        <div class="top"><span class="brand">Linterna 🔦</span><button class="x" id="x">×</button></div>
        <div id="body"></div>
      </div>`;
    root.getElementById("x").addEventListener("click", () => host.remove());
    document.body.appendChild(host);
  }

  const root = host.shadowRoot;
  const body = root.getElementById("body");
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const asked = (c) => `<p class="asked"><span class="lbl">Afirmación consultada</span>${esc(c)}</p>`;

  if (msg.type === "loading") {
    body.innerHTML = asked(msg.claim) + `<p class="muted">Buscando evidencia…</p>`;
    return;
  }
  if (msg.type === "error") {
    body.innerHTML = asked(msg.claim) +
      `<p class="muted">No se pudo verificar. ¿Está corriendo el servicio de Linterna?</p>`;
    return;
  }

  const d = msg.data;
  if (d.is_abstention) {
    body.innerHTML = asked(msg.claim) + `<div class="card">
      <p class="lead">Sin evidencia suficiente</p>
      <p>No hay verificaciones ni evidencia validada para concluir.
      <strong>Y eso es una respuesta válida</strong>, no una falla.</p>
      <p class="note">${esc(d.explanation)}</p></div>`;
    return;
  }

  const sources = (d.sources || []).map((s) => `
    <div class="src">
      <a href="${encodeURI(s.url)}" target="_blank" rel="noopener">${esc(s.title || s.url)}</a>
      <div class="pub">${esc(s.publisher)}${s.reviewed_at ? " · " + esc(s.reviewed_at) : ""}</div>
    </div>`).join("");

  body.innerHTML = asked(msg.claim) +
    `<div class="card"><p class="lead">Esto es lo que encontramos — leelo y formá tu criterio</p>${sources}</div>
     <button class="ghost" id="reveal">Mostrar lo que concluyen las fuentes →</button>
     <div id="v"></div>`;

  root.getElementById("reveal").addEventListener("click", (e) => {
    e.target.style.display = "none";
    const bar = (d.support_pct != null)
      ? `<div class="bar"><div class="fill ${esc(d.light)}" style="width:${d.support_pct}%"></div></div>
         <p class="muted">≈${d.support_pct}% de la evidencia confiable respalda la afirmación</p>`
      : "";
    root.getElementById("v").innerHTML = `<div class="card">
      <p><span class="dot ${esc(d.light)}"></span><span class="verdict">${esc(d.label)}</span></p>
      ${bar}
      <p>${esc(d.explanation)}</p>
      <p class="note">Esto es lo que dicen las fuentes${d.kind === "archivo" ? " que ya verificaron esto" : " confiables"}. La conclusión es tuya.</p></div>`;
  });
}
