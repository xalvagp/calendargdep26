# Calendar Generator

Generate A3 wall calendars: one page per month, the photo bleeding to the edges
and the day grid below. Spanish month and weekday names, ISO week numbers,
weekend tint and optional images for special days (birthdays, holidays).

The PDF is written directly, so the photo is **not recompressed**: a JPEG goes
into the PDF byte-for-byte, and a 16-bit TIFF is decoded to 8-bit RGB and stored
losslessly. No Pillow, no ImageMagick, nothing to install.

## Requirements

- Python 3.8+
- No third-party libraries.

## Directory structure

```
calendargdep26/
├── generate_calendars.py    # the whole program
├── especiales.json          # optional: special days (else the built-in list)
├── imagenes_special_days/   # images for the special days
├── pics/
│   └── YYYY/
│       ├── Enero.jpg        # one image per month, Spanish month name
│       ├── Febrero.tif
│       └── titles.txt       # optional: 12 lines, one caption per month
└── calendarios_pdf/         # output
```

## Usage

```bash
python3 generate_calendars.py              # current year
python3 generate_calendars.py 2027         # specific year
python3 generate_calendars.py 2027 --combined   # also one 12-page PDF
python3 generate_calendars.py 2027 --out salida/
```

Output: `calendarios_pdf/calendario-YYYY.pdf` (or one file per month with
`--combined` off), 12 pages, A3 (297 x 420 mm).

## Images

- **JPEG** — embedded as-is (DCTDecode). This is the recommended format.
- **TIFF** — only uncompressed RGB, 8 or 16 bits per channel. The high byte is
  used, so 16-bit files lose no visible detail at print size. A real 3508 x 2337
  16-bit file comes out at ~15 MB per page, so a full year is ~180 MB: fine for
  printing, heavy for sharing.
- **PNG, HEIC, DNG** — not supported; export JPEG.

JPEG is the recommended source: it is copied into the PDF untouched, so a 2 MB
export gives a ~2 MB page and a ~25 MB year, with print quality set in darktable
instead of here.

For print quality the photo should reach ~3340 x 2530 px (300 dpi over the
283 x 214 mm photo area). The script prints the effective dpi per month and
flags anything under 300.

## titles.txt

Twelve lines, one caption per month, placed in a white chip on the photo:

```
Churros con la abuela
Tarraco
...
```

If the file is missing or does not have exactly 12 lines, the pages are
generated without a caption (no stale titles are inherited from another year).

## especiales.json

Optional. Replaces the built-in list, so next year's birthdays do not need a
code edit:

```json
[
  {"month": 1, "day": 1, "title": "Año Nuevo", "image": "new_year.jpg"},
  {"month": 6, "day": 24, "title": "Marta", "image": "mdp.jpg"}
]
```

Missing images print a warning and that day is drawn without a picture; the rest
of the year still generates.

## Page geometry

- Paper A3, 4 mm bleed on all four sides: 305 x 428 mm.
- `MediaBox` 864.567 x 1213.228 pt, `TrimBox` 297 x 420 mm, so a printer knows
  where to cut.
- Photo area: full width, 214 mm tall, cropped to fill (no white bands).
- Grid rows follow the real number of weeks in the month (4 to 6), so short
  months do not leave half a page empty.

## Keeping the repository small

The photos, not the code, are what make a clone huge: a 16-bit uncompressed
TIFF at 3508 x 2337 is ~49 MB. Export JPEG (quality ~92) from darktable instead
and leave the TIFFs and the generated PDFs out of git — see `.gitignore`.

If large files are already committed, `.gitignore` will not remove them from
history; that needs a rewrite (`git filter-repo`) which everyone with a clone
must follow.
