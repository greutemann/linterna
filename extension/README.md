# Linterna — extensión de navegador (gesto contextual)

Seleccionás texto en cualquier página → clic derecho → **"Verificar con Linterna 🔦"** →
aparece un panel con la evidencia (fuentes primero) y el veredicto a pedido. Misma postura
socrática que la web: no es un oráculo, te muestra las fuentes.

Es una extensión **Chrome MV3** (funciona también en Edge y Brave; Firefox es casi
compatible). No tiene build step: son archivos estáticos.

## Requisito

El servicio de Linterna tiene que estar corriendo localmente:

```
python -m linterna.web        # queda en http://127.0.0.1:8000
```

## Cargar la extensión (modo desarrollador)

1. Abrí `chrome://extensions`.
2. Activá **"Modo de desarrollador"** (arriba a la derecha).
3. **"Cargar descomprimida"** → elegí esta carpeta `extension/`.
4. Listo. Seleccioná texto en cualquier página y usá el menú contextual.

> No usa content scripts ni permisos de host amplios. El panel se inyecta a demanda
> (`activeTab` + `scripting`) solo en la pestaña donde activás el gesto.

## Configurar el endpoint

Por defecto apunta a `http://127.0.0.1:8000`. Si lo cambiás (página de opciones de la
extensión) a otro host, **también** tenés que agregar ese host a `host_permissions` en
`manifest.json` — Chrome no permite hosts dinámicos fuera del manifiesto.

## Privacidad (invariante 6)

La extensión solo manda el **texto que seleccionás** a tu propio servicio de Linterna.
No guarda historial, no manda nada a terceros, no registra identidad.

## Nota

A diferencia del resto del repo, esta parte es JavaScript de navegador y **no está cubierta
por la suite de tests** (pytest). Se verifica cargándola manualmente en Chrome.
