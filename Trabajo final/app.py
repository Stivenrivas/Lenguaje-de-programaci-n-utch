from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import pymysql
import hashlib
from datetime import timedelta
import os

app = Flask(__name__, static_folder=None)
app.secret_key = 'turismo_choco_secret_key_2024'
app.permanent_session_lifetime = timedelta(days=1)
CORS(app, supports_credentials=True)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'turismo_choco',
    'charset': 'utf8mb4'
}

def get_db():
    return pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    nombre = data.get('nombre')
    email = data.get('email')
    password = data.get('password')

    if not all([nombre, email, password]):
        return jsonify({'error': 'Todos los campos son obligatorios'}), 400

    hashed = hashlib.sha256(password.encode()).hexdigest()

    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s, %s, %s, 'usuario')",
                       (nombre, email, hashed))
            conn.commit()
        conn.close()
        return jsonify({'message': 'Registro exitoso'}), 201
    except pymysql.err.IntegrityError:
        return jsonify({'error': 'El email ya esta registrado'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    hashed = hashlib.sha256(password.encode()).hexdigest()

    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM usuarios WHERE email = %s AND password = %s", (email, hashed))
        user = cur.fetchone()
    conn.close()

    if user:
        session['user_id'] = user['id']
        session['rol'] = user['rol']
        session['nombre'] = user['nombre']
        session['email'] = user['email']
        return jsonify({
            'message': 'Login exitoso',
            'user': {'id': user['id'], 'nombre': user['nombre'], 'email': user['email'], 'rol': user['rol']}
        })
    return jsonify({'error': 'Credenciales invalidas'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Sesion cerrada'})

@app.route('/api/session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({
            'user': {'id': session['user_id'], 'nombre': session['nombre'], 'email': session.get('email', ''), 'rol': session['rol']}
        })
    return jsonify({'user': None}), 401

@app.route('/api/destinos', methods=['GET'])
def get_destinos():
    municipio = request.args.get('municipio')
    categoria = request.args.get('categoria')
    conn = get_db()
    with conn.cursor() as cur:
        query = "SELECT d.*, u.nombre as creador FROM destinos d LEFT JOIN usuarios u ON d.creado_por = u.id"
        params = []
        conditions = []
        if municipio:
            conditions.append("d.municipio = %s")
            params.append(municipio)
        if categoria:
            conditions.append("d.categoria = %s")
            params.append(categoria)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY d.fecha_creacion DESC"
        cur.execute(query, params)
        destinos = cur.fetchall()
    conn.close()
    return jsonify(destinos)

@app.route('/api/destinos/<int:id>', methods=['GET'])
def get_destino(id):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT d.*, u.nombre as creador FROM destinos d LEFT JOIN usuarios u ON d.creado_por = u.id WHERE d.id = %s", (id,))
        destino = cur.fetchone()
    conn.close()
    if destino:
        return jsonify(destino)
    return jsonify({'error': 'Destino no encontrado'}), 404

@app.route('/api/destinos', methods=['POST'])
def create_destino():
    if 'user_id' not in session or session['rol'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    data = request.json
    required = ['nombre', 'descripcion', 'municipio', 'categoria']
    if not all(data.get(f) for f in required):
        return jsonify({'error': 'Campos obligatorios faltantes'}), 400
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO destinos (nombre, descripcion, actividades, ubicacion, municipio, categoria, imagen_url, creado_por)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                   (data['nombre'], data.get('descripcion'), data.get('actividades'), data.get('ubicacion'),
                    data['municipio'], data['categoria'], data.get('imagen_url'), session['user_id']))
        conn.commit()
        destino_id = cur.lastrowid
    conn.close()
    return jsonify({'message': 'Destino creado', 'id': destino_id}), 201

@app.route('/api/destinos/<int:id>', methods=['PUT'])
def update_destino(id):
    if 'user_id' not in session or session['rol'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    data = request.json
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""UPDATE destinos SET nombre=%s, descripcion=%s, actividades=%s, ubicacion=%s,
                       municipio=%s, categoria=%s, imagen_url=%s WHERE id=%s""",
                   (data.get('nombre'), data.get('descripcion'), data.get('actividades'), data.get('ubicacion'),
                    data.get('municipio'), data.get('categoria'), data.get('imagen_url'), id))
        conn.commit()
    conn.close()
    return jsonify({'message': 'Destino actualizado'})

@app.route('/api/destinos/<int:id>', methods=['DELETE'])
def delete_destino(id):
    if 'user_id' not in session or session['rol'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM destinos WHERE id = %s", (id,))
        conn.commit()
    conn.close()
    return jsonify({'message': 'Destino eliminado'})

@app.route('/api/usuarios', methods=['GET'])
def get_usuarios():
    if 'user_id' not in session or session['rol'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT id, nombre, email, rol, fecha_creacion FROM usuarios ORDER BY fecha_creacion DESC")
        usuarios = cur.fetchall()
    conn.close()
    return jsonify(usuarios)

@app.route('/api/usuarios/<int:id>', methods=['DELETE'])
def delete_usuario(id):
    if 'user_id' not in session or session['rol'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM usuarios WHERE id = %s AND rol != 'admin'", (id,))
        conn.commit()
    conn.close()
    return jsonify({'message': 'Usuario eliminado'})

@app.route('/')
def index():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'wed_site'), 'introduccion.html')

@app.route('/home')
def home():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'wed_site'), 'index.html')

@app.route('/dashboard')
def dashboard():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'wed_site'), 'dashboard.html')

@app.route('/login/')
def login_page():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'login'), 'login.html')

@app.route('/<path:filename>')
def serve_static(filename):
    base_dir = os.path.dirname(__file__)
    for folder in ['wed_site', 'login']:
        path = os.path.join(base_dir, folder, filename)
        if os.path.exists(path):
            return send_from_directory(os.path.join(base_dir, folder), filename)
    return jsonify({'error': 'Archivo no encontrado'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)