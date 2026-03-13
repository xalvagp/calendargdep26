from flask import Flask, request, jsonify, send_from_directory, send_file
from PIL import Image
from io import BytesIO
import os
import subprocess

app = Flask(__name__, static_folder='.')

MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.webp']
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB


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
