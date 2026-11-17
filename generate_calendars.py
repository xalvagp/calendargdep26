#!/usr/bin/env python3
"""Genera calendarios A3 en PDF a partir de las fotos de pics/AAAA/.

Sin dependencias externas (no necesita Pillow): escribe el PDF a mano y
embebe la imagen tal cual cuando es JPEG (DCTDecode) o la decodifica cuando es
TIFF RGB sin comprimir (FlateDecode).

Uso:
    python3 generate_calendars.py            # año actual
    python3 generate_calendars.py 2027
    python3 generate_calendars.py 2027 --out salida/
    python3 generate_calendars.py 2027 --combined   # además, un PDF de 12 páginas

Estructura esperada:
    pics/AAAA/Enero.jpg|.tif|.png ... + titles.txt (12 líneas, opcional)
    imagenes_special_days/*.jpg
    especiales.json (opcional; si no está, se usa la lista de abajo)

Salida: calendarios_pdf/<Mes>.pdf (y calendario-AAAA.pdf con --combined).
"""
import argparse
import calendar
import json
import os
import struct
import sys
import zlib
from datetime import date, datetime

MM = 72.0 / 25.4  # mm -> pt

# ---------------- geometria de pagina (mm, origen abajo-izquierda) ----------------
PAGE_W, PAGE_H = 305.0, 428.0   # A3 297x420 + sangrado 4 mm
BLEED = 4.0
PHOTO_H = 214.0
MARGIN_X = 7.0
BOTTOM_MARGIN = 8.0
WEEK_COL = 15.0
MONTH_BAND = 24.0
HDR_H = 12.0

CONTENT_X0 = BLEED + MARGIN_X
CONTENT_X1 = PAGE_W - BLEED - MARGIN_X
CONTENT_W = CONTENT_X1 - CONTENT_X0
DAY_W = CONTENT_W - WEEK_COL
CELL_W = DAY_W / 7.0
MONTH_BAND_Y0 = PHOTO_H - MONTH_BAND
HDR_Y0 = MONTH_BAND_Y0 - HDR_H
GRID_TOP = HDR_Y0
GRID_BOTTOM = BLEED + BOTTOM_MARGIN

DIAS = ['Lunes', 'Martes', 'Mi\u00e9rcoles', 'Jueves', 'Viernes', 'S\u00e1bado', 'Domingo']
MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
         'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
EXT = ('.jpg', '.jpeg', '.tif', '.tiff', '.png')

SPECIAL_DAYS = [
    {'month': 1, 'day': 1, 'title': 'A\u00f1o Nuevo', 'image': 'new_year.jpg'},
    {'month': 2, 'day': 10, 'title': 'Nan\u00e1', 'image': 'agp.jpg'},
    {'month': 5, 'day': 26, 'title': 'Salva', 'image': 'sgp.jpg'},
    {'month': 6, 'day': 24, 'title': 'Marta', 'image': 'mdp.jpg'},
    {'month': 8, 'day': 19, 'title': 'Malou', 'image': 'malou.jpg'},
    {'month': 11, 'day': 23, 'title': 'Clara', 'image': 'cgp.jpg'},
    {'month': 12, 'day': 24, 'title': 'Noche buena', 'image': 'noche_buena.jpg'},
]

# ---------------- metricas Helvetica (1/1000 em) ----------------
_REG = {' ': 278, '!': 278, '"': 355, '#': 556, '$': 556, '%': 889, '&': 667, "'": 191,
        '(': 333, ')': 333, '*': 389, '+': 584, ',': 278, '-': 333, '.': 278, '/': 278,
        '0': 556, '1': 556, '2': 556, '3': 556, '4': 556, '5': 556, '6': 556, '7': 556,
        '8': 556, '9': 556, ':': 278, ';': 278, '<': 584, '=': 584, '>': 584, '?': 556,
        '@': 1015, 'A': 667, 'B': 667, 'C': 722, 'D': 722, 'E': 667, 'F': 611, 'G': 778,
        'H': 722, 'I': 278, 'J': 500, 'K': 667, 'L': 556, 'M': 833, 'N': 722, 'O': 778,
        'P': 667, 'Q': 778, 'R': 722, 'S': 667, 'T': 611, 'U': 722, 'V': 667, 'W': 944,
        'X': 667, 'Y': 667, 'Z': 611, '[': 278, '\\': 278, ']': 278, '^': 469, '_': 556,
        '`': 333, 'a': 556, 'b': 556, 'c': 500, 'd': 556, 'e': 556, 'f': 278, 'g': 556,
        'h': 556, 'i': 222, 'j': 222, 'k': 500, 'l': 222, 'm': 833, 'n': 556, 'o': 556,
        'p': 556, 'q': 556, 'r': 333, 's': 500, 't': 278, 'u': 556, 'v': 500, 'w': 722,
        'x': 500, 'y': 500, 'z': 500, '{': 334, '|': 260, '}': 334, '~': 584}
_BOLD = {' ': 278, '!': 333, '"': 474, '#': 556, '$': 556, '%': 889, '&': 722, "'": 238,
         '(': 333, ')': 333, '*': 389, '+': 584, ',': 278, '-': 333, '.': 278, '/': 278,
         '0': 556, '1': 556, '2': 556, '3': 556, '4': 556, '5': 556, '6': 556, '7': 556,
         '8': 556, '9': 556, ':': 333, ';': 333, '<': 584, '=': 584, '>': 584, '?': 611,
         '@': 975, 'A': 722, 'B': 722, 'C': 722, 'D': 722, 'E': 667, 'F': 611, 'G': 778,
         'H': 722, 'I': 278, 'J': 556, 'K': 722, 'L': 611, 'M': 833, 'N': 722, 'O': 778,
         'P': 667, 'Q': 778, 'R': 722, 'S': 667, 'T': 611, 'U': 722, 'V': 667, 'W': 944,
         'X': 667, 'Y': 667, 'Z': 611, 'a': 556, 'b': 611, 'c': 556, 'd': 611, 'e': 556,
         'f': 333, 'g': 611, 'h': 611, 'i': 278, 'j': 278, 'k': 556, 'l': 278, 'm': 889,
         'n': 611, 'o': 611, 'p': 611, 'q': 611, 'r': 389, 's': 556, 't': 333, 'u': 611,
         'v': 556, 'w': 778, 'x': 556, 'y': 556, 'z': 500}
_ACCENT = {'\u00e1': 'a', '\u00e9': 'e', '\u00ed': 'i', '\u00f3': 'o', '\u00fa': 'u',
           '\u00c1': 'A', '\u00c9': 'E', '\u00cd': 'I', '\u00d3': 'O', '\u00da': 'U',
           '\u00f1': 'n', '\u00d1': 'N', '\u00fc': 'u', '\u00bf': '?', '\u00a1': '!'}


def text_width(s, size_pt, bold=False):
    tab = _BOLD if bold else _REG
    total = 0
    for ch in s:
        k = tab.get(ch)
        if k is None:
            k = tab.get(_ACCENT.get(ch, 'n'), 556)
        total += k
    return total / 1000.0 * size_pt


# ---------------- lectores de imagen ----------------
def jpeg_info(path):
    with open(path, 'rb') as f:
        data = f.read()
    if data[:2] != b'\xff\xd8':
        raise ValueError('no es JPEG: %s' % path)
    i, n = 2, len(data)
    while i < n - 4:
        if data[i] != 0xFF:
            i += 1
            continue
        m = data[i + 1]
        if m in (0xD8, 0x01):
            i += 2
            continue
        if m == 0xDA:
            break
        seglen = struct.unpack('>H', data[i + 2:i + 4])[0]
        if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            return struct.unpack('>HH', data[i + 5:i + 9])[::-1] + (data[i + 9], data[i + 4])
        i += 2 + seglen
    raise ValueError('sin SOF en %s' % path)


def exif_orientation(path):
    try:
        with open(path, 'rb') as f:
            data = f.read(200000)
        i = data.find(b'Exif\x00\x00')
        if i < 0:
            return 1
        t = data[i + 6:]
        end = '<' if t[:2] == b'II' else '>'
        off = struct.unpack(end + 'I', t[4:8])[0]
        n = struct.unpack(end + 'H', t[off:off + 2])[0]
        for k in range(n):
            p = off + 2 + 12 * k
            if struct.unpack(end + 'H', t[p:p + 2])[0] == 0x0112:
                return struct.unpack(end + 'H', t[p + 8:p + 10])[0]
    except Exception:
        pass
    return 1


def strip_jpeg(path):
    """Quita APPn/COM previos al primer SOS: menos peso, mismo bitstream."""
    with open(path, 'rb') as f:
        data = f.read()
    out = bytearray(data[:2])
    i, n = 2, len(data)
    while i < n - 1 and data[i] == 0xFF and data[i + 1] in tuple(range(0xE0, 0xF0)) + (0xFE,):
        i += 2 + struct.unpack('>H', data[i + 2:i + 4])[0]
    return bytes(out) + data[i:]


def _tiff_tags(data):
    end = '<' if data[:2] == b'II' else '>'
    off = struct.unpack(end + 'I', data[4:8])[0]
    n = struct.unpack(end + 'H', data[off:off + 2])[0]
    tags = {}
    for k in range(n):
        p = off + 2 + 12 * k
        tag, typ, cnt = struct.unpack(end + 'HHI', data[p:p + 8])
        size = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8}.get(typ, 1)
        if size * cnt <= 4:
            raw = data[p + 8:p + 8 + size * cnt]
        else:
            vo = struct.unpack(end + 'I', data[p + 8:p + 12])[0]
            raw = data[vo:vo + size * cnt]
        if typ == 3:
            vals = [struct.unpack(end + 'H', raw[j:j + 2])[0] for j in range(0, len(raw), 2)]
        elif typ == 4:
            vals = [struct.unpack(end + 'I', raw[j:j + 4])[0] for j in range(0, len(raw), 4)]
        else:
            vals = list(raw)
        tags[tag] = vals
    return tags, end


def tiff_to_rgb(path):
    """TIFF RGB sin comprimir (8 o 16 bits) -> (w, h, bytes RGB de 8 bits)."""
    with open(path, 'rb') as f:
        data = f.read()
    if data[:2] not in (b'II', b'MM') or struct.unpack('<H' if data[:2] == b'II' else '>H',
                                                        data[2:4])[0] != 42:
        raise ValueError('%s: no es TIFF clasico' % path)
    t, end = _tiff_tags(data)
    if t.get(259, [1])[0] != 1:
        raise ValueError('%s: TIFF comprimido (Compression=%d). Exporta en JPEG o sin comprimir.'
                         % (path, t[259][0]))
    if t.get(262, [2])[0] != 2:
        raise ValueError('%s: TIFF no RGB (Photometric=%d)' % (path, t[262][0]))
    if t.get(284, [1])[0] != 1:
        raise ValueError('%s: TIFF planar (PlanarConfig=%d)' % (path, t[284][0]))
    w, h = t[256][0], t[257][0]
    bits = t.get(258, [8])[0]
    spp = t.get(277, [3])[0]
    if spp != 3:
        raise ValueError('%s: %d canales, se esperaban 3 (RGB)' % (path, spp))
    offs = t[273]
    counts = t.get(279)
    if not counts:
        raise ValueError('%s: TIFF sin StripByteCounts' % path)
    raw = bytearray()
    for o, c in zip(offs, counts):
        raw += data[o:o + c]
    if bits == 16:
        # 16 bits -> 8 bits tomando el byte alto: en little-endian esta en el indice impar
        raw = raw[1::2] if end == '<' else raw[0::2]
    elif bits != 8:
        raise ValueError('%s: %d bits por canal no soportado' % (path, bits))
    need = w * h * 3
    if len(raw) < need:
        raise ValueError('%s: faltan datos (%d de %d bytes)' % (path, len(raw), need))
    return w, h, bytes(raw[:need])


# ---------------- primitivas de contenido ----------------
def _esc(s):
    b = s.encode('cp1252', 'replace')
    return b.replace(b'\\', b'\\\\').replace(b'(', b'\\(').replace(b')', b'\\)')


def _rgb(c):
    return '%.3f %.3f %.3f' % c


def msg(text, x, y, size, bold=False, anchor='left', color=(0, 0, 0)):
    w = text_width(text, size, bold) / MM
    if anchor == 'center':
        x -= w / 2.0
    elif anchor == 'right':
        x -= w
    return ('BT %s %.2f Tf %s rg 1 0 0 1 %.3f %.3f Tm (%s) Tj ET'
            % ('/F2' if bold else '/F1', size, _rgb(color), x * MM, y * MM,
               _esc(text).decode('latin-1')))


def _disp_dims(iw, ih, orient):
    return (ih, iw) if orient in (6, 8) else (iw, ih)


def _img_matrix(x, y, dW, dH, orient):
    if orient == 3:
        return '%.4f 0 0 %.4f %.4f %.4f' % (-dW * MM, -dH * MM, (x + dW) * MM, (y + dH) * MM)
    if orient == 6:
        return '0 %.4f %.4f 0 %.4f %.4f' % (-dH * MM, dW * MM, x * MM, (y + dH) * MM)
    if orient == 8:
        return '0 %.4f %.4f 0 %.4f %.4f' % (dH * MM, -dW * MM, (x + dW) * MM, y * MM)
    return '%.4f 0 0 %.4f %.4f %.4f' % (dW * MM, dH * MM, x * MM, y * MM)


def _box(iw, ih, orient, x, y, w, h, mode='cover', shrink=1.0):
    dw0, dh0 = _disp_dims(iw, ih, orient)
    sc = (max if mode == 'cover' else min)(w / dw0, h / dh0) * shrink
    dW, dH = dw0 * sc, dh0 * sc
    return x + (w - dW) / 2.0, y + (h - dH) / 2.0, dW, dH


def place_cover(ops, img, x, y, w, h):
    num, iw, ih, orient = img
    bx, by, dW, dH = _box(iw, ih, orient, x, y, w, h, 'cover')
    ops.append('q %.4f %.4f %.4f %.4f re W n' % (x * MM, y * MM, w * MM, h * MM))
    ops.append('q %s cm /Im%d Do Q' % (_img_matrix(bx, by, dW, dH, orient), num))
    ops.append('Q')


def place_fit_alpha(ops, img, x, y, w, h, shrink=0.94):
    num, iw, ih, orient = img
    bx, by, dW, dH = _box(iw, ih, orient, x, y, w, h, 'contain', shrink)
    ops.append('q /GS1 gs %s cm /Im%d Do Q' % (_img_matrix(bx, by, dW, dH, orient), num))


# ---------------- PDF ----------------
class PdfDoc:
    def __init__(self):
        self.objs = {}
        self.n = 0

    def add(self, body):
        self.n += 1
        self.objs[self.n] = body
        return self.n

    def stream(self, data, extra=''):
        self.n += 1
        head = ('<< /Length %d %s >>\nstream\n' % (len(data), extra)).encode('latin-1')
        self.objs[self.n] = head + data + b'\nendstream'
        return self.n

    def build(self, root, fh):
        out = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
        offs = {}
        for num in sorted(self.objs):
            offs[num] = len(out)
            out += ('%d 0 obj\n' % num).encode() + self.objs[num] + b'\nendobj\n'
        xref = len(out)
        total = self.n + 1
        out += ('xref\n0 %d\n' % total).encode() + b'0000000000 65535 f \n'
        for i in range(1, total):
            out += ('%010d 00000 n \n' % offs[i]).encode()
        out += ('trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n'
                % (total, root, xref)).encode()
        fh.write(out)


def add_image(doc, path):
    """Devuelve (num_objeto, w, h, orientacion). JPEG tal cual; TIFF -> Flate."""
    with open(path, 'rb') as f:
        magic = f.read(4)
    if magic[:2] == b'\xff\xd8':
        w, h, ncomp, prec = jpeg_info(path)
        if prec != 8:
            raise ValueError('%s: JPEG de %d bits; exporta en 8 bits' % (path, prec))
        cs = {1: '/DeviceGray', 3: '/DeviceRGB', 4: '/DeviceCMYK'}.get(ncomp)
        if cs is None:
            raise ValueError('%s: %d componentes' % (path, ncomp))
        extra = ('/Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace %s '
                 '/BitsPerComponent 8 /Filter /DCTDecode' % (w, h, cs))
        if ncomp == 4:
            extra += ' /Decode [1 0 1 0 1 0 1 0]'
        return doc.stream(strip_jpeg(path), extra), w, h, exif_orientation(path)
    if magic[:2] in (b'II', b'MM'):
        w, h, rgb = tiff_to_rgb(path)
        extra = ('/Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceRGB '
                 '/BitsPerComponent 8 /Filter /FlateDecode' % (w, h))
        return doc.stream(zlib.compress(rgb, 6), extra), w, h, 1
    raise ValueError('%s: formato no soportado (usa JPEG o TIFF RGB sin comprimir)' % path)


def render_month(doc, parent, year, month, photo, title, specials, fonts, xobjs):
    cal = calendar.monthcalendar(year, month)
    rows = len(cal)
    cell_h = (GRID_TOP - GRID_BOTTOM) / rows
    ops = []

    if photo:
        place_cover(ops, photo, 0, PHOTO_H, PAGE_W, PAGE_H - PHOTO_H)

    if title:
        size, pad = 12.0, 3.0
        tw = text_width(title, size, True) / MM
        bx = PAGE_W - BLEED - 3.0 - tw - 2 * pad
        by = PHOTO_H + 4.0
        ops.append('q 1 1 1 rg %.3f %.3f %.3f %.3f re f Q'
                   % (bx * MM, by * MM, (tw + 2 * pad) * MM, (size / MM + 2 * pad) * MM))
        ops.append(msg(title, bx + pad, by + pad + size / MM * 0.28, size, True))

    # Banda translucida: sin ella el nombre del mes es ilegible sobre la foto.
    ops.append('q /GS2 gs 1 1 1 rg %.3f %.3f %.3f %.3f re f Q'
               % (CONTENT_X0 * MM, MONTH_BAND_Y0 * MM, CONTENT_W * MM, MONTH_BAND * MM))
    ops.append('q /GS2 gs 0.55 0.55 0.55 rg %.3f %.3f %.3f %.1f re f Q'
               % (CONTENT_X0 * MM, MONTH_BAND_Y0 * MM, CONTENT_W * MM, 0.9))
    ops.append(msg(MESES[month - 1], PAGE_W / 2.0, MONTH_BAND_Y0 + 7.0, 27, True, 'center'))

    for i, d in enumerate(DIAS):
        ops.append(msg(d, CONTENT_X0 + CELL_W * (i + 0.5), HDR_Y0 + 3.6, 13.5, True, 'center'))
    ops.append(msg('Sem.', CONTENT_X0 + DAY_W + WEEK_COL / 2.0, HDR_Y0 + 3.6, 10.5, True, 'center'))

    for r, week in enumerate(cal):
        for c in (5, 6):
            if c < len(week) and week[c] != 0:
                cx = CONTENT_X0 + c * CELL_W
                cy = GRID_TOP - (r + 1) * cell_h
                ops.append('q 0.945 0.945 0.945 rg %.3f %.3f %.3f %.3f re f Q'
                           % (cx * MM, cy * MM, CELL_W * MM, cell_h * MM))

    for r, week in enumerate(cal):
        for c, day in enumerate(week):
            sp = specials.get((month, day)) if day else None
            if sp:
                cx = CONTENT_X0 + c * CELL_W
                cy = GRID_TOP - (r + 1) * cell_h
                place_fit_alpha(ops, sp['img'], cx + 1, cy + 4, CELL_W - 2, cell_h - 5)

    def line(x1, y1, x2, y2, lw=0.5):
        ops.append('q %.2f w 0 0 0 RG %.3f %.3f m %.3f %.3f l S Q'
                   % (lw, x1 * MM, y1 * MM, x2 * MM, y2 * MM))

    ops.append('q 0.8 w 0 0 0 RG %.3f %.3f %.3f %.3f re S Q'
               % (CONTENT_X0 * MM, GRID_BOTTOM * MM, DAY_W * MM, (GRID_TOP - GRID_BOTTOM) * MM))
    for r in range(1, rows):
        y = GRID_TOP - r * cell_h
        line(CONTENT_X0, y, CONTENT_X0 + DAY_W, y)
    for c in range(1, 7):
        x = CONTENT_X0 + c * CELL_W
        line(x, GRID_BOTTOM, x, GRID_TOP)
    line(CONTENT_X0 + DAY_W, GRID_BOTTOM, CONTENT_X0 + DAY_W, GRID_TOP)

    for r, week in enumerate(cal):
        cy_top = GRID_TOP - r * cell_h
        if any(week):
            first = next(d for d in week if d != 0)
            wk = date(year, month, first).isocalendar()[1]
            ops.append(msg(str(wk), CONTENT_X0 + DAY_W + WEEK_COL / 2.0,
                           cy_top - cell_h / 2.0 - 1.7, 12, False, 'center', (0.3, 0.3, 0.3)))
        for c, day in enumerate(week):
            if not day:
                continue
            cx = CONTENT_X0 + c * CELL_W
            ops.append(msg(str(day), cx + CELL_W - 2.0, cy_top - 7.0, 13, True, 'right'))
            sp = specials.get((month, day))
            if sp:
                ops.append(msg(sp['title'], cx + CELL_W / 2.0, cy_top - cell_h + 3.0,
                               8.5, True, 'center'))

    cnum = doc.stream('\n'.join(ops).encode('latin-1'))
    xo = ' '.join('/Im%d %d 0 R' % (k, k) for k in sorted(xobjs))
    page = ('<< /Type /Page /Parent %d 0 R '
            '/MediaBox [0 0 %.3f %.3f] /TrimBox [%.3f %.3f %.3f %.3f] '
            '/BleedBox [0 0 %.3f %.3f] /CropBox [0 0 %.3f %.3f] '
            '/Resources << /XObject << %s >> /Font << /F1 %d 0 R /F2 %d 0 R >> '
            '/ExtGState << /GS1 << /ca 0.32 /CA 0.32 >> /GS2 << /ca 0.78 /CA 0.78 >> >> >> '
            '/Contents %d 0 R >>'
            % (parent, PAGE_W * MM, PAGE_H * MM,
               BLEED * MM, BLEED * MM, (PAGE_W - BLEED) * MM, (PAGE_H - BLEED) * MM,
               PAGE_W * MM, PAGE_H * MM, PAGE_W * MM, PAGE_H * MM,
               xo, fonts[0], fonts[1], cnum))
    return doc.add(page.encode('latin-1'))


# ---------------- entrada / configuracion ----------------
def find_image(month_name, directory):
    for ext in EXT:
        for cand in (month_name + ext, month_name + ext.upper()):
            p = os.path.join(directory, cand)
            if os.path.exists(p):
                return p
    return None


def load_titles(year):
    p = os.path.join('pics', str(year), 'titles.txt')
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            lines = [l.strip() for l in f if l.strip()]
        if len(lines) == 12:
            return lines
        print('AVISO: %s debe tener 12 lineas (tiene %d); sin titulos.' % (p, len(lines)))
    return ['' for _ in range(12)]


def load_specials(path='especiales.json'):
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return SPECIAL_DAYS


def _new_doc():
    doc = PdfDoc()
    f1 = doc.add(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
    f2 = doc.add(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>')
    return doc, (f1, f2)


def _build_page(doc, fonts, pages_ref, year, month, photo_path, title, specials_spec, specials_dir):
    """Anade imagen(es) y pagina al documento. Devuelve la ref de la pagina."""
    xobjs = set()
    photo = None
    if photo_path:
        photo = add_image(doc, photo_path)
        xobjs.add(photo[0])
        _, iw, ih, orient = photo
        dw, dh = _disp_dims(iw, ih, orient)
        dpi = min(dw / (CONTENT_W / 25.4), dh / (PHOTO_H / 25.4))
        print('  %-11s %-28s %5dx%-5d %.0f dpi%s'
              % (MESES[month - 1], os.path.basename(photo_path), iw, ih, dpi,
                 '  <-- baja' if dpi < 300 else ''))
    else:
        print('  %-11s sin foto' % MESES[month - 1])

    specials = {}
    for spec in specials_spec:
        if spec['month'] != month:
            continue
        p = os.path.join(specials_dir, spec['image'])
        if not os.path.exists(p):
            print('  AVISO: falta %s (%s); ese dia sale sin imagen' % (p, spec['title']))
            continue
        try:
            img = add_image(doc, p)
        except Exception as e:
            print('  AVISO: %s no usable: %s' % (p, e))
            continue
        specials[(spec['month'], spec['day'])] = {'title': spec['title'], 'img': img}
        xobjs.add(img[0])

    return render_month(doc, pages_ref, year, month, photo, title, specials, fonts, xobjs)


def _finish(doc, pages_ref, kids, out_path):
    doc.objs[pages_ref] = ('<< /Type /Pages /Count %d /Kids [%s] >>'
                           % (len(kids), ' '.join('%d 0 R' % k for k in kids))).encode('latin-1')
    catalog = doc.add(('<< /Type /Catalog /Pages %d 0 R >>' % pages_ref).encode('latin-1'))
    with open(out_path, 'wb') as f:
        doc.build(catalog, f)
    print('  -> %s (%.1f MB)' % (out_path, os.path.getsize(out_path) / 1e6))


def build_year(year, out_dir, combined, specials_spec, specials_dir):
    titles = load_titles(year)
    paths = {m: find_image(MESES[m - 1], os.path.join('pics', str(year))) for m in range(1, 13)}
    os.makedirs(out_dir, exist_ok=True)

    if combined:
        doc, fonts = _new_doc()
        pages_ref = doc.add(b'X')
        kids = [_build_page(doc, fonts, pages_ref, year, m, paths[m], titles[m - 1],
                            specials_spec, specials_dir) for m in range(1, 13)]
        _finish(doc, pages_ref, kids, os.path.join(out_dir, 'calendario-%d.pdf' % year))
        return

    for m in range(1, 13):
        doc, fonts = _new_doc()
        pages_ref = doc.add(b'X')
        page = _build_page(doc, fonts, pages_ref, year, m, paths[m], titles[m - 1],
                           specials_spec, specials_dir)
        _finish(doc, pages_ref, [page], os.path.join(out_dir, '%s.pdf' % MESES[m - 1]))


def main():
    ap = argparse.ArgumentParser(description='Genera calendarios A3 (12 meses) sin dependencias.')
    ap.add_argument('year', nargs='?', type=int, default=datetime.now().year)
    ap.add_argument('--out', default='calendarios_pdf', help='carpeta de salida')
    ap.add_argument('--specials-dir', default='imagenes_special_days')
    ap.add_argument('--combined', action='store_true', help='un solo PDF de 12 paginas')
    args = ap.parse_args()
    build_year(args.year, args.out, args.combined, load_specials(), args.specials_dir)


if __name__ == '__main__':
    main()
