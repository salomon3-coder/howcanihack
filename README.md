# howcanihack.com — Setup Guide

## Archivos incluidos
- `index.html` — Página principal del sitio
- `netlify.toml` — Configuración de Netlify (publicación automática + redirect de howtohack.net)
- `robots.txt` — Para Google
- `sitemap.xml` — Para SEO

---

## Paso 1 — Subir a GitHub

1. Ve a https://github.com/new
2. Crea un repositorio llamado `howcanihack`
3. Sube todos estos archivos (arrastra y suelta, o usa GitHub Desktop)

---

## Paso 2 — Crear cuenta en Netlify y conectar GitHub

1. Ve a https://netlify.com → Sign up con tu cuenta de GitHub
2. Click en "Add new site" → "Import an existing project"
3. Selecciona GitHub → elige el repo `howcanihack`
4. Build settings: déjalos en blanco (es HTML puro)
5. Click "Deploy site"

✅ En 30 segundos el sitio estará vivo en una URL tipo `random-name.netlify.app`

---

## Paso 3 — Conectar tu dominio howcanihack.com

1. En Netlify → Site settings → Domain management → Add custom domain
2. Escribe `howcanihack.com` → Verify
3. Netlify te dará 2 nameservers (ej: `dns1.p01.nsone.net`)
4. Ve al panel donde compraste el dominio y cambia los nameservers a los de Netlify
5. Espera 5-30 minutos → HTTPS automático ✅

---

## Paso 4 — Redirect de howtohack.net (ya está en netlify.toml)

El archivo `netlify.toml` ya tiene configurado el redirect 301 de howtohack.net → howcanihack.com.
Solo necesitas apuntar los nameservers de howtohack.net también a Netlify.

---

## Paso 5 — Publicar nuevo contenido

Cada vez que subas un archivo nuevo o edites uno en GitHub:
→ Netlify detecta el cambio automáticamente y publica en ~30 segundos.

Para agregar artículos: crea archivos HTML en carpetas como:
- `tutorials/nombre-del-articulo.html`
- `news/nombre-de-la-noticia.html`
- `cve/cve-2026-xxxx.html`

---

## Monetización con Google AdSense

1. Ve a https://adsense.google.com → Sign up
2. Agrega tu sitio `howcanihack.com`
3. Google te da un snippet de código → agrégalo en el `<head>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4579344894934796" crossorigin="anonymous"></script>` de index.html
4. Listo, los anuncios aparecen automáticamente

---

## Para generar contenido con IA

Prompt sugerido para Claude o ChatGPT:
```
Escribe un artículo SEO de 1500 palabras sobre [TEMA] para el sitio howcanihack.com.
El público es principiante en ciberseguridad. Incluye:
- Título con keyword principal
- Meta description de 155 caracteres
- Subtítulos H2 y H3
- Código o comandos donde sea relevante
- Conclusión con CTA
Formato: HTML listo para publicar.
```
