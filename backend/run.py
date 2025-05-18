from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from functools import wraps
from firebase_admin import auth as firebase_auth, exceptions as firebase_exceptions
import firebase_admin
from firebase_config import auth_pyrebase # seu pyrebase config

app = Flask(__name__)
CORS(app)

# Config DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Se quiser resetar o banco toda vez (útil para testes)
if os.path.exists("database.db"):
    os.remove("database.db")

# Modelos

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    transacoes = db.relationship('Transacao', backref='user', lazy=True)
    orcamentos = db.relationship('Orcamento', backref='user', lazy=True)

class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    transacoes = db.relationship('Transacao', backref='categoria', lazy=True)
    orcamentos = db.relationship('Orcamento', backref='categoria', lazy=True)

class Transacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(255), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # receita ou despesa
    data = db.Column(db.DateTime, nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Orcamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Float, nullable=False)
    mes_ano = db.Column(db.String(7), nullable=False)  # "YYYY-MM"
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)

# Decorator para validar token Firebase no header Authorization
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # O token geralmente vem no header: Authorization: Bearer <token>
        auth_header = request.headers.get('Authorization')
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
        
        if not token:
            return jsonify({'message': 'Token não fornecido'}), 401

        try:
            decoded_token = firebase_auth.verify_id_token(token)
            request.user = decoded_token  # uid em decoded_token['uid']
        except firebase_exceptions.FirebaseError:
            return jsonify({'message': 'Token inválido'}), 401

        return f(*args, **kwargs)
    return decorated

# Rotas

@app.route('/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        username = data.get('username')

        if not email or not password or not username:
            return jsonify({"error": "Email, senha e username são obrigatórios"}), 400

        # Cria usuário no Firebase Authentication
        user = auth_pyrebase.create_user_with_email_and_password(email, password)

        # Cria usuário no banco local
        novo_user = User(email=email, username=username)
        db.session.add(novo_user)
        db.session.commit()

        return jsonify({"message": "Usuário criado com sucesso", "uid": user['localId']}), 201

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 400

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    try:
        user = auth_pyrebase.sign_in_with_email_and_password(email, password)
        id_token = user['idToken']
        return jsonify({"token": id_token}), 200
    except Exception:
        return jsonify({"error": "Credenciais inválidas"}), 401

@app.route('/api/categorias', methods=['GET'])
@token_required
def listar_categorias():
    categorias = Categoria.query.all()
    resultado = [{"id": c.id, "nome": c.nome} for c in categorias]
    return jsonify(resultado), 200

@app.route('/api/categorias', methods=['POST'])
@token_required
def create_categoria():
    data = request.get_json()
    nome = data.get('nome')
    if not nome:
        return jsonify({"error": "Nome da categoria é obrigatório"}), 400

    if Categoria.query.filter_by(nome=nome).first():
        return jsonify({"error": "Categoria já existe"}), 400

    nova_categoria = Categoria(nome=nome)
    db.session.add(nova_categoria)
    db.session.commit()
    return jsonify({"message": "Categoria criada com sucesso!", "id": nova_categoria.id}), 201

@app.route('/api/transacoes', methods=['GET'])
@token_required
def listar_transacoes():
    user_uid = request.user['uid']
    user = User.query.filter_by(email=request.user.get('email')).first()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    transacoes = Transacao.query.filter_by(user_id=user.id).all()
    resultado = []
    for t in transacoes:
        resultado.append({
            "id": t.id,
            "descricao": t.descricao,
            "valor": t.valor,
            "tipo": t.tipo,
            "data": t.data.strftime("%Y-%m-%d"),
            "categoria": t.categoria.nome
        })
    return jsonify(resultado), 200

@app.route('/api/transacoes', methods=['POST'])
@token_required
def create_transacao():
    data = request.get_json()
    descricao = data.get('descricao')
    valor = data.get('valor')
    tipo = data.get('tipo')
    data_str = data.get('data')
    categoria_id = data.get('categoria_id')

    # Busca usuário no DB via e-mail do token
    user = User.query.filter_by(email=request.user.get('email')).first()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    if not descricao or valor is None or not tipo or not data_str or not categoria_id:
        return jsonify({"error": "Todos os campos são obrigatórios"}), 400

    try:
        data_dt = datetime.strptime(data_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Data inválida, use formato YYYY-MM-DD"}), 400

    categoria = Categoria.query.get(categoria_id)
    if not categoria:
        return jsonify({"error": "Categoria não encontrada"}), 404

    transacao = Transacao(
        descricao=descricao,
        valor=valor,
        tipo=tipo,
        data=data_dt,
        user_id=user.id,
        categoria_id=categoria.id
    )
    db.session.add(transacao)
    db.session.commit()

    return jsonify({"message": "Transação criada com sucesso!", "id": transacao.id}), 201

@app.route('/api/orcamentos', methods=['POST'])
@token_required
def create_orcamento():
    data = request.get_json()
    valor = data.get('valor')
    mes_ano = data.get('mes_ano')
    categoria_id = data.get('categoria_id')

    user = User.query.filter_by(email=request.user.get('email')).first()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    if valor is None or not mes_ano or not categoria_id:
        return jsonify({"error": "Todos os campos são obrigatórios"}), 400

    categoria = Categoria.query.get(categoria_id)
    if not categoria:
        return jsonify({"error": "Categoria não encontrada"}), 404

    novo_orcamento = Orcamento(
        valor=valor,
        mes_ano=mes_ano,
        user_id=user.id,
        categoria_id=categoria.id
    )
    db.session.add(novo_orcamento)
    db.session.commit()

    return jsonify({"message": "Orçamento criado com sucesso!", "id": novo_orcamento.id}), 201

@app.route('/api/orcamentos/saldo', methods=['GET'])
@token_required
def verificar_saldo_orcamento():
    mes_ano = request.args.get('mes_ano')
    user = User.query.filter_by(email=request.user.get('email')).first()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    if not mes_ano:
        return jsonify({"error": "Parâmetro mes_ano é obrigatório"}), 400

    orcamentos = Orcamento.query.filter_by(user_id=user.id, mes_ano=mes_ano).all()
    saldo_total = 0
    for orcamento in orcamentos:
        categoria = Categoria.query.get(orcamento.categoria_id)
        transacoes = Transacao.query.filter_by(user_id=user.id, categoria_id=categoria.id).all()
        total_despesas = sum(t.valor for t in transacoes if t.tipo == 'despesa')
        saldo_total += orcamento.valor - total_despesas

    return jsonify({"saldo_total": saldo_total}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
