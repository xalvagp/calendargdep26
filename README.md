# Calendario GdeP

Generador de calendarios de pared en formato A3, en español, con fotos personalizadas por mes, días especiales marcados con imagen de fondo, número de semana ISO y pie de foto configurable. Incluye una interfaz web local para gestionar todo sin tocar la terminal.

**GitHub Pages:** [xalvagp.github.io/calendargdep26](https://xalvagp.github.io/calendargdep26/)
**Repositorio:** [github.com/xalvagp/calendargdep26](https://github.com/xalvagp/calendargdep26)

---

## Índice

1. [Características](#características)
2. [Requisitos](#requisitos)
3. [Estructura del proyecto](#estructura-del-proyecto)
4. [Uso rápido — línea de comandos](#uso-rápido--línea-de-comandos)
5. [Interfaz web local](#interfaz-web-local)
6. [Configuración por año](#configuración-por-año)
   - [Fotos mensuales](#fotos-mensuales)
   - [Títulos de fotos](#títulos-de-fotos)
   - [Días especiales](#días-especiales)
7. [Diseño del calendario](#diseño-del-calendario)
8. [Referencia de la API REST](#referencia-de-la-api-rest)
9. [Recursos](#recursos)

---

## Características

| Característica | Detalle |
|---|---|
| Formato de salida | A3 (297 × 420 mm) a 300 DPI con 4 mm de sangrado |
| Idioma | Español — días y meses en castellano |
| Foto por mes | JPG, JPEG, TIF, TIFF, PNG, WebP |
| Pie de foto | Configurable por mes mediante `titles.txt` |
| Días especiales | Imagen semitransparente en la celda del día + nombre |
| Semana ISO | Columna lateral con número de semana (ISO 8601) |
| Fin de semana | Sábado y domingo con fondo gris diferenciado |
| Interfaz web | Gestión completa desde el navegador vía Flask |
| Configuración por año | Fotos, títulos y días especiales independientes por año |

---

## Requisitos

```
Python 3.8+
Pillow          (generación de imágenes)
Flask           (servidor web local — opcional)
DejaVu Sans     (fuente — incluida en la mayoría de distribuciones Linux)
```

Instalación de dependencias:

```bash
pip install pillow flask
```

En Ubuntu/Debian, si la fuente DejaVu no está disponible:

```bash
sudo apt install fonts-dejavu
```

---

## Estructura del proyecto

```
calendargdep26/
│
├── generate_calendars.py       # Script principal de generación
├── server.py                   # Servidor Flask para la interfaz web
├── app.html                    # Interfaz web local (gestión completa)
├── index.html                  # Página de presentación (GitHub Pages)
│
├── pics/                       # Fotos organizadas por año
│   └── YYYY/                   # Una carpeta por año (ej. 2026/)
│       ├── Enero.jpg           # Foto del mes (nombre en español)
│       ├── Febrero.tif
│       ├── ...
│       ├── Diciembre.webp
│       ├── titles.txt          # (opcional) Títulos de las 12 fotos
│       └── special_days.json   # (opcional) Días especiales del año
│
├── imagenes_ejemplo/           # Fotos de ejemplo (fallback si no hay foto del año)
│   ├── Enero.jpg
│   └── ...
│
├── imagenes_special_days/      # Imágenes para días especiales
│   ├── mdp.jpg                 # Marta
│   ├── sgp.jpg                 # Salva
│   ├── agp.jpg                 # Naná
│   ├── cgp.jpg                 # Clara
│   ├── malou.jpg               # Malou
│   ├── noche_buena.jpg         # Noche Buena
│   ├── new_year.jpg            # Año Nuevo
│   └── gdep.jpg                # GdeP
│
└── calendarios_pdf/            # PDFs generados
    ├── Enero.pdf
    └── ...
```

---

## Uso rápido — línea de comandos

### Generar los 12 calendarios de un año

```bash
python3 generate_calendars.py 2026
```

Los PDFs se guardan en `calendarios_pdf/` con el nombre del mes (`Enero.pdf`, `Febrero.pdf`…).

### Flujo completo desde cero

```bash
# 1. Clonar el repositorio
git clone https://github.com/xalvagp/calendargdep26.git
cd calendargdep26

# 2. Instalar dependencias
pip install pillow flask

# 3. Crear la carpeta del año y añadir las fotos
mkdir -p pics/2027
cp /ruta/a/mis/fotos/Enero.jpg pics/2027/
# ... repetir para los 12 meses

# 4. (Opcional) Crear títulos personalizados
echo "Mi título de enero" > pics/2027/titles.txt
# ... añadir 12 líneas en total

# 5. Generar
python3 generate_calendars.py 2027
```

---

## Interfaz web local

La interfaz web permite gestionar fotos, títulos y días especiales, y generar los PDFs, todo desde el navegador.

### Arrancar el servidor

```bash
python3 server.py
```

Abre **http://localhost:5000** en el navegador.

### Secciones de la interfaz

#### Galería
Muestra miniaturas de las 12 fotos del año seleccionado. El servidor convierte cualquier formato (incluido TIF) a JPEG al vuelo para la previsualización. Haz clic en una imagen para ampliarla en lightbox.

#### Subir fotos
Permite añadir o reemplazar la foto de cada mes mediante:
- **Click** en la tarjeta o en el botón "Seleccionar"
- **Arrastrar y soltar** la imagen directamente sobre la tarjeta

Al subir una foto se elimina automáticamente cualquier versión anterior del mismo mes (independientemente de la extensión). Se muestra una previsualización instantánea y el tamaño del archivo.

El botón **Eliminar** borra el archivo del disco.

#### Títulos de fotos
Formulario con 12 campos de texto, uno por mes, para editar el pie de foto que aparece en el calendario. Los valores se cargan desde `pics/YYYY/titles.txt` si existe, o desde los títulos por defecto en caso contrario.

- **Guardar** — escribe `pics/YYYY/titles.txt`
- **Descartar cambios** — recarga los valores guardados
- **Restablecer defaults** — carga los títulos por defecto hardcodeados

Un punto naranja indica que hay cambios sin guardar.

#### Días especiales
Tabla editable con todos los días especiales del año. Cada fila contiene:

| Campo | Descripción |
|---|---|
| Mes | Selector desplegable (Enero–Diciembre) |
| Día | Número del día (1–31) |
| Título | Texto que aparece en la celda del calendario |
| Imagen | Desplegable con las imágenes de `imagenes_special_days/` + miniatura |

Acciones disponibles:
- **+ Añadir día** — inserta una fila nueva al final
- **✕** por fila — elimina esa entrada
- **⬆ Subir** (en la columna imagen) — sube una nueva imagen a `imagenes_special_days/`
- **Copiar de año** — importa la configuración de otro año ya guardado
- **Restablecer defaults** — vuelve a los días especiales por defecto
- **Guardar** — escribe `pics/YYYY/special_days.json`

Un punto naranja indica cambios sin guardar.

#### Generar PDFs
Ejecuta `generate_calendars.py` para el año seleccionado y muestra la salida en pantalla. El proceso puede tardar varios minutos dependiendo de la resolución de las fotos.

#### Descargar PDFs
Lista los PDFs disponibles en `calendarios_pdf/` con su tamaño y fecha de generación. Cada entrada tiene un botón de descarga directa.

### Selector de año
El desplegable en la barra superior lista todos los años que tienen carpeta en `pics/`. El botón **+ Nuevo año** permite introducir un año manualmente (crea la carpeta al subir la primera foto o al guardar configuración).

---

## Configuración por año

Toda la configuración específica de un año vive en `pics/YYYY/`.

### Fotos mensuales

Las fotos deben nombrarse con el nombre del mes en español:

```
Enero, Febrero, Marzo, Abril, Mayo, Junio,
Julio, Agosto, Septiembre, Octubre, Noviembre, Diciembre
```

Extensiones soportadas: `.jpg` `.jpeg` `.tif` `.tiff` `.png` `.webp` (mayúsculas también aceptadas).

Si no existe foto para un mes en `pics/YYYY/`, el script busca en `imagenes_ejemplo/`. Si tampoco la encuentra, usa un fondo blanco.

**Recomendaciones para impresión A3:**
- Relación de aspecto 3:2 (horizontal)
- Resolución mínima recomendada: 3508 × 2339 px (300 DPI)
- Las imágenes con canal alfa (PNG/WebP con transparencia) se componen sobre fondo blanco automáticamente

### Títulos de fotos

Archivo: `pics/YYYY/titles.txt`

Debe contener exactamente **12 líneas** no vacías, una por mes en orden (Enero a Diciembre):

```
Churros con la abuela
Tarraco
Parada del 61 Diego de León
Altafulla, Tarraco
Giovanni Marongiu City Museum, Sardegna
Las Merindades
Granada
Nuraghe Losa, Sardegna
La Araña
Altafulla, Tarraco
Madrid
Año nuevo 26 Le Chinouse
```

Si el archivo no existe o tiene un número de líneas distinto de 12, se usan los títulos por defecto.

### Días especiales

Archivo: `pics/YYYY/special_days.json`

Array JSON con un objeto por día especial. Si el archivo no existe, se usan los días por defecto (ver más abajo).

Estructura de cada entrada:

```json
{
  "month": 6,
  "day":   24,
  "title": "Marta",
  "image": "mdp.jpg"
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `month` | entero 1–12 | Mes del evento |
| `day` | entero 1–31 | Día del mes |
| `title` | cadena | Texto que aparece en la celda del calendario |
| `image` | cadena | Nombre del archivo en `imagenes_special_days/` |

El campo `image` es opcional: si está vacío o el archivo no existe, el día se salta sin error.

**Días especiales por defecto:**

| Fecha | Título | Imagen |
|---|---|---|
| 1 de enero | Año Nuevo | `new_year.jpg` |
| 10 de febrero | Naná | `agp.jpg` |
| 26 de mayo | Salva | `sgp.jpg` |
| 24 de junio | Marta | `mdp.jpg` |
| 14 de julio | GdeP | `gdep.jpg` |
| 19 de agosto | Malou | `malou.jpg` |
| 23 de noviembre | Clara | `cgp.jpg` |
| 24 de diciembre | Noche buena | `noche_buena.jpg` |

Las imágenes de días especiales se colocan en la celda del día con **50% de opacidad** sobre el fondo, y el título aparece en la parte inferior de la celda.

---

## Diseño del calendario

### Dimensiones

| Zona | Medidas |
|---|---|
| Página total (con sangrado) | 305 × 428 mm a 300 DPI |
| Página imprimible (A3) | 297 × 420 mm |
| Sangrado | 4 mm en todos los lados |
| Foto (ocupa todo el ancho + sangrado superior, lateral) | ~305 × 197 mm |
| Zona del calendario | ~297 × 182 mm |
| Columna de semanas | ~20 mm |

### Elementos visuales

- **Nombre del mes** — centrado, tipografía grande (120 px a 300 DPI), entre la foto y la rejilla
- **Cabecera de días** — Lunes a Domingo en negrita, 79 px
- **Columna "Semana"** — número ISO a la derecha, 60 px
- **Números de día** — alineados a la derecha de cada celda, 60 px
- **Fin de semana** — fondo gris claro `(240, 240, 240)` en columnas Sábado y Domingo
- **Pie de foto** — título del mes en esquina inferior derecha de la foto, tipografía 24 px, color negro
- **Fuente** — DejaVu Sans / DejaVu Sans Bold (path `/usr/share/fonts/truetype/dejavu/`)

### Prioridad de capas (de abajo a arriba)

1. Foto del mes (fondo superior)
2. Fondo blanco de la zona del calendario
3. Sombra gris en celdas de fin de semana
4. Imagen del día especial (50% opacidad) si aplica
5. Líneas de la rejilla
6. Texto (números, días, mes, semana, título foto, título día especial)

---

## Referencia de la API REST

El servidor Flask expone los siguientes endpoints en `http://localhost:5000`:

### Páginas

| Ruta | Descripción |
|---|---|
| `GET /` | Interfaz de gestión (`app.html`) |
| `GET /index.html` | Página de presentación (`index.html`) |
| `GET /calendarios_pdf/<archivo>` | Descarga de un PDF generado |
| `GET /imagenes_special_days/<archivo>` | Imagen de día especial |

### Años y estado

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/years` | Lista de años con carpeta en `pics/` |
| `GET` | `/api/status/<year>` | Estado de las 12 fotos del año (encontrada, extensión, tamaño) |

### Fotos mensuales

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/thumbnail/<year>/<mes>` | Miniatura JPEG de la foto del mes (convierte TIF, PNG, etc.) |
| `POST` | `/api/upload/<year>/<mes>` | Sube una foto para el mes (form-data, campo `file`) |
| `DELETE` | `/api/delete/<year>/<mes>` | Elimina la foto del mes |

### Títulos

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/titles/<year>` | Lee `titles.txt` del año (o defaults si `year=0` o no existe) |
| `POST` | `/api/titles/<year>` | Guarda `titles.txt` — body: array JSON de 12 cadenas |

### Días especiales

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/special_days/<year>` | Lee `special_days.json` del año (o defaults si `year=0` o no existe) |
| `POST` | `/api/special_days/<year>` | Guarda `special_days.json` — body: array JSON de objetos |
| `GET` | `/api/special_day_images` | Lista de imágenes en `imagenes_special_days/` |
| `POST` | `/api/special_day_images` | Sube una imagen a `imagenes_special_days/` (form-data, campo `file`) |

### Generación y descarga

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/generate/<year>` | Ejecuta `generate_calendars.py <year>` y devuelve stdout/stderr |
| `GET` | `/api/calendars/<year>` | Lista los PDFs generados con tamaño y fecha de modificación |

**Límite de subida:** 200 MB por archivo.
**Formatos aceptados:** `.jpg` `.jpeg` `.png` `.tif` `.tiff` `.webp` (insensible a mayúsculas).

---

## Recursos

- [Página del proyecto en Notion](https://www.notion.so/xgpo/Calendars-ddffe2a9a7d846968ea93833bef50f59)
- [Referencia calendarios laborales España](https://www.calendarioslaborales.com/calendario-laboral-madrid-2025.htm)
- [GitHub Pages del proyecto](https://xalvagp.github.io/calendargdep26/)
