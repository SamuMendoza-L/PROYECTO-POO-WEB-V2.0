from app import db
from datetime import datetime

# ROLE: 'emprendedor' o 'cliente'
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # id_emprendedor para emprendedor (10 dígitos string), puede ser null para clientes
    id_emprendedor = db.Column(db.String(10), unique=True, nullable=True)
    nombre = db.Column(db.String(120), nullable=False)
    apellido = db.Column(db.String(120), nullable=False)
    carrera = db.Column(db.String(120), nullable=True)
    correo = db.Column(db.String(150), unique=True, nullable=False)
    telefono = db.Column(db.String(30), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'emprendedor' o 'cliente'
    nombre_emprendimiento = db.Column(db.String(200), nullable=True)  # solo emprendedor

    def __repr__(self):
        return f"<User {self.correo} ({self.role})>"

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(5), unique=True, nullable=False)  # id de 5 dígitos
    nombre = db.Column(db.String(200), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    cantidad = db.Column(db.Integer, default=0)
    imagen_filename = db.Column(db.String(300), nullable=True)
    # relacion al emprendedor dueño del producto
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    owner = db.relationship('User', backref='productos')

    def __repr__(self):
        return f"<Product {self.nombre} ({self.codigo})>"

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_nombre = db.Column(db.String(200), nullable=False)
    cliente_contacto = db.Column(db.String(50), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    lugar_retiro = db.Column(db.String(200), nullable=True)
    comentarios = db.Column(db.Text, nullable=True)
    metodo_pago = db.Column(db.String(50), nullable=False)  # 'efectivo' o 'transferencia'
    entregado = db.Column(db.Boolean, default=False)
    # relacion con emprendedor (quién recibe el pedido)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    owner = db.relationship('User', backref='pedidos')

    def __repr__(self):
        return f"<Order {self.id} - {self.cliente_nombre}>"

class FinanceEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False)  # 'ingreso' o 'egreso'
    fecha = db.Column(db.Date, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    owner = db.relationship('User', backref='finanzas')

    def __repr__(self):
        return f"<Finance {self.tipo} {self.monto}>"
