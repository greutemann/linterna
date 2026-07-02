# Fuentes confiables (curaduría)

Para *aportar* sin equivocar, el agente no razona sobre cualquier resultado de la web:
clasifica los dominios por confiabilidad. Esta curaduría es **pública y versionada**
(`src/linterna/evidence/reliability.py`), como manda el invariante 5.

## Tres niveles
- **Alta (`HIGH`):** instituciones científicas y oficiales, enciclopedias, agencias de
  fact-checking y medios establecidos. Pueden sostener un desmentido.
- **Descartada (`DENY`):** fuentes conocidas por desinformación/pseudociencia. Se excluyen;
  ni se muestran.
- **Desconocida (`UNKNOWN`):** el resto. Sirven como contexto o punto de partida, pero **no**
  sostienen por sí solas una conclusión fuerte.

## Reglas que aplican
- Las `DENY` se descartan **antes** de razonar.
- Un **desmentido** (🔴) exige al menos una fuente de confiabilidad **alta**.
- Si solo hay fuentes desconocidas, el agente ofrece **fuentes-guía** para investigar, sin
  veredicto.

## Cómo proponer cambios
Las listas son deliberadamente conservadoras y **ampliables por la comunidad**. Si creés que
falta una fuente confiable (o que sobra una), abrí un *issue* o un *pull request* editando
`_HIGH` / `_DENY` en `reliability.py`, con una breve justificación. Criterios sugeridos para
"alta": reputación editorial verificable, correcciones públicas, y foco en evidencia.

Ver también: [[Esquema de verificación]] · [[Contribuir]]
