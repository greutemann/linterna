// Guarda/lee el endpoint de la API en chrome.storage.sync.
const DEFAULT_ENDPOINT = "http://127.0.0.1:8000";
const input = document.getElementById("endpoint");
const saved = document.getElementById("saved");

chrome.storage.sync.get({ endpoint: DEFAULT_ENDPOINT }, (v) => {
  input.value = v.endpoint;
});

document.getElementById("save").addEventListener("click", () => {
  const endpoint = (input.value || DEFAULT_ENDPOINT).trim().replace(/\/+$/, "");
  chrome.storage.sync.set({ endpoint }, () => {
    saved.textContent = "Guardado ✓";
    setTimeout(() => (saved.textContent = ""), 1500);
  });
});
