"""Página socrática de Linterna (HTML+JS mínimo, sin build step).

Postura de diseño: evidencia primero. Las fuentes se muestran siempre; el veredicto hay
que pedirlo ("mostrame las fuentes y dejame pensar"). La abstención es una respuesta
válida, presentada con calma, no como error.
"""

from __future__ import annotations

PRIVACY_HTML = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Linterna — Política de privacidad</title>
<style>
  body{font-family:system-ui,sans-serif;max-width:720px;margin:0 auto;padding:48px 20px 80px;
       color:#1a1a1a;line-height:1.6;background:#fbfbfa;}
  h1{font-size:1.8rem;} h2{font-size:1.15rem;margin-top:28px;}
  .muted{color:#6b7280;} a{color:#2563eb;}
  code{background:#eef;padding:1px 5px;border-radius:4px;}
</style>
</head>
<body>
  <h1>Política de privacidad — Linterna 🔦</h1>
  <p class="muted">Última actualización: 2026-06-22</p>

  <p>Linterna es un servicio público y open-source de verificación de información. Esta
  política describe qué datos maneja el servicio web y la extensión de navegador.</p>

  <h2>Qué datos recibimos</h2>
  <p>Únicamente <strong>la afirmación (texto) que vos elegís verificar</strong> — ya sea
  escribiéndola en la web o seleccionándola en una página y usando el menú contextual de la
  extensión. Nada más.</p>

  <h2>Qué NO hacemos</h2>
  <ul>
    <li>No te pedimos cuenta, login ni datos personales.</li>
    <li>No guardamos datos personales identificables (<strong>cero PII</strong>): ninguna
    consulta se asocia a tu identidad.</li>
    <li>No usamos cookies de seguimiento, no hacemos perfiles, no mostramos publicidad.</li>
    <li>No vendemos ni cedemos datos a terceros con fines comerciales.</li>
  </ul>

  <h2>Cómo se procesa tu consulta</h2>
  <p>Para verificar una afirmación, el servicio consulta fuentes externas: la API de
  <strong>Google Fact Check Tools</strong> (verificaciones humanas previas), y —si no hay
  verificación previa— el buscador <strong>Brave Search</strong> (evidencia) y el modelo
  <strong>Google Gemini</strong> (razonamiento sobre esa evidencia). El texto de tu
  afirmación se envía a esos servicios solo para resolver la consulta; su tratamiento se
  rige por las políticas de cada proveedor. La evidencia recuperada de Brave no se persiste.</p>

  <h2>Almacenamiento</h2>
  <p>Se cachea la afirmación y su resultado de verificación (sin identidad asociada) para
  no repetir trabajo. Ningún registro contiene texto identificable del usuario.</p>

  <h2>La extensión</h2>
  <p>La extensión solo envía el texto que seleccionás a este servicio de Linterna. Guarda
  localmente (en tu navegador) la dirección del servicio configurada. No accede a otros
  datos de las páginas que visitás.</p>

  <h2>Código abierto</h2>
  <p>El método es público y auditable. Podés revisar exactamente qué hace el código.</p>

  <h2>Contacto</h2>
  <p>Ante dudas o para reportar un problema, escribí a
  <a href="mailto:greutemann@gmail.com">greutemann@gmail.com</a>.</p>
</body>
</html>
"""

INDEX_HTML = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Linterna — verificación de información</title>
<style>
  :root { --bg:#fbfbfa; --fg:#1a1a1a; --muted:#6b7280; --line:#e5e7eb; --accent:#2563eb; }
  * { box-sizing: border-box; }
  body { margin:0; font-family: system-ui, sans-serif; background:var(--bg); color:var(--fg);
         line-height:1.5; }
  main { max-width: 680px; margin: 0 auto; padding: 48px 20px 80px; }
  h1 { font-size: 1.9rem; margin: 0 0 4px; }
  .tag { color: var(--muted); margin: 0 0 28px; }
  form { display:flex; gap:8px; }
  input { flex:1; padding:12px 14px; font-size:1rem; border:1px solid var(--line);
          border-radius:10px; background:#fff; }
  button { padding:12px 18px; font-size:1rem; border:0; border-radius:10px;
           background:var(--accent); color:#fff; cursor:pointer; }
  button.ghost { background:transparent; color:var(--accent); border:1px solid var(--accent); }
  #out { margin-top:28px; }
  .card { border:1px solid var(--line); border-radius:12px; padding:18px 20px; background:#fff;
          margin-bottom:14px; }
  .lead { font-size:.85rem; text-transform:uppercase; letter-spacing:.04em; color:var(--muted);
          margin:0 0 10px; }
  .src { padding:10px 0; border-top:1px solid var(--line); }
  .src:first-child { border-top:0; }
  .src a { color:var(--accent); text-decoration:none; font-weight:600; }
  .src .pub { color:var(--muted); font-size:.85rem; }
  .dot { display:inline-block; width:12px; height:12px; border-radius:50%; margin-right:8px;
         vertical-align:middle; }
  .verde{background:#16a34a;} .amarillo{background:#d97706;} .rojo{background:#dc2626;}
  .gris{background:#9ca3af;}
  .verdict { font-size:1.3rem; font-weight:700; text-transform:capitalize; }
  .note { color:var(--muted); font-size:.9rem; margin-top:10px; }
  .muted { color:var(--muted); }
  .asked { border-left:3px solid var(--accent); padding:6px 0 6px 14px; margin:0 0 16px;
           font-size:1.05rem; }
  .asked .lbl { display:block; color:var(--muted); font-size:.78rem; text-transform:uppercase;
                letter-spacing:.04em; margin-bottom:2px; }
</style>
</head>
<body>
<main>
  <h1>Linterna 🔦</h1>
  <p class="tag">No es un oráculo. Te muestra las fuentes; la conclusión es tuya.</p>

  <form id="f">
    <input id="claim" placeholder="Pegá una afirmación para verificar…" autocomplete="off"/>
    <button type="submit">Buscar evidencia</button>
  </form>

  <div id="out"></div>
</main>

<script>
const f = document.getElementById('f');
const out = document.getElementById('out');

f.addEventListener('submit', async (e) => {
  e.preventDefault();
  const claim = document.getElementById('claim').value.trim();
  if (!claim) return;
  out.innerHTML = '<p class="muted">Buscando evidencia…</p>';
  try {
    const r = await fetch('/api/verify', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({claim})
    });
    if (!r.ok) { out.innerHTML = '<p class="muted">No se pudo verificar ahora. Probá de nuevo.</p>'; return; }
    render(await r.json(), claim);
  } catch { out.innerHTML = '<p class="muted">Error de conexión.</p>'; }
});

function asked(claim) {
  return `<p class="asked"><span class="lbl">Afirmación consultada</span>${escapeHtml(claim)}</p>`;
}

function render(d, claim) {
  if (d.is_abstention) {
    out.innerHTML = asked(claim) + `<div class="card">
      <p class="lead">Sin evidencia suficiente</p>
      <p>No encontramos verificaciones ni evidencia validada para concluir.
         <strong>Y eso es una respuesta válida</strong>, no una falla.</p>
      <p class="note">${escapeHtml(d.explanation)}</p>
    </div>`;
    return;
  }

  const sources = d.sources.map(s => `
    <div class="src">
      <a href="${encodeURI(s.url)}" target="_blank" rel="noopener">${escapeHtml(s.title || s.url)}</a>
      <div class="pub">${escapeHtml(s.publisher)}${s.reviewed_at ? ' · ' + escapeHtml(s.reviewed_at) : ''}</div>
    </div>`).join('');

  out.innerHTML = asked(claim) + `
    <div class="card">
      <p class="lead">Esto es lo que encontramos — leelo y formá tu criterio</p>
      ${sources}
    </div>
    <button class="ghost" id="reveal">Mostrar lo que concluyen las fuentes →</button>
    <div id="v"></div>`;

  document.getElementById('reveal').addEventListener('click', (e) => {
    e.target.style.display = 'none';
    document.getElementById('v').innerHTML = `<div class="card">
      <p><span class="dot ${escapeHtml(d.light)}"></span><span class="verdict">${escapeHtml(d.verdict)}</span></p>
      <p>${escapeHtml(d.explanation)}</p>
      <p class="note">Esto es lo que concluyen las fuentes citadas. La decisión final es tuya.</p>
    </div>`;
  });
}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, c =>
    ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
</script>
</body>
</html>
"""
