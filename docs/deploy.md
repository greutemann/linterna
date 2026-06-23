# Deploy en Google Cloud Run

Guía para publicar Linterna como servicio público en Cloud Run, barato y seguro.

## Principios

- **Las API keys nunca van al repo ni a la imagen.** Se guardan en **Secret Manager** y
  se inyectan como variables de entorno en runtime. El `.dockerignore` excluye
  `api_keys.env`/`*.env`.
- **Aislamiento de billing.** Cloud Run necesita billing habilitado. Para NO sacar a
  Gemini del free tier, se usa un proyecto de hosting **separado** de `linterna-500200`.
  La key de Gemini sigue viviendo en `linterna-500200` (free tier); Cloud Run solo paga
  el compute, que cae dentro del free tier (2M requests/mes ≈ US$0).

## 0. Antes de empezar: rate limiting

Un `/api/verify` público gasta tus keys. Las defensas de presupuesto (SearchBudget,
BudgetExceeded) acotan el gasto, pero conviene **agregar rate limiting por IP** antes de
exponerlo. Ver la sección final.

## 1. Proyecto de hosting (con billing, aislado)

```bash
gcloud projects create linterna-run --name="Linterna hosting"
gcloud config set project linterna-run
# Vincular una cuenta de facturación (puede ser la existente) y poner un budget alert.
gcloud services enable run.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com
```

> Poné un **presupuesto con alerta** en esta cuenta de facturación. El compute de Cloud
> Run para tráfico chico es ~US$0, pero la alerta te cubre de sorpresas.

## 2. Guardar las keys en Secret Manager

```bash
printf '%s' "TU_GEMINI_KEY"      | gcloud secrets create GEMINI_API_KEY --data-file=-
printf '%s' "TU_FACTCHECK_KEY"   | gcloud secrets create GOOGLE_FACTCHECK_API_KEY --data-file=-
printf '%s' "TU_BRAVE_KEY"       | gcloud secrets create BRAVE_API_KEY --data-file=-
```

## 3. Deploy (build + run en un comando)

```bash
gcloud run deploy linterna \
  --source . \
  --region southamerica-east1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 3 \
  --set-secrets=GEMINI_API_KEY=GEMINI_API_KEY:latest,GOOGLE_FACTCHECK_API_KEY=GOOGLE_FACTCHECK_API_KEY:latest,BRAVE_API_KEY=BRAVE_API_KEY:latest
```

`--source .` usa el `Dockerfile`. `--max-instances 3` acota el paralelismo (otra red de
contención de costo). Al terminar te da la URL pública (`https://linterna-…run.app`).

## 4. Apuntar la extensión al servicio

En las opciones de la extensión, poné la URL de Cloud Run como endpoint. Además agregá
ese host a `host_permissions` en `extension/manifest.json`.

## Notas de seguridad

- **Restricción de keys por IP:** en Cloud Run la IP de salida es **dinámica**, así que
  restringir las keys por IP no es práctico sin VPC connector + Cloud NAT (costo extra).
  Por eso la defensa principal es: Secret Manager + topes de presupuesto de la app +
  rate limiting + el crédito gratis acotado de Brave.
- **`--max-instances`** limita cuánto puede escalar (y gastar) ante un pico/abuso.
- **Cero PII (invariante 6):** no se loguea texto identificable del usuario; no agregar
  logging que lo haga.

## Rate limiting (pendiente recomendado)

Agregar `slowapi` (o equivalente) al `create_app` para limitar requests por IP a
`/api/verify`. Es un cambio chico; pedilo y se implementa con su test antes de ir a
producción.
