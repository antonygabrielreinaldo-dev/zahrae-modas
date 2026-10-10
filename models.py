from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, default="")
    price_cents = db.Column(db.Integer, nullable=False)          # preço atual, em centavos
    old_price_cents = db.Column(db.Integer, nullable=True)       # preço "de", se estiver em oferta
    installments = db.Column(db.Integer, default=1)              # nº de parcelas sem juros
    badge = db.Column(db.String(30), default="")                 # "Novo", "-20%" etc.
    image = db.Column(db.String(160), default="placeholder.svg")
    stock = db.Column(db.Integer, default=0)

    @property
    def image_path(self):
        """Caminho relativo a /static. Fotos enviadas pelo admin ficam em uploads/."""
        img = self.image or "placeholder.svg"
        return img if img.startswith("uploads/") else "img/" + img

    @property
    def price(self):
        return self.price_cents / 100

    @property
    def old_price(self):
        return self.old_price_cents / 100 if self.old_price_cents else None

    @property
    def installment_value(self):
        return self.price / self.installments if self.installments else self.price