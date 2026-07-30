from flask import Flask, request, jsonify, session, send_from_directory
import mysql.connector

app = Flask(__name__)
app.secret_key = 'clave_secreta_cambiala'

DB_CONFIG = {
    'host':     'localhost',
    'user':     'root',
    'password': '',
    'database': 'pagina_del_agua'
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# ── Páginas ─────────────────────────────────────────────────────

@app.route('/')
def index():
    session.clear()  
    return send_from_directory('login', 'index.html')

@app.route('/agua')
def agua():
    if 'usuario' not in session:
        return '<script>alert("Debes iniciar sesion primero"); window.location="/";</script>'
    return send_from_directory('pagina_wed', 'index_2.html')

# ── Archivos estáticos ──────────────────────────────────────────

@app.route('/login/<path:filename>')
def login_static(filename):
    return send_from_directory('login', filename)

@app.route('/pagina_wed/<path:filename>')
def pagina_wed_static(filename):
    return send_from_directory('pagina_wed', filename)

# ── API Registro ────────────────────────────────────────────────

@app.route('/api/registro', methods=['POST'])
def registro():
    datos    = request.get_json()
    nombre   = datos.get('nombre', '').strip()
    correo   = datos.get('correo', '').strip()
    password = datos.get('password', '').strip()

    if not nombre or not correo or not password:
        return jsonify({'ok': False, 'mensaje': 'Todos los campos son obligatorios'}), 400
    if len(password) < 8:
        return jsonify({'ok': False, 'mensaje': 'La contraseña debe tener mínimo 8 caracteres'}), 400

    try:
        db  = get_db()
        cur = db.cursor()
        cur.execute('SELECT id FROM usuarios WHERE correo = %s', (correo,))
        if cur.fetchone():
            return jsonify({'ok': False, 'mensaje': 'El correo ya está registrado'}), 409
        cur.execute(
            'INSERT INTO usuarios (nombre, correo, password) VALUES (%s, %s, %s)',
            (nombre, correo, password)
        )
        db.commit()
        cur.close()
        db.close()
        return jsonify({'ok': True, 'mensaje': '¡Cuenta creada exitosamente!'})
    except Exception as e:
        return jsonify({'ok': False, 'mensaje': f'Error: {str(e)}'}), 500

# ── API Login ───────────────────────────────────────────────────

@app.route('/api/login', methods=['POST'])
def login():
    datos    = request.get_json()
    correo   = datos.get('correo', '').strip()
    password = datos.get('password', '').strip()

    if not correo or not password:
        return jsonify({'ok': False, 'mensaje': 'Completa todos los campos'}), 400

    try:
        db  = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute(
            'SELECT * FROM usuarios WHERE correo = %s AND password = %s',
            (correo, password)
        )
        usuario = cur.fetchone()
        cur.close()
        db.close()

        if usuario:
            session['usuario'] = usuario['nombre']
            session['correo']  = usuario['correo']
            return jsonify({'ok': True, 'nombre': usuario['nombre'], 'redirect': '/agua'})
        else:
            return jsonify({'ok': False, 'mensaje': 'Correo o contraseña incorrectos'}), 401
    except Exception as e:
        return jsonify({'ok': False, 'mensaje': f'Error: {str(e)}'}), 500

# ── API Logout ──────────────────────────────────────────────────

@app.route('/api/logout')
def logout():
    session.clear()
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)