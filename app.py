import os
import uuid
from datetime import datetime
from functools import wraps
from urllib.parse import urlparse
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from dotenv import load_dotenv

from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from flask_wtf.csrf import CSRFProtect, CSRFError
from PIL import Image, UnidentifiedImageError
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename

from models import db, User, Product

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True, encoding="utf-8-sig")

app = Flask(__name__)
# Atrás do proxy do PythonAnywhere: pega o IP real (rate limit) e o https
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY não configurada.")
csrf = CSRFProtect(app)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)

app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "zaraeh.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Fotos enviadas pelo painel ficam fora de static/img (que é versionada no Git)
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB por upload
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("PRODUCTION") == "1"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
# formato real da imagem (detectado pelo Pillow) -> extensão salva
FORMATOS_IMAGEM = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
Image.MAX_IMAGE_PIXELS = 50_000_000

# Número de WhatsApp da loja (55 = Brasil, 92 = DDD de Manaus), só dígitos.
WHATSAPP_NUMERO = "".join(ch for ch in os.environ.get("WHATSAPP_NUMERO", "") if ch.isdigit())
if not WHATSAPP_NUMERO:
    raise RuntimeError("WHATSAPP_NUMERO não configurado (ex.: 5592999999999).")

# A loja agora é 100% feminina: estas são as seções do catálogo.
# slug -> nome exibido. A ordem aqui é a ordem do menu.
CATEGORIAS = {
    "vestidos": "Vestidos",
    "blusas": "Blusas",
    "saias": "Saias",
    "calcas": "Calças",
    "jeans": "Jeans",
    "alfaiataria": "Alfaiataria",
    "moda-praia": "Moda Praia",
    "calcados": "Calçados",
    "acessorios": "Acessórios",
}


def extensao_permitida(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _pagina_erro(codigo, titulo, mensagem):
    return render_template("erro.html", codigo=codigo, titulo=titulo, mensagem=mensagem), codigo


@app.errorhandler(CSRFError)
def csrf_expirado(error):
    return _pagina_erro(400, "Sessão expirada",
                        "Sua sessão expirou ou o formulário é inválido. Volte, recarregue a página e tente de novo.")


@app.errorhandler(403)
def acesso_proibido(error):
    return _pagina_erro(403, "Acesso proibido", "Você não tem permissão para acessar este recurso.")


@app.errorhandler(404)
def pagina_nao_encontrada(error):
    return _pagina_erro(404, "Página não encontrada", "A página que você procura não existe ou foi movida.")


@app.errorhandler(413)
def arquivo_muito_grande(error):
    return _pagina_erro(413, "Arquivo muito grande",
                        "O arquivo enviado excede o tamanho máximo de 8 MB. Reduza o tamanho e tente novamente.")


@app.errorhandler(429)
def muitas_tentativas(error):
    return _pagina_erro(429, "Muitas tentativas", "Aguarde um minuto antes de tentar novamente.")


@app.errorhandler(500)
def erro_interno(error):
    app.logger.exception("Erro interno do servidor")
    return _pagina_erro(500, "Erro interno do servidor", "Ocorreu um problema inesperado. Tente novamente mais tarde.")


@app.after_request
def cabecalhos_de_seguranca(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return resp


@app.context_processor
def contexto_global():
    return {"ano_atual": datetime.now().year}


@app.template_filter("brl")
def brl(valor):
    """1234.5 -> 'R$ 1.234,50'"""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def nome_categoria(slug):
    """'calcas' -> 'Calças' (usado nos templates, inclusive nas macros importadas)."""
    return CATEGORIAS.get(slug, (slug or "").replace("-", " ").title())


# Global do Jinja: funciona em qualquer template, inclusive em macros importadas
app.jinja_env.globals["nome_categoria"] = nome_categoria
app.jinja_env.globals["categorias"] = CATEGORIAS
app.jinja_env.globals["whatsapp_numero"] = WHATSAPP_NUMERO


db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Entre com sua conta de administrador para continuar."


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_required(view_func):
    """Bloqueia a rota para quem não está logado ou não é administrador."""
    @wraps(view_func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view_func(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------
# Catálogo público
# ---------------------------------------------------------------
@app.route("/")
def index():
    lancamentos = Product.query.filter_by(badge="Novo").order_by(Product.id.desc()).limit(4).all()
    ofertas = Product.query.filter(Product.old_price_cents.isnot(None)).order_by(Product.id.desc()).limit(4).all()
    return render_template("index.html", lancamentos=lancamentos, ofertas=ofertas)


@app.route("/busca")
def busca():
    q = request.args.get("q", "").strip()
    resultados = []
    if q:
        seguro = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{seguro}%"
        resultados = Product.query.filter(
            Product.name.ilike(like, escape="\\") | Product.category.ilike(like, escape="\\")
        ).all()
    return render_template("busca.html", q=q, categoria=None, titulo=f"Resultados para “{q}”" if q else "Busca", resultados=resultados)


@app.route("/produto/<int:product_id>")
def produto(product_id):
    product = Product.query.get_or_404(product_id)
    relacionados = (
        Product.query.filter(Product.category == product.category, Product.id != product.id)
        .limit(4).all()
    )
    return render_template("produto.html", product=product, relacionados=relacionados)


@app.route("/<categoria>")
def categoria(categoria):
    if categoria == "ofertas":
        produtos = Product.query.filter(Product.old_price_cents.isnot(None)).all()
        titulo = "Ofertas"
    elif categoria == "lancamentos":
        produtos = Product.query.filter_by(badge="Novo").order_by(Product.id.desc()).all()
        titulo = "Lançamentos"
    elif categoria in CATEGORIAS:
        produtos = Product.query.filter(Product.category == categoria).order_by(Product.id.desc()).all()
        titulo = CATEGORIAS[categoria]
    else:
        abort(404)
    return render_template("busca.html", q=None, categoria=categoria, titulo=titulo, resultados=produtos)


# ---------------------------------------------------------------
# Páginas institucionais e de ajuda
# ---------------------------------------------------------------
@app.route("/sobre")
def sobre():
    return render_template("sobre.html")


@app.route("/privacidade")
def privacidade():
    return render_template("privacidade.html")


@app.route("/trocas")
def trocas():
    return render_template("trocas.html")


@app.route("/guia-de-medidas")
def guia_medidas():
    return render_template("guia_medidas.html")


# ---------------------------------------------------------------
# Login (só existe login — não há cadastro público)
# ---------------------------------------------------------------
def _url_segura(destino):
    """Aceita só caminhos internos (evita redirecionar para sites externos)."""
    if not destino:
        return None
    partes = urlparse(destino)
    if partes.scheme or partes.netloc or not destino.startswith("/") or destino.startswith("//"):
        return None
    return destino


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin_produtos"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        next_url = _url_segura(request.args.get("next")) or url_for("admin_produtos")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f"Bem-vinda(o) de volta, {user.name}!", "sucesso")
            return redirect(next_url)

        flash("E-mail ou senha inválidos.", "erro")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("index"))


# ---------------------------------------------------------------
# Admin: cadastro de produtos
# ---------------------------------------------------------------
def _ler_form_produto(form):
    """Converte os campos de texto do formulário para os tipos certos."""
    def reais_para_centavos(valor):
        valor = (valor or "").strip().replace(",", ".")
        if not valor:
            return None
        try:
            return int(round(float(valor) * 100))
        except ValueError:
            return None

    def inteiro(valor, padrao):
        try:
            return max(int(valor), 0)
        except (TypeError, ValueError):
            return padrao

    return {
        "name": form.get("name", "").strip(),
        "category": form.get("category", "").strip(),
        "description": form.get("description", "").strip(),
        "price_cents": reais_para_centavos(form.get("price")) or 0,
        "old_price_cents": reais_para_centavos(form.get("old_price")),
        "installments": max(inteiro(form.get("installments"), 1), 1),
        "badge": form.get("badge", "").strip(),
        "stock": inteiro(form.get("stock"), 0),
    }


def _dados_invalidos(dados):
    return (not dados["name"] or dados["category"] not in CATEGORIAS
            or dados["price_cents"] <= 0)


def _remover_foto(produto):
    """Apaga o arquivo enviado pelo painel (nunca mexe nas fotos de static/img)."""
    if produto.image and produto.image.startswith("uploads/"):
        try:
            os.remove(os.path.join(BASE_DIR, "static", produto.image))
        except OSError:
            pass


def _salvar_foto(produto):
    """Salva a foto enviada. Retorna False se o arquivo foi enviado mas é inválido."""
    arquivo = request.files.get("foto")
    if not arquivo or not arquivo.filename:
        return True
    if not extensao_permitida(arquivo.filename):
        return False
    try:
        with Image.open(arquivo.stream) as img:
            formato = img.format
            img.verify()  # confere se o conteúdo é mesmo uma imagem
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError):
        return False
    if formato not in FORMATOS_IMAGEM:
        return False
    arquivo.stream.seek(0)
    # nome único: evita cache do navegador mostrando a foto antiga
    nome_arquivo = f"produto-{produto.id}-{uuid.uuid4().hex[:8]}.{FORMATOS_IMAGEM[formato]}"
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    arquivo.save(os.path.join(app.config["UPLOAD_FOLDER"], nome_arquivo))
    _remover_foto(produto)
    produto.image = f"uploads/{nome_arquivo}"
    return True


MSG_FOTO_INVALIDA = "A foto não foi aceita. Envie um JPG, PNG ou WebP válido de até 8 MB."


@app.route("/admin/produtos")
@admin_required
def admin_produtos():
    produtos = Product.query.order_by(Product.id.desc()).all()
    return render_template("admin_produtos.html", produtos=produtos)


@app.route("/admin/produtos/novo", methods=["GET", "POST"])
@admin_required
def admin_produto_novo():
    if request.method == "POST":
        dados = _ler_form_produto(request.form)

        if _dados_invalidos(dados):
            flash("Preencha nome, escolha uma categoria e informe um preço válido.", "erro")
            return render_template("admin_produto_form.html", produto=None, dados=dados)

        produto = Product(image="placeholder.svg", **dados)
        db.session.add(produto)
        db.session.commit()  # precisa do id antes de nomear o arquivo da foto

        foto_ok = _salvar_foto(produto)
        db.session.commit()

        flash(f'Produto "{produto.name}" cadastrado com sucesso.', "sucesso")
        if not foto_ok:
            flash(MSG_FOTO_INVALIDA, "erro")
        return redirect(url_for("admin_produtos"))

    return render_template("admin_produto_form.html", produto=None, dados=None)


@app.route("/admin/produtos/<int:product_id>/editar", methods=["GET", "POST"])
@admin_required
def admin_produto_editar(product_id):
    produto = Product.query.get_or_404(product_id)

    if request.method == "POST":
        dados = _ler_form_produto(request.form)

        if _dados_invalidos(dados):
            flash("Preencha nome, escolha uma categoria e informe um preço válido.", "erro")
            return render_template("admin_produto_form.html", produto=produto, dados=dados)

        for campo, valor in dados.items():
            setattr(produto, campo, valor)
        foto_ok = _salvar_foto(produto)

        db.session.commit()
        flash(f'Produto "{produto.name}" atualizado.', "sucesso")
        if not foto_ok:
            flash(MSG_FOTO_INVALIDA, "erro")
        return redirect(url_for("admin_produtos"))

    return render_template("admin_produto_form.html", produto=produto, dados=None)


@app.route("/admin/produtos/<int:product_id>/excluir", methods=["POST"])
@admin_required
def admin_produto_excluir(product_id):
    produto = Product.query.get_or_404(product_id)
    nome = produto.name
    _remover_foto(produto)
    db.session.delete(produto)
    db.session.commit()
    flash(f'Produto "{nome}" excluído.', "sucesso")
    return redirect(url_for("admin_produtos"))


# ---------------------------------------------------------------
# Dados de exemplo (só roupas femininas) + conta de administrador
# ---------------------------------------------------------------
def seed_products():
    """Produtos de exemplo: só com SEED_DEMO=1 (não povoa o site em produção)."""
    if os.environ.get("SEED_DEMO") != "1" or Product.query.first():
        return

    produtos = [
        dict(name="Vestido midi plissado", category="vestidos", price_cents=18990,
             installments=6, badge="Novo", image="produto-1.jpg",
             description="Caimento fluido e plissado delicado. Perfeito do trabalho ao jantar."),
        dict(name="Blusa de linho manga longa", category="blusas", price_cents=11990,
             installments=4, badge="Novo", image="produto-2.jpg",
             description="Linho leve e respirável, ideal para o calor de Manaus."),
        dict(name="Saia midi acetinada", category="saias", price_cents=12990,
             installments=3, badge="Novo", image="produto-3.jpg",
             description="Acetinado com brilho suave e cintura confortável."),
        dict(name="Blusa cropped de alças", category="blusas", price_cents=7990,
             installments=2, badge="Novo", image="produto-4.jpg",
             description="Básico versátil para compor looks do dia a dia."),
        dict(name="Jaqueta jeans cropped", category="jeans", price_cents=17990,
             old_price_cents=22990, installments=6, badge="-22%", image="produto-5.jpg",
             description="Jeans estruturado com lavagem clássica."),
        dict(name="Calça wide leg de alfaiataria", category="alfaiataria", price_cents=15990,
             old_price_cents=19990, installments=5, badge="-20%", image="produto-6.jpg",
             description="Corte reto e amplo, tecido com ótimo caimento."),
        dict(name="Sandália salto bloco", category="calcados", price_cents=12990,
             old_price_cents=18990, installments=3, badge="-32%", image="produto-7.jpg",
             description="Salto bloco confortável para o dia inteiro."),
        dict(name="Bolsa tote estruturada", category="acessorios", price_cents=11990,
             old_price_cents=16990, installments=4, badge="-29%", image="produto-8.jpg",
             description="Espaçosa, estruturada e com acabamento dourado."),
    ]

    for p in produtos:
        db.session.add(Product(**p))
    db.session.commit()


def seed_admin():
    """Cria a conta de administrador se ainda não existir nenhuma."""
    if User.query.filter_by(is_admin=True).first():
        return

    email = (os.environ.get("ADMIN_EMAIL") or "").strip().lower()  # login compara em minúsculas
    if not email:
        raise RuntimeError("ADMIN_EMAIL não configurado.")
    senha = os.environ.get("ADMIN_PASSWORD")
    if not senha:
        raise RuntimeError("ADMIN_PASSWORD não configurada.")

    admin = User(name="Administrador", email=email, is_admin=True)
    admin.set_password(senha)
    db.session.add(admin)
    db.session.commit()

    print("=" * 60)
    print(" Conta de administrador criada:")
    print(f"   E-mail: {email}")
    print(" Troque a senha o quanto antes.")
    print("=" * 60)


with app.app_context():
    db.create_all()
    seed_products()
    seed_admin()


if __name__ == "__main__":
    debug = os.environ.get("DEBUG") == "1"
    app.run(debug=debug)