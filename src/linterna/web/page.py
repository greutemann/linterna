"""Página socrática de Linterna (HTML+JS mínimo, sin build step).

Postura de diseño: evidencia primero. Las fuentes se muestran siempre; el veredicto hay
que pedirlo ("mostrame las fuentes y dejame pensar"). La abstención es una respuesta
válida, presentada con calma, no como error.
"""

from __future__ import annotations

ESQUEMA_HTML = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Linterna — Esquema de verificación</title>
<style>
  body{font-family:system-ui,sans-serif;max-width:760px;margin:0 auto;padding:48px 20px 80px;
       color:#1a1a1a;line-height:1.6;background:#fbfbfa;}
  h1{font-size:1.9rem;} h2{font-size:1.2rem;margin-top:32px;}
  .muted{color:#6b7280;} a{color:#2563eb;}
  code{background:#eef;padding:1px 5px;border-radius:4px;}
  .step{border-left:3px solid #2563eb;padding:4px 0 4px 16px;margin:14px 0;}
  .dot{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:6px;vertical-align:middle;}
  .verde{background:#16a34a;}.rojo{background:#dc2626;}.gris{background:#9ca3af;}
  table{border-collapse:collapse;width:100%;margin-top:8px;} td,th{border:1px solid #e5e7eb;padding:8px;text-align:left;}
  .back{margin-bottom:20px;display:inline-block;}
</style>
</head>
<body>
  <a class="back" href="/">← Volver</a>
  <h1>Esquema de verificación 🔦</h1>
  <p class="muted">Cómo trabaja el framework de Linterna, en detalle. El método es público
  y auditable — esa es la idea: la confianza vive en el método, no en el modelo de IA.</p>

  <h2>Principio: no es un oráculo</h2>
  <p>Linterna no te da "la verdad". Te muestra qué dicen las fuentes y te devuelve la decisión.
  Cuando no sabe, lo dice. Un veredicto firme solo aparece cuando lo respalda una verificación
  hecha por humanos; sobre todo lo demás, la herramienta aporta evidencia sin sentenciar.</p>

  <h2>Los dos caminos</h2>
  <div class="step"><strong>1. Archivo-primero (verificación humana).</strong> Ante una
  afirmación, primero busca si periodistas y organizaciones de fact-checking ya la verificaron
  (vía ClaimReview / Google Fact Check). Si existe —y habla de la misma afirmación—, muestra
  su veredicto (<span class="dot verde"></span>verdadero / <span class="dot rojo"></span>falso)
  con sus fuentes y fecha. La mayoría de las falsedades se reciclan: muchas se resuelven acá.</div>

  <div class="step"><strong>2. Agente investigador (evidencia fresca).</strong> Si nadie la
  verificó antes, recupera evidencia de la web, descartando fuentes marginales o
  desinformantes y priorizando las confiables.</div>

  <h2>Cautela asimétrica (la regla clave del agente)</h2>
  <p>Desde evidencia web, el agente puede <strong>desmentir</strong> pero
  <strong>nunca afirmar</strong>:</p>
  <table>
    <tr><th>Situación</th><th>Qué hace</th></tr>
    <tr><td>Fuentes confiables <strong>contradicen</strong> la afirmación</td>
        <td><span class="dot rojo"></span>La desmiente, con sus fuentes</td></tr>
    <tr><td>La evidencia <strong>parecería respaldarla</strong></td>
        <td>NO la afirma: ofrece fuentes confiables para que investigues</td></tr>
    <tr><td>Disputado / sin evidencia confiable</td>
        <td><span class="dot gris"></span>Fuentes-guía o abstención</td></tr>
  </table>
  <p class="muted">¿Por qué asimétrica? Desmentir una falsedad con un contraejemplo confiable
  es seguro y útil. Confirmar una afirmación —sobre todo si es cargada o sensible— desde unos
  resultados de búsqueda es donde anida el daño (puede reforzar un sesgo aplastando el matiz).
  Por eso afirmar requiere verificación humana, no la palabra del modelo.</p>

  <h2>Garantías de código (no dependen del modelo)</h2>
  <ul>
    <li><strong>Validación de citas determinística:</strong> el código —no el modelo— verifica
    que cada fuente citada sea real y efectivamente recuperada. Cita inventada = rechazada.</li>
    <li><strong>Curaduría de fuentes:</strong> los dominios se clasifican en confiabilidad
    alta / desconocida / descartada. Las descartadas no se usan; un desmentido exige al menos
    una fuente de alta confiabilidad. Las listas son públicas y versionadas.</li>
    <li><strong>El modelo razona solo sobre evidencia recuperada</strong>, nunca aporta datos
    de su entrenamiento, y a temperatura 0 para fidelidad.</li>
    <li><strong>Abstención válida:</strong> sin evidencia confiable, lo dice. No inventar es
    una respuesta correcta, no una falla.</li>
  </ul>

  <h2>Privacidad</h2>
  <p>No se persisten datos personales de quien consulta; ninguna consulta se asocia a tu
  identidad. Ver la <a href="/privacy">política de privacidad</a>.</p>

  <h2>Abierto y corregible</h2>
  <p>El código es abierto de punta a punta (AGPL-3.0). La herramienta comete errores y los
  corrige a la vista de todos; cualquiera puede reportar uno.</p>
  <p>
    <a href="https://github.com/greutemann/linterna" target="_blank" rel="noopener">Código en GitHub →</a>
    &nbsp;·&nbsp;
    <a href="https://github.com/greutemann/linterna/wiki" target="_blank" rel="noopener">Wiki (documentación) →</a>
  </p>
</body>
</html>
"""

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
  .verdict { font-size:1.2rem; font-weight:700; }
  .bar { height:10px; border-radius:6px; background:#eee; overflow:hidden; margin:10px 0 4px; }
  .fill { height:100%; border-radius:6px; }
  .fill.verde{background:#16a34a;} .fill.amarillo{background:#d97706;}
  .fill.rojo{background:#dc2626;} .fill.gris{background:#9ca3af;}
  .note { color:var(--muted); font-size:.9rem; margin-top:10px; }
  .muted { color:var(--muted); }
  .how { margin-top:40px; border:1px solid var(--line); border-radius:12px; padding:6px 18px;
         background:#fff; }
  .how summary { cursor:pointer; padding:12px 0; font-weight:600; }
  .how ol { padding-left:20px; } .how li { margin:8px 0; }
  .foot { margin-top:28px; font-size:.85rem; }
  .foot a { color:var(--accent); text-decoration:none; }
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

  <details class="how">
    <summary>¿Cómo verificamos? <span class="muted">(y por qué no somos un oráculo)</span></summary>
    <p>Linterna no te da “la verdad”. Te muestra qué dicen las fuentes y te deja decidir.
       Así trabaja, paso a paso:</p>
    <ol>
      <li><strong>Primero, el archivo.</strong> Busca si periodistas y organizaciones de
          verificación ya chequearon esa afirmación. Si existe, te muestra su veredicto y el
          enlace. (La mayoría de las falsedades se reciclan: muchas se resuelven acá.)</li>
      <li><strong>Si nadie la verificó antes, busca evidencia.</strong> Recupera fuentes de
          la web sobre el tema.</li>
      <li><strong>Un modelo de IA razona solo sobre esa evidencia.</strong> Nunca aporta
          datos de su “memoria”: ordena y explica lo que las fuentes dicen, nada más.</li>
      <li><strong>Validación automática de citas.</strong> Antes de mostrarte nada, el código
          comprueba que cada fuente citada sea real y efectivamente encontrada. Una cita
          inventada se rechaza.</li>
      <li><strong>Si no alcanza, se abstiene.</strong> Cuando no hay evidencia suficiente te
          lo dice (“insuficiente”). Preferimos no responder antes que inventar.</li>
    </ol>
    <p class="muted">La confianza vive en este método —público y auditable—, no en el modelo
       de IA, que es reemplazable. Código abierto de punta a punta.</p>
    <p><a href="/esquema">Ver el esquema de verificación completo →</a></p>
  </details>

  <footer class="foot">
    <a href="/esquema">Cómo funciona</a> ·
    <a href="/privacy">Privacidad</a> ·
    <a href="https://github.com/greutemann/linterna" target="_blank" rel="noopener">Código en GitHub</a> ·
    <span class="muted">Servicio público · cero PII · open-source (AGPL-3.0)</span>
  </footer>
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

function sourcesHtml(list) {
  return (list || []).map(s => `
    <div class="src">
      <a href="${encodeURI(s.url)}" target="_blank" rel="noopener">${escapeHtml(s.title || s.url)}</a>
      <div class="pub">${escapeHtml(s.publisher)}${s.reviewed_at ? ' · ' + escapeHtml(s.reviewed_at) : ''}</div>
    </div>`).join('');
}

function render(d, claim) {
  if (d.is_abstention) {
    const hasLeads = d.sources && d.sources.length;
    if (hasLeads) {
      // Sin verificación humana, pero hay fuentes confiables para empezar a investigar.
      out.innerHTML = asked(claim) + `
        <div class="card">
          <p class="lead">Sin verificación humana — fuentes para investigar</p>
          <p class="note">${escapeHtml(d.explanation)}</p>
          ${sourcesHtml(d.sources)}
        </div>`;
    } else {
      out.innerHTML = asked(claim) + `<div class="card">
        <p class="lead">Sin evidencia suficiente</p>
        <p>No encontramos verificaciones ni evidencia validada para concluir.
           <strong>Y eso es una respuesta válida</strong>, no una falla.</p>
        <p class="note">${escapeHtml(d.explanation)}</p>
      </div>`;
    }
    return;
  }

  out.innerHTML = asked(claim) + `
    <div class="card">
      <p class="lead">Esto es lo que encontramos — leelo y formá tu criterio</p>
      ${sourcesHtml(d.sources)}
    </div>
    <button class="ghost" id="reveal">Mostrar lo que concluyen las fuentes →</button>
    <div id="v"></div>`;

  document.getElementById('reveal').addEventListener('click', (e) => {
    e.target.style.display = 'none';
    const bar = (d.support_pct != null)
      ? `<div class="bar"><div class="fill ${escapeHtml(d.light)}" style="width:${d.support_pct}%"></div></div>
         <p class="muted">≈${d.support_pct}% de la evidencia confiable respalda la afirmación</p>`
      : '';
    document.getElementById('v').innerHTML = `<div class="card">
      <p><span class="dot ${escapeHtml(d.light)}"></span><span class="verdict">${escapeHtml(d.label)}</span></p>
      ${bar}
      <p>${escapeHtml(d.explanation)}</p>
      <p class="note">Esto es lo que dicen las fuentes${d.kind === 'archivo' ? ' que ya verificaron esto' : ' confiables'}. La conclusión es tuya.</p>
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
