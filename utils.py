import random
from app import db
from models import User, Product

def generate_numeric_code(length=5):
    """Genera un string numérico aleatorio de longitud length"""
    return ''.join(random.choices('0123456789', k=length))

def generate_unique_id_for_user(length=10):
    # genera id único para emprendedor
    while True:
        code = generate_numeric_code(length)
        exists = User.query.filter_by(id_emprendedor=code).first()
        if not exists:
            return code

def generate_unique_product_code(length=5):
    while True:
        code = generate_numeric_code(length)
        exists = Product.query.filter_by(codigo=code).first()
        if not exists:
            return code
