# Proposal — Inversión determinística de veredicto por polaridad opuesta

## Problema (caso real)

Consulta: **"el hombre llegó a la Luna en 1969"** (verdadera, evidencia abrumadora).

El archivo (M1) encuentra el ClaimReview de Maldita.es sobre la afirmación **opuesta**:
«Stanley Kubrick confiesa que el alunizaje fue falso» → **Falso**.

Comportamientos observados:
1. **Antes del fix de polaridad:** aplicaba el veredicto tal cual → **ROJO "Falso"** sobre una
   afirmación verdadera. Inaceptable.
2. **Con el fix de polaridad (d1aac63):** detecta la inversión y se abstiene → **GRIS**.
   Seguro, pero pobre: la herramienta *tiene* la respuesta en la mano y no la usa.

## Insight

El corpus ClaimReview está sesgado por construcción: los verificadores humanos chequean
**la desinformación**, no los hechos verdaderos. Nadie fact-checkea "la Tierra gira alrededor
del Sol"; fact-checkean "la NASA admitió que la Tierra no gira". Por lo tanto, **gran parte
del valor del archivo está en polaridad invertida** respecto de consultas afirmativas.

Desaprovechar eso convierte respuestas conocidas en abstenciones.

## Propuesta

Cuando el ClaimReview relevante tiene **polaridad opuesta** a la consulta (detector de
marcadores ya existente: montaje/bulo/farsa/nunca/no/...), en lugar de abstenerse:

| Veredicto del ClaimReview (sobre la afirmación opuesta) | Resultado para la consulta |
|---|---|
| **Falso** (desmintieron lo contrario) | 🟢 **Verdadero** — "X desmintió la afirmación contraria" |
| **Verdadero** (confirmaron lo contrario) | 🔴 **Falso** — "X confirmó la afirmación contraria" |
| Engañoso / Disputado / no mapeable | ⚪ Se mantiene "verificación relacionada" (gris) |

Es **lógica proposicional simple aplicada por código** (¬A=Falso ⟹ A=Verdadero), 100%
determinística y auditable — consistente con el invariante 3 (la garantía es código, no
modelo). La explicación siempre muestra la afirmación exacta que se verificó y su
calificación original (transparencia total: el usuario ve la inversión, no se le oculta).

## Riesgos y mitigaciones

- **El detector de polaridad es heurístico** (marcadores léxicos). Mitigación: la inversión
  solo se aplica con veredictos nítidos (Falso/Verdadero); Engañoso/Disputado no se invierten
  (los matices no sobreviven una negación). Ante marcadores dobles o ambiguos ya hoy el
  detector tiende a marcar mismatch → gris, no inversión errada.
- **Doble negación** ("no es cierto que el alunizaje fuera un montaje"): los marcadores en
  ambos lados se cancelan en el detector actual (compara presencia relativa), y el peor caso
  es gris, no inversión.
- **Queda un límite honesto:** inversiones semánticas sin marcadores léxicos no se detectan.
  Ante la duda, el sistema sigue prefiriendo no sentenciar.

## Fuera de alcance (futuro)

- Chequeo semántico/NLI de equivalencia entre afirmaciones (rompería "M1 sin LLM"; podría
  vivir como paso opcional del agente M3).
- Usar múltiples ClaimReviews coincidentes para reforzar la confianza de la inversión.
