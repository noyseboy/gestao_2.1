from flask import Flask
from models import db, Usuario
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'gestao_cfc_secret')

# --- Banco de Dados ---
database_url = os.getenv('DATABASE_URL')
if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cfc_local.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# --- Blueprints ---
from routes.auth import auth_bp
from routes.alunos import alunos_bp
from routes.financeiro import financeiro_bp
from routes.treinamento import treinamento_bp
from routes.parcelas import parcelas_bp

app.register_blueprint(auth_bp)
app.register_blueprint(alunos_bp)
app.register_blueprint(financeiro_bp)
app.register_blueprint(treinamento_bp)
app.register_blueprint(parcelas_bp)

# --- Context Processor global ---
@app.context_processor
def utility_functions():
    def formatar_moeda(valor):
        if not valor:
            return "0,00"
        return "{:,.2f}".format(float(valor)).replace(',', 'X').replace('.', ',').replace('X', '.')
    return dict(formatar_moeda=formatar_moeda)

# --- Inicialização ---
with app.app_context():
    db.create_all()
    if not Usuario.query.filter_by(username='talita').first():
        db.session.add(Usuario(username='talita', password='jade1234', role='admin'))
    if not Usuario.query.filter_by(username='instrutor').first():
        db.session.add(Usuario(username='instrutor', password='anchieta26', role='instrutor'))
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)