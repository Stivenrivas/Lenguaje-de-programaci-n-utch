import os, re, uuid, hashlib, datetime, mysql.connector
from flask import Flask, request, jsonify, send_from_directory, session, g, redirect
from flask_cors import CORS
from functools import wraps

app = Flask(__name__, static_folder='.')
app.secret_key = os.getenv('SECRET_KEY', 'LinkWork-2026-Secret-Key!')
app.config.update(
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)
CORS(app, supports_credentials=True)
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASS', ''),
    'database': os.getenv('DB_NAME', 'Linkwork'),
    'port': int(os.getenv('DB_PORT', '3306')),
}

def allowed_file(name):
    return '.' in name and name.rsplit('.', 1)[1].lower() in ALLOWED_EXT

# --- SQLite ---

def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(**DB_CONFIG)
        g.db.autocommit = False
    return g.db

@app.teardown_appcontext
def close_db(e):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def query(sql, params=None):
    c = get_db().cursor(dictionary=True)
    c.execute(sql, params or ())
    rows = c.fetchall()
    c.close()
    return rows

def query_one(sql, params=None):
    c = get_db().cursor(dictionary=True)
    c.execute(sql, params or ())
    r = c.fetchone()
    c.close()
    return r if r else None

def execute(sql, params=None):
    db = get_db()
    c = db.cursor()
    c.execute(sql, params or ())
    db.commit()
    n = c.rowcount
    c.close()
    return n

def execute_lastid(sql, params=None):
    db = get_db()
    c = db.cursor()
    c.execute(sql, params or ())
    db.commit()
    n = c.lastrowid
    c.close()
    return n

def init_db():
    db = mysql.connector.connect(**DB_CONFIG)
    c = db.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE,
        phone VARCHAR(255) NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL,
        frecuencia INT DEFAULT 0,
        avatar VARCHAR(500),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS empleos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        company VARCHAR(255) NOT NULL,
        location VARCHAR(255) NOT NULL,
        salary VARCHAR(255),
        description TEXT NOT NULL,
        email VARCHAR(255) NOT NULL,
        employer VARCHAR(255) NOT NULL,
        imagen VARCHAR(500),
        tipo VARCHAR(50) DEFAULT 'fijo',
        horas INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS servicios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        category VARCHAR(255) NOT NULL,
        price VARCHAR(255),
        description TEXT NOT NULL,
        providerEmail VARCHAR(255) NOT NULL,
        provider VARCHAR(255) NOT NULL,
        imagen VARCHAR(500),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS aplicaciones (
        id INT AUTO_INCREMENT PRIMARY KEY,
        tipo VARCHAR(50) NOT NULL,
        ref_id INT NOT NULL,
        solicitante_id INT NOT NULL,
        solicitante_nombre VARCHAR(255) NOT NULL,
        solicitante_email VARCHAR(255) NOT NULL,
        propietario_email VARCHAR(255) NOT NULL,
        mensaje TEXT,
        estado VARCHAR(50) DEFAULT 'pendiente',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS contratos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        empleador_id INT NOT NULL,
        empleador_email VARCHAR(255) NOT NULL,
        trabajador_id INT NOT NULL,
        trabajador_nombre VARCHAR(255) NOT NULL,
        trabajador_email VARCHAR(255) NOT NULL,
        tipo VARCHAR(50) NOT NULL,
        ref_id INT NOT NULL,
        ref_titulo VARCHAR(255) NOT NULL,
        monto DECIMAL(12,2) DEFAULT 0,
        horas INT DEFAULT 0,
        estado VARCHAR(50) DEFAULT 'activo',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS finanzas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        user_email VARCHAR(255) NOT NULL,
        tipo VARCHAR(50) NOT NULL,
        categoria VARCHAR(255) NOT NULL,
        ref_tipo VARCHAR(50),
        ref_id INT,
        concepto TEXT NOT NULL,
        monto DECIMAL(12,2) NOT NULL,
        fecha_registro DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS mensajes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        remitente_id INT NOT NULL,
        remitente_nombre VARCHAR(255) NOT NULL,
        destinatario_id INT NOT NULL,
        destinatario_nombre VARCHAR(255) NOT NULL,
        tipo_ref VARCHAR(50) NOT NULL,
        ref_id INT NOT NULL,
        mensaje TEXT NOT NULL,
        leido INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute("SELECT id FROM usuarios WHERE email=%s", ('admin@admin.com',))
    if not c.fetchone():
        admin_pw = hashlib.sha256(b'admin123').hexdigest()
        c.execute("INSERT INTO usuarios (username, email, phone, password, role) VALUES (%s,%s,%s,%s,%s)",
                   ('admin', 'admin@admin.com', '0000000000', admin_pw, 'admin'))
    db.commit()
    c.close()
    db.close()

init_db()

# --- Auth helpers ---

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        if session['user']['role'] != 'admin':
            return jsonify({'error': 'Se requieren permisos de administrador'}), 403
        return f(*args, **kwargs)
    return decorated

def get_user():
    return session.get('user')

# --- Auth API ---

@app.route('/api/me')
def api_me():
    if 'user' in session:
        r = query_one('SELECT id, username, email, phone, role, frecuencia FROM usuarios WHERE email=%s', (session['user']['email'],))
        if r:
            session['user'] = dict(r)
            return jsonify(session['user'])
        return jsonify(session['user'])
    return jsonify({'error': 'No autenticado'}), 401

@app.route('/api/usuarios', methods=['GET'])
@admin_required
def api_get_usuarios():
    return jsonify(query('SELECT id, username, email, phone, role, frecuencia, created_at FROM usuarios ORDER BY id'))

@app.route('/api/registro', methods=['POST'])
def api_registro():
    data = request.json
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    phone = (data.get('phone') or '').strip()
    password = data.get('password', '')
    role = data.get('role', '')
    if not all([username, email, phone, password, role]):
        return jsonify({'error': 'Todos los campos son obligatorios'}), 400
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return jsonify({'error': 'Correo inválido'}), 400
    if len(password) < 6:
        return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
    if query_one('SELECT id FROM usuarios WHERE email = %s', (email,)):
        return jsonify({'error': 'Este correo ya está registrado'}), 409
    if query_one('SELECT id FROM usuarios WHERE username = %s', (username,)):
        return jsonify({'error': 'Este usuario ya existe'}), 409
    execute('INSERT INTO usuarios (username, email, phone, password, role) VALUES (%s, %s, %s, %s, %s)',
            (username, email, phone, hash_pw(password), role))
    return jsonify({'message': 'Cuenta creada correctamente'}), 201

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.json
        email = (data.get('email') or '').strip()
        password = data.get('password', '')
        user = query_one('SELECT * FROM usuarios WHERE email = %s AND password = %s', (email, hash_pw(password)))
        if not user:
            return jsonify({'error': 'Credenciales incorrectas'}), 401
        session['user'] = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'phone': user['phone'],
            'frecuencia': user.get('frecuencia', 0),
        }
        session.permanent = True
        return jsonify(session['user'])
    except Exception as e:
        # --- TEMPORAL: solo para depurar, quitar este bloque después ---
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'DEBUG {type(e).__name__}: {e}'}), 500
        # --- fin bloque temporal ---

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'message': 'Sesión cerrada'})

@app.route('/api/frecuentes', methods=['GET'])
@login_required
def api_frecuentes():
    return jsonify(query(
        'SELECT id, username, email, role, frecuencia FROM usuarios WHERE frecuencia>0 ORDER BY frecuencia DESC'
    ))

@app.route('/api/usuarios/<email>', methods=['DELETE'])
@admin_required
def api_delete_usuario(email):
    execute('DELETE FROM usuarios WHERE email = %s AND role != "admin"', (email,))
    return jsonify({'message': 'Usuario eliminado'})

# --- Upload ---

@app.route('/api/upload', methods=['POST'])
@login_required
def api_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No se envió archivo'}), 400
    f = request.files['file']
    if not f or not allowed_file(f.filename):
        return jsonify({'error': 'Formato no permitido (png, jpg, jpeg, gif, webp)'}), 400
    ext = f.filename.rsplit('.', 1)[1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    f.save(os.path.join(UPLOAD_DIR, name))
    return jsonify({'url': f'/uploads/{name}'})

@app.route('/uploads/<name>')
def serve_upload(name):
    return send_from_directory(UPLOAD_DIR, name)

# --- Empleos ---

@app.route('/api/empleos', methods=['GET'])
def api_get_empleos():
    return jsonify(query('SELECT * FROM empleos ORDER BY created_at DESC'))

@app.route('/api/empleos/mis', methods=['POST'])
@login_required
def api_mis_empleos():
    return jsonify(query('SELECT * FROM empleos WHERE email = %s ORDER BY created_at DESC', (session['user']['email'],)))

@app.route('/api/empleos', methods=['POST'])
@login_required
def api_create_empleo():
    data = request.json
    if not all([data.get('title'), data.get('company'), data.get('location'), data.get('description')]):
        return jsonify({'error': 'Completa todos los campos obligatorios'}), 400
    execute(
        'INSERT INTO empleos (title, company, location, salary, description, email, employer, imagen, tipo, horas) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
        (data['title'], data['company'], data['location'], data.get('salary', ''), data['description'],
         session['user']['email'], session['user']['username'],
         data.get('imagen'), data.get('tipo', 'fijo'), int(data.get('horas', 0)))
    )
    return jsonify({'message': 'Empleo publicado'}), 201

@app.route('/api/empleos/<int:id>', methods=['DELETE'])
@login_required
def api_delete_empleo(id):
    execute('DELETE FROM empleos WHERE id = %s', (id,))
    return jsonify({'message': 'Empleo eliminado'})

# --- Servicios ---

@app.route('/api/servicios', methods=['GET'])
def api_get_servicios():
    return jsonify(query('SELECT * FROM servicios ORDER BY created_at DESC'))

@app.route('/api/servicios/mis', methods=['POST'])
@login_required
def api_mis_servicios():
    return jsonify(query('SELECT * FROM servicios WHERE providerEmail = %s ORDER BY created_at DESC', (session['user']['email'],)))

@app.route('/api/servicios', methods=['POST'])
@login_required
def api_create_servicio():
    data = request.json
    if not all([data.get('title'), data.get('category'), data.get('description')]):
        return jsonify({'error': 'Completa todos los campos obligatorios'}), 400
    execute(
        'INSERT INTO servicios (title, category, price, description, providerEmail, provider, imagen) VALUES (%s,%s,%s,%s,%s,%s,%s)',
        (data['title'], data['category'], data.get('price', ''), data['description'],
         session['user']['email'], session['user']['username'], data.get('imagen'))
    )
    return jsonify({'message': 'Servicio publicado'}), 201

@app.route('/api/servicios/<int:id>', methods=['DELETE'])
@login_required
def api_delete_servicio(id):
    execute('DELETE FROM servicios WHERE id = %s', (id,))
    return jsonify({'message': 'Servicio eliminado'})

# --- Aplicaciones ---

@app.route('/api/aplicaciones', methods=['POST'])
@login_required
def api_aplicar():
    data = request.json
    user = get_user()
    tipo = data.get('tipo')
    ref_id = data.get('ref_id')
    mensaje = (data.get('mensaje') or '').strip()
    if tipo not in ('empleo', 'servicio') or not ref_id:
        return jsonify({'error': 'Datos inválidos'}), 400
    if query_one('SELECT id FROM aplicaciones WHERE tipo=%s AND ref_id=%s AND solicitante_email=%s', (tipo, ref_id, user['email'])):
        return jsonify({'error': 'Ya te has postulado a esto'}), 409
    prop_email = None
    if tipo == 'empleo':
        r = query_one('SELECT email FROM empleos WHERE id=%s', (ref_id,))
        if r: prop_email = r['email']
    else:
        r = query_one('SELECT providerEmail FROM servicios WHERE id=%s', (ref_id,))
        if r: prop_email = r['providerEmail']
    if not prop_email:
        return jsonify({'error': 'Referencia no encontrada'}), 404
    execute(
        'INSERT INTO aplicaciones (tipo, ref_id, solicitante_id, solicitante_nombre, solicitante_email, propietario_email, mensaje) VALUES (%s,%s,%s,%s,%s,%s,%s)',
        (tipo, ref_id, user['id'], user['username'], user['email'], prop_email, mensaje)
    )
    if tipo == 'servicio':
        execute('UPDATE usuarios SET frecuencia = frecuencia + 1 WHERE email=%s', (user['email'],))
    return jsonify({'message': 'Postulación enviada'}), 201

@app.route('/api/aplicaciones/recibidas', methods=['GET'])
@login_required
def api_aplicaciones_recibidas():
    user = get_user()
    rows = query(
        'SELECT a.*, COALESCE(e.title, s.title) as ref_titulo '
        'FROM aplicaciones a '
        'LEFT JOIN empleos e ON a.tipo="empleo" AND a.ref_id=e.id '
        'LEFT JOIN servicios s ON a.tipo="servicio" AND a.ref_id=s.id '
        'WHERE a.propietario_email=%s ORDER BY a.created_at DESC', (user['email'],)
    )
    return jsonify(rows)

@app.route('/api/aplicaciones/enviadas', methods=['GET'])
@login_required
def api_aplicaciones_enviadas():
    user = get_user()
    rows = query(
        'SELECT a.*, COALESCE(e.title, s.title) as ref_titulo '
        'FROM aplicaciones a '
        'LEFT JOIN empleos e ON a.tipo="empleo" AND a.ref_id=e.id '
        'LEFT JOIN servicios s ON a.tipo="servicio" AND a.ref_id=s.id '
        'WHERE a.solicitante_email=%s ORDER BY a.created_at DESC', (user['email'],)
    )
    return jsonify(rows)

@app.route('/api/aplicaciones/<int:id>/estado', methods=['PATCH'])
@login_required
def api_cambiar_estado_aplicacion(id):
    data = request.json
    estado = data.get('estado')
    if estado not in ('aceptado', 'rechazado'):
        return jsonify({'error': 'Estado inválido'}), 400
    execute('UPDATE aplicaciones SET estado=%s WHERE id=%s', (estado, id))
    return jsonify({'message': f'Solicitud {estado}'})

# --- Contratos ---

@app.route('/api/contratos', methods=['POST'])
@login_required
def api_crear_contrato():
    data = request.json
    user = get_user()
    trabajador_id = data.get('trabajador_id')
    if not trabajador_id and data.get('trabajador_email'):
        r = query_one('SELECT id FROM usuarios WHERE email=%s', (data['trabajador_email'],))
        if r: trabajador_id = r['id']
    eid = execute_lastid(
        'INSERT INTO contratos (empleador_id, empleador_email, trabajador_id, trabajador_nombre, trabajador_email, tipo, ref_id, ref_titulo, monto, horas) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
        (user['id'], user['email'], trabajador_id, data['trabajador_nombre'],
         data['trabajador_email'], data['tipo'], data['ref_id'], data['ref_titulo'],
         float(data.get('monto', 0)), int(data.get('horas', 0)))
    )
    return jsonify({'id': eid, 'message': 'Contrato creado'}), 201

@app.route('/api/contratos/mis', methods=['GET'])
@login_required
def api_mis_contratos():
    user = get_user()
    return jsonify(query(
        'SELECT * FROM contratos WHERE empleador_email=%s OR trabajador_email=%s ORDER BY created_at DESC',
        (user['email'], user['email'])
    ))

@app.route('/api/contratos/<int:id>', methods=['PATCH'])
@login_required
def api_finalizar_contrato(id):
    execute('UPDATE contratos SET estado="finalizado" WHERE id=%s', (id,))
    return jsonify({'message': 'Contrato finalizado'})

# --- Finanzas ---

@app.route('/api/finanzas', methods=['POST'])
@login_required
def api_crear_finanza():
    data = request.json
    user = get_user()
    execute(
        'INSERT INTO finanzas (user_id, user_email, tipo, categoria, ref_tipo, ref_id, concepto, monto, fecha_registro) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
        (user['id'], user['email'], data['tipo'], data['categoria'],
         data.get('ref_tipo'), data.get('ref_id'), data['concepto'],
         float(data['monto']), data.get('fecha_registro', datetime.date.today().isoformat()))
    )
    return jsonify({'message': 'Registro financiero creado'}), 201

@app.route('/api/finanzas', methods=['GET'])
@login_required
def api_get_finanzas():
    user = get_user()
    year = request.args.get('year')
    month = request.args.get('month')
    sql = 'SELECT * FROM finanzas WHERE user_email=%s'
    params = [user['email']]
    if year and month:
        sql += ' AND YEAR(fecha_registro)=%s AND MONTH(fecha_registro)=%s'
        params += [str(int(year)), f"{int(month):02d}"]
    sql += ' ORDER BY fecha_registro DESC, created_at DESC'
    return jsonify(query(sql, tuple(params)))

@app.route('/api/finanzas/resumen', methods=['GET'])
@login_required
def api_resumen_finanzas():
    user = get_user()
    year = request.args.get('year', datetime.date.today().year)
    month = request.args.get('month', datetime.date.today().month)
    rows = query(
        'SELECT tipo, SUM(monto) as total FROM finanzas WHERE user_email=%s AND YEAR(fecha_registro)=%s AND MONTH(fecha_registro)=%s GROUP BY tipo',
        (user['email'], str(int(year)), f"{int(month):02d}")
    )
    ingresos = 0
    egresos = 0
    for r in rows:
        if r['tipo'] == 'ingreso':
            ingresos = float(r['total'])
        else:
            egresos = float(r['total'])
    return jsonify({'ingresos': ingresos, 'egresos': egresos, 'balance': ingresos - egresos})

# --- Mensajes ---

@app.route('/api/mensajes', methods=['POST'])
@login_required
def api_enviar_mensaje():
    data = request.json
    user = get_user()
    dest_id = data.get('destinatario_id')
    dest_nombre = data.get('destinatario_nombre')
    if not dest_id and data.get('destinatario_email'):
        r = query_one('SELECT id, username FROM usuarios WHERE email=%s', (data['destinatario_email'],))
        if r:
            dest_id = r['id']
            dest_nombre = dest_nombre or r['username']
    if not dest_id:
        return jsonify({'error': 'Destinatario no encontrado'}), 404
    eid = execute_lastid(
        'INSERT INTO mensajes (remitente_id, remitente_nombre, destinatario_id, destinatario_nombre, tipo_ref, ref_id, mensaje) VALUES (%s,%s,%s,%s,%s,%s,%s)',
        (user['id'], user['username'], dest_id, dest_nombre,
         data['tipo_ref'], data['ref_id'], data['mensaje'])
    )
    r = query_one('SELECT * FROM mensajes WHERE id=%s', (eid,))
    return jsonify(r if r else {'message': 'Mensaje enviado'}), 201

@app.route('/api/mensajes/<tipo_ref>/<int:ref_id>', methods=['GET'])
@login_required
def api_get_mensajes(tipo_ref, ref_id):
    user = get_user()
    if tipo_ref not in ('empleo', 'servicio'):
        return jsonify({'error': 'Tipo inválido'}), 400
    rows = query(
        'SELECT *, CASE WHEN remitente_id=%s THEN 1 ELSE 0 END as es_mio FROM mensajes WHERE tipo_ref=%s AND ref_id=%s AND (remitente_id=%s OR destinatario_id=%s) ORDER BY created_at ASC',
        (user['id'], tipo_ref, ref_id, user['id'], user['id'])
    )
    return jsonify(rows)

@app.route('/api/mensajes/no-leidos', methods=['GET'])
@login_required
def api_mensajes_no_leidos():
    user = get_user()
    r = query_one('SELECT COUNT(*) as total FROM mensajes WHERE destinatario_id=%s AND leido=0', (user['id'],))
    return jsonify({'total': r['total'] if r else 0})

@app.route('/api/mensajes/leer/<int:id>', methods=['PATCH'])
@login_required
def api_marcar_leido(id):
    execute('UPDATE mensajes SET leido=1 WHERE id=%s AND destinatario_id=%s', (id, get_user()['id']))
    return jsonify({'message': 'Marcado como leído'})

@app.route('/api/mensajes/conversaciones', methods=['GET'])
@login_required
def api_conversaciones():
    user = get_user()
    uid = user['id']
    rows = query(
        'SELECT m.*, '
        'CASE WHEN m.remitente_id=%s THEN m.destinatario_id ELSE m.remitente_id END as otro_id, '
        'CASE WHEN m.remitente_id=%s THEN m.destinatario_nombre ELSE m.remitente_nombre END as otro_nombre, '
        'm.mensaje as last_message, '
        '(SELECT COUNT(*) FROM mensajes WHERE tipo_ref=m.tipo_ref AND ref_id=m.ref_id AND destinatario_id=%s AND leido=0) as unread '
        'FROM mensajes m WHERE m.id IN '
        '(SELECT MAX(id) FROM mensajes WHERE remitente_id=%s OR destinatario_id=%s GROUP BY '
        'tipo_ref, ref_id, '
        'CASE WHEN remitente_id < destinatario_id THEN remitente_id ELSE destinatario_id END, '
        'CASE WHEN remitente_id < destinatario_id THEN destinatario_id ELSE remitente_id END) '
        'ORDER BY m.created_at DESC', (uid, uid, uid, uid, uid)
    )
    out = []
    for r in rows:
        d = dict(r)
        d['tipo'] = d['tipo_ref']
        ref = query_one(
            'SELECT title FROM empleos WHERE id=%s AND %s="empleo" UNION ALL SELECT title FROM servicios WHERE id=%s AND %s="servicio"',
            (d['ref_id'], d['tipo'], d['ref_id'], d['tipo'])
        )
        d['ref_titulo'] = ref['title'] if ref else ''
        out.append(d)
    return jsonify(out)

# --- Recomendaciones ---

@app.route('/api/recomendaciones', methods=['GET'])
@login_required
def api_recomendaciones():
    user = get_user()
    applied = query('SELECT ref_id FROM aplicaciones WHERE solicitante_email=%s AND tipo="empleo"', (user['email'],))
    applied_ids = [r['ref_id'] for r in applied]
    rows = query('SELECT * FROM empleos WHERE tipo="hora" AND horas > 0 AND horas < 48 ORDER BY horas DESC')
    out = []
    for r in rows:
        if r['id'] in applied_ids:
            continue
        h = r['horas'] or 0
        falta = 48 - h
        rec = 56 - h
        r['horas_actuales'] = h
        r['recomendacion'] = f"Te faltan {falta}h para llegar a 48h semanales (máx recomendado: {rec}h)"
        r['horas_faltantes'] = max(0, falta)
        out.append(r)
    return jsonify(out)

# --- Dashboard stats ---

@app.route('/api/dashboard/stats')
@admin_required
def api_dashboard_stats():
    u = query_one('SELECT COUNT(*) as t FROM usuarios')['t']
    e = query_one('SELECT COUNT(*) as t FROM empleos')['t']
    s = query_one('SELECT COUNT(*) as t FROM servicios')['t']
    c = query_one('SELECT COUNT(*) as t FROM contratos')['t']
    a = query_one('SELECT COUNT(*) as t FROM aplicaciones WHERE estado="pendiente"')['t']
    return jsonify({'usuarios': u, 'empleos': e, 'servicios': s, 'contratos': c, 'aplicaciones_pendientes': a})

# --- Static files ---

BASE = os.path.dirname(os.path.abspath(__file__))
LOGIN = os.path.join(BASE, 'Login')
WED = os.path.join(BASE, 'wed_site')

@app.route('/')
def index():
    return send_from_directory(LOGIN, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    if path.startswith('wed_site/') and 'user' not in session:
        return redirect('/')
    for dire in [BASE, LOGIN, WED]:
        p = os.path.join(dire, path)
        if os.path.isfile(p):
            return send_from_directory(dire, path)
    return '', 404

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'No encontrado'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    print(f'  LinkWork API corriendo en http://localhost:{port}')
    app.run(host='0.0.0.0', port=port, threaded=True)