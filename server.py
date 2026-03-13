from flask import Flask, request, jsonify, send_from_directory
import os
import subprocess

app = Flask(__name__, static_folder='.')

MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.webp'}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/api/status/<int:year>')
def status(year):
    pics_dir = os.path.join('pics', str(year))
    result = {}
    for mes in MESES:
        found_ext = None
        for ext in ALLOWED_EXTENSIONS:
            if os.path.exists(os.path.join(pics_dir, mes + ext)):
                found_ext = ext
                break
            if os.path.exists(os.path.join(pics_dir, mes + ext.upper())):
                found_ext = ext.upper()
                break
        result[mes] = found_ext is not None
    return jsonify(result)


@app.route('/api/upload/<int:year>/<mes>', methods=['POST'])
def upload(year, mes):
    if mes not in MESES:
        return jsonify({'error': 'Mes no válido'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No se recibió ningún archivo'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'Nombre de archivo vacío'}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': f'Extensión no permitida: {ext}'}), 400

    pics_dir = os.path.join('pics', str(year))
    os.makedirs(pics_dir, exist_ok=True)

    # Eliminar archivos anteriores del mismo mes
    for old_ext in list(ALLOWED_EXTENSIONS) + [e.upper() for e in ALLOWED_EXTENSIONS]:
        old_path = os.path.join(pics_dir, mes + old_ext)
        if os.path.exists(old_path):
            os.remove(old_path)

    save_path = os.path.join(pics_dir, mes + ext)
    file.save(save_path)
    return jsonify({'success': True, 'path': save_path})


@app.route('/api/generate/<int:year>', methods=['POST'])
def generate(year):
    try:
        result = subprocess.run(
            ['python3', 'generate_calendars.py', str(year)],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            return jsonify({'success': True, 'output': result.stdout})
        else:
            return jsonify({'success': False, 'error': result.stderr}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Tiempo de espera agotado (>5 min)'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
