from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models import User, Product, Order, FinanceEntry
from utils import generate_unique_id_for_user, generate_unique_product_code
from datetime import datetime, date
import os
from werkzeug.utils import secure_filename

bp = Blueprint('main', __name__)

# -------------------------
# Helpers para autenticación (muy simple)
# -------------------------
def login_user(user):
    # guardamos en session info mínima
    session['user_id'] = user.id
    session['user_role'] = user.role
    session['user_nombre'] = user.nombre

def logout_user():
    session.pop('user_id', None)
    session.pop('user_role', None)
    session.pop('user_nombre', None)

def current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    return User.query.get(uid)

# -------------------------
# Rutas: login / register
# -------------------------
@bp.route('/')
def home():
    # muestra página de login con opción registro
    return redirect(url_for('main.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # GET: muestra formulario
    # POST: recibe correo y password -> verifica -> login
    if request.method == 'POST':
        correo = request.form.get('correo')
        password = request.form.get('password')
        user = User.query.filter_by(correo=correo).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            # redirigimos según rol
            if user.role == 'emprendedor':
                return redirect(url_for('main.dashboard_emprendedor'))
            else:
                return "Cliente logueado (aún no implementado dashboard cliente)"
        else:
            flash('Credenciales inválidas')
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    # GET: muestra tipo de registro (emprendedor/cliente)
    # POST: procesa registro según role seleccionado
    if request.method == 'POST':
        role = request.form.get('role')  # 'emprendedor' o 'cliente'
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        correo = request.form.get('correo')
        telefono = request.form.get('telefono')
        carrera = request.form.get('carrera')
        password = request.form.get('password')

        # validaciones básicas
        if User.query.filter_by(correo=correo).first():
            flash('Correo ya registrado')
            return redirect(url_for('main.register'))

        password_hash = generate_password_hash(password)

        if role == 'emprendedor':
            nombre_emprendimiento = request.form.get('nombre_emprendimiento')
            id_emprendedor = generate_unique_id_for_user(10)
            user = User(
                id_emprendedor=id_emprendedor,
                nombre=nombre,
                apellido=apellido,
                carrera=carrera,
                correo=correo,
                telefono=telefono,
                password_hash=password_hash,
                role='emprendedor',
                nombre_emprendimiento=nombre_emprendimiento
            )
        else:
            user = User(
                nombre=nombre,
                apellido=apellido,
                carrera=carrera,
                correo=correo,
                telefono=telefono,
                password_hash=password_hash,
                role='cliente',
            )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        if user.role == 'emprendedor':
            return redirect(url_for('main.dashboard_emprendedor'))
        return "Cliente registrado y logueado"

    return render_template('register.html')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.login'))

# -------------------------
# Dashboard emprendedor
# -------------------------
@bp.route('/dashboard')
def dashboard_emprendedor():
    user = current_user()
    if not user or user.role != 'emprendedor':
        return redirect(url_for('main.login'))
    # obtenemos datos para mostrar en el dashboard
    productos = Product.query.filter_by(owner_id=user.id).all()
    pedidos = Order.query.filter_by(owner_id=user.id).order_by(Order.fecha.desc()).all()
    ingresos = sum([f.monto for f in FinanceEntry.query.filter_by(owner_id=user.id, tipo='ingreso')])
    egresos = sum([f.monto for f in FinanceEntry.query.filter_by(owner_id=user.id, tipo='egreso')])
    balance = ingresos - egresos
    return render_template('dashboard_emprendedor.html',
                           user=user, productos=productos, pedidos=pedidos,
                           ingresos=ingresos, egresos=egresos, balance=balance)

# -------------------------
# Productos: listar, crear, eliminar, buscar
# -------------------------
@bp.route('/productos', methods=['GET', 'POST'])
def productos():
    user = current_user()
    if not user or user.role != 'emprendedor':
        return redirect(url_for('main.login'))

    # Si es POST -> crear producto
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        precio = float(request.form.get('precio') or 0)
        descripcion = request.form.get('descripcion')
        cantidad = int(request.form.get('cantidad') or 0)

        codigo = generate_unique_product_code(5)

        # manejo de imagen (opcional)
        imagen = request.files.get('imagen')
        imagen_filename = None
        if imagen:
            filename = secure_filename(imagen.filename)
            imagen_filename = f"{codigo}_{filename}"
            imagen.save(os.path.join(current_app.config['UPLOAD_FOLDER'], imagen_filename))

        producto = Product(
            codigo=codigo, nombre=nombre, precio=precio,
            descripcion=descripcion, cantidad=cantidad,
            imagen_filename=imagen_filename, owner_id=user.id
        )
        db.session.add(producto)
        db.session.commit()
        flash('Producto creado')
        return redirect(url_for('main.productos'))

    # GET: buscar y listar
    q = request.args.get('q')
    if q:
        # buscamos por nombre o codigo (exacto o parcial)
        productos = Product.query.filter(Product.owner_id == user.id).filter(
            (Product.nombre.ilike(f"%{q}%")) | (Product.codigo.ilike(f"%{q}%"))
        ).all()
    else:
        productos = Product.query.filter_by(owner_id=user.id).all()

    return render_template('products_list.html', productos=productos, query=q)

@bp.route('/productos/eliminar/<int:product_id>', methods=['POST'])
def eliminar_producto(product_id):
    user = current_user()
    if not user or user.role != 'emprendedor':
        return redirect(url_for('main.login'))
    producto = Product.query.get(product_id)
    if producto and producto.owner_id == user.id:
        # eliminar imagen si existe
        if producto.imagen_filename:
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], producto.imagen_filename))
            except:
                pass
        db.session.delete(producto)
        db.session.commit()
        flash('Producto eliminado')
    return redirect(url_for('main.productos'))

# -------------------------
# Pedidos: listar y marcar entregado
# -------------------------
@bp.route('/pedidos')
def pedidos():
    user = current_user()
    if not user or user.role != 'emprendedor':
        return redirect(url_for('main.login'))
    pedidos = Order.query.filter_by(owner_id=user.id).order_by(Order.fecha.desc()).all()
    return render_template('orders_list.html', pedidos=pedidos)

@bp.route('/pedidos/entregar/<int:order_id>', methods=['POST'])
def entregar_pedido(order_id):
    user = current_user()
    if not user or user.role != 'emprendedor':
        return redirect(url_for('main.login'))
    pedido = Order.query.get(order_id)
    if pedido and pedido.owner_id == user.id and not pedido.entregado:
        pedido.entregado = True
        db.session.commit()
        # cuando se marca entregado, se agrega automáticamente un input de tipo 'ingreso' en finanzas
        # creamos registro en finanzas con la fecha de hoy
        fin = FinanceEntry(tipo='ingreso', fecha=date.today(), monto=pedido.total,
                           descripcion=f"Ingreso por pedido {pedido.id}", owner_id=user.id)
        db.session.add(fin)
        db.session.commit()
        flash('Pedido marcado como entregado y registrado como ingreso')
    return redirect(url_for('main.pedidos'))

# -------------------------
# Finanzas: listar y crear manualmente ingresos/egresos
# -------------------------
@bp.route('/finanzas', methods=['GET', 'POST'])
def finanzas():
    user = current_user()
    if not user or user.role != 'emprendedor':
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        tipo = request.form.get('tipo')  # 'ingreso' o 'egreso'
        fecha_str = request.form.get('fecha')
        monto = float(request.form.get('monto') or 0)
        descripcion = request.form.get('descripcion')
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else date.today()
        fin = FinanceEntry(tipo=tipo, fecha=fecha, monto=monto, descripcion=descripcion, owner_id=user.id)
        db.session.add(fin)
        db.session.commit()
        flash('Entrada financiera registrada')
        return redirect(url_for('main.finanzas'))

    ingresos = FinanceEntry.query.filter_by(owner_id=user.id, tipo='ingreso').order_by(FinanceEntry.fecha.desc()).all()
    egresos = FinanceEntry.query.filter_by(owner_id=user.id, tipo='egreso').order_by(FinanceEntry.fecha.desc()).all()
    return render_template('finance.html', ingresos=ingresos, egresos=egresos)
