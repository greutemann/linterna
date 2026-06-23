# Chrome Web Store — textos para la ficha de Linterna

Copiá y pegá esto en el Developer Dashboard al publicar `linterna-extension.zip`.

## Nombre
Linterna — verificación contextual

## Descripción corta (máx. 132 caracteres)
Seleccioná texto en cualquier página y verificá la afirmación. No es un oráculo: te muestra las fuentes y la conclusión es tuya.

## Descripción larga
Linterna es una capa pública y open-source de acceso a la verificación de información.

Seleccioná una afirmación en cualquier página web, hacé clic derecho → "Verificar con Linterna", y aparece un panel con la evidencia: primero las fuentes, y el veredicto solo si lo pedís. La idea no es darte una respuesta cerrada, sino ponerte la evidencia adelante para que formes tu propio criterio.

Cómo funciona:
• Primero busca si periodistas y organizaciones humanas ya verificaron la afirmación (Google Fact Check / ClaimReview).
• Si no hay verificación previa, recupera evidencia de fuentes confiables y un modelo razona únicamente sobre esa evidencia.
• Código —no el modelo— valida que cada cita apunte a una fuente real. Cita inventada = rechazada.
• Cuando no hay evidencia suficiente, se abstiene. Y eso es una respuesta válida, no una falla.

Privacidad: solo se envía el texto que seleccionás, a tu servicio de Linterna. Sin cuentas, sin tracking, sin publicidad, cero datos personales.

Open-source de punta a punta: el método es público y auditable.

## Categoría sugerida
Tools (Herramientas) — alternativa: News & Weather

## Idioma
Español (Latinoamérica)

## Política de privacidad (URL)
https://linterna-498857011078.southamerica-east1.run.app/privacy

## Justificación de permisos (para el formulario)

- **contextMenus**: agregar la opción "Verificar con Linterna" al menú contextual cuando hay texto seleccionado.
- **storage**: recordar la dirección del servicio de Linterna configurada por el usuario (nada más).
- **activeTab**: acceder a la pestaña activa únicamente cuando el usuario activa el gesto de verificación, para mostrar el panel de resultados ahí.
- **scripting**: inyectar el panel de resultados en la pestaña activa, a demanda, en respuesta a la acción explícita del usuario.
- **host permission (…run.app / localhost)**: enviar el texto seleccionado a la API de Linterna para verificarlo.
- **Remote code**: no se usa código remoto.
- **Single purpose**: verificar una afirmación seleccionada contra el servicio de Linterna.

## Prácticas de privacidad (pestaña "Privacy practices")

- Datos recolectados: **contenido del sitio web** (solo el texto que el usuario selecciona para verificar), con el único fin de la funcionalidad de la app.
- NO recolecta información personal identificable, ni historial, ni ubicación, ni datos financieros/salud.
- Certificaciones: no se venden datos a terceros; no se usan para fines ajenos al propósito único; no se usan para determinar solvencia crediticia.
