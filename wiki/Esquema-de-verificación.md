# Esquema de verificación

Cómo Linterna resuelve una afirmación, paso a paso. Hace cumplir los [[Invariantes]].

## Principio: no es un oráculo
Linterna no te da "la verdad". Te muestra qué dicen las fuentes y te devuelve la decisión.
Un veredicto firme solo aparece cuando lo respalda una verificación **hecha por humanos**;
sobre todo lo demás, aporta evidencia sin sentenciar.

## Los dos caminos

### 1. Archivo-primero (verificación humana)
Primero busca si periodistas y organizaciones de fact-checking ya verificaron la afirmación
(vía ClaimReview / Google Fact Check). Si existe **y habla de la misma afirmación** (hay un
control de similitud para no aplicar el veredicto de un chequeo vecino de otro tema), muestra
su veredicto —🟢 verdadero / 🔴 falso— con sus fuentes y fecha. La mayoría de las falsedades
se reciclan: muchas se resuelven acá.

### 2. Agente investigador (evidencia fresca)
Si nadie la verificó antes, recupera evidencia de la web, descartando fuentes marginales o
desinformantes y priorizando las confiables (ver [[Fuentes confiables]]).

## Cautela asimétrica (la regla clave del agente)
Desde evidencia web, el agente puede **desmentir** pero **nunca afirmar**:

| Situación | Qué hace |
|---|---|
| Fuentes confiables **contradicen** la afirmación | 🔴 La desmiente, con sus fuentes |
| La evidencia **parecería respaldarla** | NO la afirma: ofrece fuentes confiables para investigar |
| Disputado / sin evidencia confiable | ⚪ Fuentes-guía o abstención |

**¿Por qué asimétrica?** Desmentir una falsedad con un contraejemplo confiable es seguro y
útil. Confirmar una afirmación —sobre todo si es cargada o sensible— desde unos resultados de
búsqueda es donde anida el daño (puede reforzar un sesgo aplastando el matiz). Por eso afirmar
requiere verificación humana, no la palabra del modelo. *(Esta regla nació de un incidente
real: el agente llegó a presentar como "respaldada" una afirmación racista leyendo una brecha
de tests y omitiendo que las fuentes la atribuyen a factores ambientales.)*

## Garantías de código (no dependen del modelo)
- **Validación de citas determinística:** el código verifica que cada fuente citada sea real
  y efectivamente recuperada. Cita inventada = rechazada. *(Nota: validar una cita garantiza
  procedencia, no veracidad — por eso el resto de las garantías.)*
- **Curaduría de fuentes:** confiabilidad alta / desconocida / descartada. Un desmentido exige
  al menos una fuente de alta confiabilidad.
- **El modelo razona solo sobre evidencia recuperada**, a temperatura 0 (fidelidad).
- **Abstención válida:** sin evidencia confiable, lo dice.

## Salida
`(veredicto o lean, semáforo, explicación, fuentes)` — o fuentes-guía / `INSUFICIENTE`.

Ver también: [[Arquitectura]] · [[Invariantes]]
