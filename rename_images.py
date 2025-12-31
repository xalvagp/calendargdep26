import os
import shutil

# Create imagenes_ejemplo directory if it doesn't exist
os.makedirs('imagenes_ejemplo', exist_ok=True)

# Mapping of numbered files to month names
file_mapping = {
    '01-Enero.jpg': 'Enero.jpg',
    '02-Febrero.jpg': 'Febrero.jpg',
    '03-Marzo.jpg': 'Marzo.jpg',
    '04-Abril.jpg': 'Abril.jpg',
    '05-Mayo.jpg': 'Mayo.jpg',
    '06-Junio.JPG': 'Junio.jpg',
    '07-Julio.jpg': 'Julio.jpg',
    '08-Agosto.jpg': 'Agosto.jpg',
    '09-Septiembre.jpg': 'Septiembre.jpg',
    '10-Octubre.jpg': 'Octubre.jpg',
    '11-Noviembre.jpg': 'Noviembre.jpg',
    '12-Diciembre.jpg': 'Diciembre.jpg'
}

# Copy and rename files
for old_name, new_name in file_mapping.items():
    src = os.path.join('Pics', old_name)
    dst = os.path.join('imagenes_ejemplo', new_name)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f'Copied {old_name} to {new_name}')
    else:
        print(f'Warning: Source file {old_name} not found')
