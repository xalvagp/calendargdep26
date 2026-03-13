from flask import Flask, request, jsonify, send_from_directory, send_file
from PIL import Image
from io import BytesIO
import os
import json
import subprocess

app = Flask(__name__, static_folder='.')

MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.webp']
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB

DEFAULT_SPECIAL_DAYS = [
    {'month': 6,  'day': 24, 'title': 'Marta',      'image': 'mdp.jpg'},
    {'month': 5,  'day': 26, 'title': 'Salva',       'image': 'sgp.jpg'},
    {'month': 2,  'day': 10, 'title': 'Naná',        'image': 'agp.jpg'},
    {'month': 11, 'day': 23, 'title': 'Clara',       'image': 'cgp.jpg'},
    {'month': 8,  'day': 19, 'title': 'Malou',       'image': 'malou.jpg'},
    {'month': 12, 'day': 24, 'title': 'Noche buena', 'image': 'noche_buena.jpg'},
    {'month': 7,  'day': 14, 'title': 'GdeP',        'image': 'gdep.jpg'},
    {'month': 1,  'day': 1,  'title': 'Año Nuevo',   'image': 'new_year.jpg'},
]

DEFAULT_TITLES = [
    'Churros con la abuela', 'Tarraco', 'Parada del 61 Diego de Leon',
    'Altafulla, Tarraco', 'Giovanni Marongiu City Museum, Sardegna',
    'Las Merindades', 'Granada', 'Nuraghe Losa, Sardegna',
    'La Araña', 'Altafulla, Tarraco', 'Madrid', 'Año nuevo 26 Le Chinouse',
]


# ── helpers ──────────────────────────────────────────────────────────────────

def find_image(mes, directory):
    for ext in ALLOWED_EXTENSIONS + [e.upper() for e in ALLOWED_EXTENSIONS]:
        path = os.path.join(directory, mes + ext)
        if os.path.exists(path):
            return path
    return None


# ── static files ─────────────────────────────────────────────────────────────

@app.route('/')
def root():
    return send_from_directory('.', 'app.html')

@app.route('/index.html')
def landing():
    return send_from_directory('.', 'index.html')

@app.route('/calendarios_pdf/<path:filename>')
def download_pdf(filename):
    return send_from_directory('calendarios_pdf', filename)

@app.route('/imagenes_special_days/<path:filename>')
def special_day_image(filename):
    return send_from_directory('imagenes_special_days', filename)


# ── API ───────────────────────────────────────────────────────────────────────

@app.route('/api/years')
def api_years():
    pics_dir = 'pics'
    if not os.path.exists(pics_dir):
        return jsonify([])
    years = sorted(
        [d for d in os.listdir(pics_dir)
         if os.path.isdir(os.path.join(pics_dir, d)) and d.isdigit()],
        reverse=True
    )
    return jsonify(years)


@app.route('/api/status/<int:year>')
def api_status(year):
    pics_dir = os.path.join('pics', str(year))
    result = {}
    for mes in MESES:
        path = find_image(mes, pics_dir)
        if path:
            ext = os.path.splitext(path)[1].lower()
            size = os.path.getsize(path)
            result[mes] = {'found': True, 'ext': ext, 'size': size}
        else:
            result[mes] = {'found': False}
    return jsonify(result)


@app.route('/api/thumbnail/<int:year>/<mes>')
def api_thumbnail(year, mes):
    if mes not in MESES:
        return '', 404
    path = find_image(mes, os.path.join('pics', str(year)))
    if not path:
        return '', 404
    try:
        with Image.open(path) as img:
            if img.mode == 'RGBA':
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3])
                img = bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            img.thumbnail((600, 400), Image.LANCZOS)
            buf = BytesIO()
            img.save(buf, 'JPEG', quality=82)
            buf.seek(0)
        return send_file(buf, mimetype='image/jpeg',
                         max_age=60, conditional=True)
    except Exception as e:
        return str(e), 500


@app.route('/api/upload/<int:year>/<mes>', methods=['POST'])
def api_upload(year, mes):
    if mes not in MESES:
        return jsonify({'error': 'Mes no válido'}), 400
    if 'file' not in request.files:
        return jsonify({'error': 'Sin archivo'}), 400
    file = request.files['file']
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': f'Formato no soportado: {ext}'}), 400

    pics_dir = os.path.join('pics', str(year))
    os.makedirs(pics_dir, exist_ok=True)

    # eliminar versiones anteriores del mismo mes
    for old_ext in ALLOWED_EXTENSIONS + [e.upper() for e in ALLOWED_EXTENSIONS]:
        old = os.path.join(pics_dir, mes + old_ext)
        if os.path.exists(old):
            os.remove(old)

    save_path = os.path.join(pics_dir, mes + ext)
    file.save(save_path)
    size = os.path.getsize(save_path)
    return jsonify({'success': True, 'path': save_path, 'size': size, 'ext': ext})


@app.route('/api/delete/<int:year>/<mes>', methods=['DELETE'])
def api_delete(year, mes):
    if mes not in MESES:
        return jsonify({'error': 'Mes no válido'}), 400
    pics_dir = os.path.join('pics', str(year))
    deleted = False
    for ext in ALLOWED_EXTENSIONS + [e.upper() for e in ALLOWED_EXTENSIONS]:
        p = os.path.join(pics_dir, mes + ext)
        if os.path.exists(p):
            os.remove(p)
            deleted = True
    return jsonify({'success': deleted})


@app.route('/api/special_days/<int:year>', methods=['GET'])
def get_special_days(year):
    if year == 0:
        return jsonify(DEFAULT_SPECIAL_DAYS)
    path = os.path.join('pics', str(year), 'special_days.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    return jsonify(DEFAULT_SPECIAL_DAYS)


@app.route('/api/special_days/<int:year>', methods=['POST'])
def save_special_days(year):
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({'error': 'Se esperaba una lista'}), 400
    pics_dir = os.path.join('pics', str(year))
    os.makedirs(pics_dir, exist_ok=True)
    with open(os.path.join(pics_dir, 'special_days.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'success': True})


@app.route('/api/titles/<int:year>', methods=['GET'])
def get_titles(year):
    if year == 0:
        return jsonify(DEFAULT_TITLES)
    path = os.path.join('pics', str(year), 'titles.txt')
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                titles = [l.strip() for l in f if l.strip()]
            if len(titles) == 12:
                return jsonify(titles)
        except Exception:
            pass
    return jsonify(DEFAULT_TITLES)


@app.route('/api/titles/<int:year>', methods=['POST'])
def save_titles(year):
    data = request.get_json()
    if not isinstance(data, list) or len(data) != 12:
        return jsonify({'error': 'Se esperan exactamente 12 títulos'}), 400
    pics_dir = os.path.join('pics', str(year))
    os.makedirs(pics_dir, exist_ok=True)
    with open(os.path.join(pics_dir, 'titles.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(data))
    return jsonify({'success': True})


@app.route('/api/special_day_images', methods=['GET'])
def list_special_day_images():
    d = 'imagenes_special_days'
    exts = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.webp',
            '.JPG', '.JPEG', '.PNG', '.TIF', '.TIFF', '.WEBP'}
    imgs = sorted(f for f in os.listdir(d)
                  if os.path.isfile(os.path.join(d, f)) and os.path.splitext(f)[1] in exts)
    return jsonify(imgs)


@app.route('/api/special_day_images', methods=['POST'])
def upload_special_day_image():
    if 'file' not in request.files:
        return jsonify({'error': 'Sin archivo'}), 400
    file = request.files['file']
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': f'Formato no soportado: {ext}'}), 400
    # Sanitize filename: only keep alphanumeric, dash, underscore, dot
    import re
    safe = re.sub(r'[^\w.\-]', '_', file.filename)
    save_path = os.path.join('imagenes_special_days', safe)
    file.save(save_path)
    return jsonify({'success': True, 'filename': safe})


@app.route('/api/generate/<int:year>', methods=['POST'])
def api_generate(year):
    try:
        result = subprocess.run(
            ['python3', 'generate_calendars.py', str(year)],
            capture_output=True, text=True, timeout=600
        )
        ok = result.returncode == 0
        return jsonify({
            'success': ok,
            'output': result.stdout,
            'error': result.stderr if not ok else ''
        })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Tiempo agotado (>10 min)'}), 504
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/calendars/<int:year>')
def api_calendars(year):
    pdf_dir = 'calendarios_pdf'
    result = []
    for mes in MESES:
        path = os.path.join(pdf_dir, f'{mes}.pdf')
        if os.path.exists(path):
            size = os.path.getsize(path)
            mtime = os.path.getmtime(path)
            result.append({'mes': mes, 'size': size, 'mtime': mtime})
    return jsonify(result)


if __name__ == '__main__':
    print('Abre http://localhost:5000 en tu navegador')
    app.run(debug=True, port=5000)
