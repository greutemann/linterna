// Service worker: arma el menú contextual y consulta la API de Linterna.
// El fetch sale desde acá con host_permissions, así que no hace falta CORS en el server.

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

  send(tab.id, { type: "linterna:loading", claim });

  try {
    const endpoint = await getEndpoint();
    const r = await fetch(endpoint + "/api/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ claim }),
    });
    if (!r.ok) throw new Error("HTTP " + r.status);
    const data = await r.json();
    send(tab.id, { type: "linterna:result", claim, data });
  } catch (e) {
    send(tab.id, { type: "linterna:error", claim, message: String(e && e.message ? e.message : e) });
  }
});

function send(tabId, msg) {
  chrome.tabs.sendMessage(tabId, msg).catch(() => {
    // El content script puede no estar inyectado (página abierta antes de instalar
    // la extensión). En ese caso, recargá la pestaña.
  });
}

function getEndpoint() {
  return new Promise((resolve) => {
    chrome.storage.sync.get({ endpoint: DEFAULT_ENDPOINT }, (v) => resolve(v.endpoint));
  });
}
