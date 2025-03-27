from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import pytz
from functools import wraps
import os
from dotenv import load_dotenv

load_dotenv()  # Cargar variables de entorno

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tu_clave_secreta_aqui')

# Configuración de la base de datos
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///inventario.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelos
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cajas = db.Column(db.Integer, default=0)
    rejas = db.Column(db.Integer, default=0)
    piezas = db.Column(db.Integer, default=0)
    movimientos = db.relationship('Movimiento', backref='producto', lazy=True)
    pedidos = db.relationship('Pedido', backref='producto', lazy=True)

class Movimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)  # entrada, salida, devolucion
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cajas = db.Column(db.Integer, default=0)
    rejas = db.Column(db.Integer, default=0)
    piezas = db.Column(db.Integer, default=0)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.Column(db.String(100), nullable=False)

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    pedidos = db.relationship('Pedido', backref='cliente', lazy=True)

class Repartidor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    pedidos = db.relationship('Pedido', backref='repartidor', lazy=True)

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    repartidor_id = db.Column(db.Integer, db.ForeignKey('repartidor.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cajas = db.Column(db.Integer, default=0)
    rejas = db.Column(db.Integer, default=0)
    piezas = db.Column(db.Integer, default=0)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente o entregado

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='usuario')  # admin o usuario

class Configuracion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_empresa = db.Column(db.String(100), nullable=False, default='Sistema de Inventario de Huevos')
    idioma = db.Column(db.String(20), nullable=False, default='es')
    zona_horaria = db.Column(db.String(50), nullable=False, default='America/Mexico_City')
    modo_oscuro = db.Column(db.Boolean, default=False)

# Decorador para proteger rutas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Rutas públicas
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        password = request.form.get('password')
        
        if not nombre or not password:
            flash('Por favor ingrese usuario y contraseña', 'error')
            return redirect(url_for('login'))
        
        usuario = Usuario.query.filter_by(nombre=nombre).first()
        if usuario and check_password_hash(usuario.password_hash, password):
            session['usuario_id'] = usuario.id
            session['usuario_nombre'] = usuario.nombre
            session['usuario_rol'] = usuario.rol
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Rutas protegidas
@app.route('/')
@login_required
def index():
    active_tab = request.args.get('active_tab', 'inventario')
    
    productos = Producto.query.all()
    movimientos = Movimiento.query.order_by(Movimiento.fecha.desc()).all()
    clientes = Cliente.query.all()
    repartidores = Repartidor.query.all()
    pedidos = Pedido.query.order_by(Pedido.fecha.desc()).all()
    
    config = Configuracion.query.first()
    if not config:
        config = Configuracion()
        db.session.add(config)
        db.session.commit()
    
    return render_template('index.html', 
                          productos=productos, 
                          movimientos=movimientos,
                          clientes=clientes,
                          repartidores=repartidores,
                          pedidos=pedidos,
                          active_tab=active_tab,
                          config=config)

@app.route('/agregar_producto', methods=['POST'])
@login_required
def agregar_producto():
    nombre = request.form['nombre']
    if nombre:
        producto = Producto(nombre=nombre)
        db.session.add(producto)
        db.session.commit()
        flash('Producto agregado exitosamente', 'success')
    return redirect(url_for('index', active_tab='inventario'))

@app.route('/registrar_movimiento', methods=['POST'])
@login_required
def registrar_movimiento():
    producto_id = request.form['producto_id']
    tipo = request.form['tipo']
    cajas = int(request.form['cajas']) if request.form['cajas'] else 0
    rejas = int(request.form['rejas']) if request.form['rejas'] else 0
    piezas = int(request.form['piezas']) if request.form['piezas'] else 0
    
    producto = Producto.query.get(producto_id)
    if not producto:
        flash('Producto no encontrado', 'error')
        return redirect(url_for('index', active_tab='movimientos'))
    
    if tipo == 'salida':
        # Verificar si hay suficiente stock
        if (producto.cajas < cajas or 
            producto.rejas < rejas or 
            producto.piezas < piezas):
            flash('No hay suficiente stock para realizar esta operación', 'error')
            return redirect(url_for('index', active_tab='movimientos'))
        
        # Actualizar stock (restar)
        producto.cajas -= cajas
        producto.rejas -= rejas
        producto.piezas -= piezas
    elif tipo == 'entrada':
        # Actualizar stock (sumar)
        producto.cajas += cajas
        producto.rejas += rejas
        producto.piezas += piezas
    elif tipo == 'devolucion':
        # Actualizar stock (sumar - es una devolución)
        producto.cajas += cajas
        producto.rejas += rejas
        producto.piezas += piezas
        
    # Registrar el movimiento
    movimiento = Movimiento(
        producto_id=producto_id,
        tipo=tipo,
        cajas=cajas,
        rejas=rejas,
        piezas=piezas,
        usuario=session.get('usuario_nombre', 'Sistema')
    )
    db.session.add(movimiento)
    db.session.commit()
    flash('Movimiento registrado exitosamente', 'success')
    return redirect(url_for('index', active_tab='movimientos'))

@app.route('/agregar_cliente', methods=['POST'])
@login_required
def agregar_cliente():
    nombre = request.form['nombre']
    telefono = request.form['telefono']
    direccion = request.form['direccion']
    
    if nombre and telefono:
        cliente = Cliente(nombre=nombre, telefono=telefono, direccion=direccion)
        db.session.add(cliente)
        db.session.commit()
        flash('Cliente agregado exitosamente', 'success')
    else:
        flash('Nombre y teléfono son requeridos', 'error')
    
    return redirect(url_for('index', active_tab='clientes'))

@app.route('/agregar_repartidor', methods=['POST'])
@login_required
def agregar_repartidor():
    nombre = request.form['nombre']
    telefono = request.form['telefono']
    
    if nombre and telefono:
        repartidor = Repartidor(nombre=nombre, telefono=telefono)
        db.session.add(repartidor)
        db.session.commit()
        flash('Repartidor agregado exitosamente', 'success')
    else:
        flash('Nombre y teléfono son requeridos', 'error')
    
    return redirect(url_for('index', active_tab='repartidores'))

@app.route('/registrar_pedido', methods=['POST'])
@login_required
def registrar_pedido():
    cliente_id = request.form['cliente_id']
    repartidor_id = request.form['repartidor_id']
    producto_id = request.form['producto_id']
    cajas = int(request.form['cajas']) if request.form['cajas'] else 0
    rejas = int(request.form['rejas']) if request.form['rejas'] else 0
    piezas = int(request.form['piezas']) if request.form['piezas'] else 0
    
    # Verificar que existan todos los elementos relacionados
    cliente = Cliente.query.get(cliente_id)
    repartidor = Repartidor.query.get(repartidor_id)
    producto = Producto.query.get(producto_id)
    
    if not cliente or not repartidor or not producto:
        flash('Error: cliente, repartidor o producto no encontrado', 'error')
        return redirect(url_for('index', active_tab='pedidos'))
    
    if cajas <= 0 and rejas <= 0 and piezas <= 0:
        flash('Debe especificar al menos una cantidad', 'error')
        return redirect(url_for('index', active_tab='pedidos'))
    
    # Verificar si hay suficiente stock
    if (producto.cajas < cajas or 
        producto.rejas < rejas or 
        producto.piezas < piezas):
        flash('No hay suficiente stock para realizar este pedido', 'error')
        return redirect(url_for('index', active_tab='pedidos'))
    
    # Registrar el pedido
    pedido = Pedido(
        cliente_id=cliente_id,
        repartidor_id=repartidor_id,
        producto_id=producto_id,
        cajas=cajas,
        rejas=rejas,
        piezas=piezas,
        estado='pendiente'
    )
    db.session.add(pedido)
    
    # Actualizar stock (restar)
    producto.cajas -= cajas
    producto.rejas -= rejas
    producto.piezas -= piezas
    
    # Registrar el movimiento de salida
    movimiento = Movimiento(
        producto_id=producto_id,
        tipo='salida',
        cajas=cajas,
        rejas=rejas,
        piezas=piezas,
        usuario=session.get('usuario_nombre', 'Sistema')
    )
    db.session.add(movimiento)
    
    db.session.commit()
    flash('Pedido registrado exitosamente', 'success')
    return redirect(url_for('index', active_tab='pedidos'))

@app.route('/cambiar_estado_pedido/<int:pedido_id>', methods=['POST'])
@login_required
def cambiar_estado_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    nuevo_estado = request.form.get('estado')
    
    if nuevo_estado in ['pendiente', 'entregado']:
        pedido.estado = nuevo_estado
        db.session.commit()
        flash(f'Estado del pedido actualizado a {nuevo_estado}', 'success')
    else:
        flash('Estado de pedido no válido', 'error')
        
    return redirect(url_for('index', active_tab='pedidos'))

@app.route('/configuracion', methods=['GET', 'POST'])
@login_required
def configuracion():
    if session['usuario_rol'] != 'admin':
        flash('Acceso no autorizado', 'error')
        return redirect(url_for('index'))
    
    config = Configuracion.query.first()
    if not config:
        config = Configuracion()
        db.session.add(config)
        db.session.commit()
    
    if request.method == 'POST':
        config.nombre_empresa = request.form['nombre_empresa']
        config.idioma = request.form['idioma']
        config.zona_horaria = request.form['zona_horaria']
        config.modo_oscuro = 'modo_oscuro' in request.form
        db.session.commit()
        flash('Configuración actualizada', 'success')
        return redirect(url_for('configuracion'))
    
    usuarios = Usuario.query.all()
    return render_template('configuracion.html', config=config, usuarios=usuarios)

@app.route('/actualizar_modo_oscuro', methods=['POST'])
@login_required
def actualizar_modo_oscuro():
    if session['usuario_rol'] != 'admin':
        return jsonify({'error': 'Acceso no autorizado'})
    
    config = Configuracion.query.first()
    if config:
        config.modo_oscuro = request.json.get('modo_oscuro', False)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Configuración no encontrada'})

@app.route('/crear_usuario', methods=['POST'])
@login_required
def crear_usuario():
    if session['usuario_rol'] != 'admin':
        return jsonify({'error': 'No autorizado'})
    
    nombre = request.form.get('nombre')
    password = request.form.get('password')
    rol = request.form.get('rol')
    
    # Verificar si el usuario ya existe
    usuario_existente = Usuario.query.filter_by(nombre=nombre).first()
    if usuario_existente:
        return jsonify({'error': 'El nombre de usuario ya existe'})
    
    if nombre and password and rol in ['usuario', 'admin']:
        nuevo_usuario = Usuario(
            nombre=nombre,
            password_hash=generate_password_hash(password),
            rol=rol
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Datos de usuario incorrectos'})

# Inicialización de la base de datos
def init_db():
    with app.app_context():
        db.create_all()
        
        # Crear productos iniciales si no existen
        productos_iniciales = [
            "huevo rojo200", "huevo blanco sucio", "huevo blanco200",
            "huevo rojo360", "huevo rojito", "huevo pewe"
        ]
        for nombre in productos_iniciales:
            if not Producto.query.filter_by(nombre=nombre).first():
                producto = Producto(nombre=nombre)
                db.session.add(producto)
        
        # Crear usuario admin si no existe
        admin = Usuario.query.filter_by(nombre='admin').first()
        if not admin:
            admin = Usuario(
                nombre='admin',
                password_hash=generate_password_hash('admin123'),
                rol='admin'
            )
            db.session.add(admin)
            print("Usuario admin creado exitosamente")
        
        # Crear configuración inicial si no existe
        config = Configuracion.query.first()
        if not config:
            config = Configuracion()
            db.session.add(config)
            print("Configuración inicial creada exitosamente")
        
        db.session.commit()
        print("Base de datos inicializada correctamente")

# Inicializar la base de datos al arrancar
init_db()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)