// Guarda/lee el endpoint de la API en chrome.storage.sync.
const DEFAULT_ENDPOINT = "https://linterna-498857011078.southamerica-east1.run.app";
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
