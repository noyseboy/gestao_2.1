from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

db = SQLAlchemy()


class Aluno(db.Model):
    __tablename__ = 'alunos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False, index=True)
    contato = db.Column(db.String(20))

    tipo_processo = db.Column(db.String(50), default="1ª Habilitação", nullable=False)
    categoria = db.Column(db.String(2), nullable=False)

    horas_a = db.Column(db.Integer, default=0)
    horas_b = db.Column(db.Integer, default=0)

    data_inscricao = db.Column(db.Date, default=date.today)
    data_prova = db.Column(db.Date, nullable=True)
    concluido = db.Column(db.Boolean, default=False)
    data_conclusao = db.Column(db.Date)
    em_treinamento = db.Column(db.Boolean, default=False)
    origem = db.Column(db.String(20), default="Auto Escola")
    observacoes = db.Column(db.Text, nullable=True)

    valor_total = db.Column(db.Float, default=0.0)
    valor_entrada = db.Column(db.Float, default=0.0)
    forma_pagamento = db.Column(db.String(20), default='a_vista')
    qtd_parcelas = db.Column(db.Integer, default=1)

    aulas = db.relationship('Presenca', backref='aluno', lazy='dynamic', cascade="all, delete-orphan")
    parcelas = db.relationship('Parcela', backref='aluno', cascade="all, delete-orphan", lazy='dynamic')

    @property
    def total_pago_nas_parcelas(self):
        return sum(parcela.valor or 0 for parcela in self.parcelas.filter_by(paga=True).all())

    @property
    def saldo_devedor(self):
        if self.forma_pagamento == 'a_vista':
            return 0.0
        return sum(parcela.valor or 0 for parcela in self.parcelas.filter_by(paga=False).all())

    @property
    def aulas_moto_realizadas(self):
        return self.aulas.filter_by(veiculo='MOTO').count()

    @property
    def aulas_carro_realizadas(self):
        return self.aulas.filter(Presenca.veiculo.in_(['GOL', 'KIWD'])).count()

    @property
    def aulas_a_realizadas(self):
        return self.aulas_moto_realizadas

    @property
    def aulas_b_realizadas(self):
        return self.aulas_carro_realizadas

    def __repr__(self):
        return f'<Aluno {self.nome}>'


class Parcela(db.Model):
    __tablename__ = 'parcelas'

    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('alunos.id', ondelete="CASCADE"), nullable=False)
    numero_parcela = db.Column(db.Integer, nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    paga = db.Column(db.Boolean, default=False)
    data_pagamento = db.Column(db.Date, nullable=True)

    @property
    def atrasada(self):
        if self.paga or not self.data_vencimento:
            return False
        return date.today() > self.data_vencimento


class Presenca(db.Model):
    __tablename__ = 'presencas'

    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('alunos.id', ondelete="CASCADE"), nullable=False)
    data_aula = db.Column(db.Date, nullable=False, default=date.today)
    horario_aula = db.Column(db.String(20), nullable=False)
    veiculo = db.Column(db.String(10), nullable=False)
    numero_aula = db.Column(db.Integer, nullable=False)
    data_registro = db.Column(db.DateTime, default=lambda: datetime.utcnow() - timedelta(hours=3))

    __table_args__ = (
        db.UniqueConstraint('aluno_id', 'data_aula', 'horario_aula', 'veiculo', 'numero_aula', name='uq_presenca'),
    )


class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='instrutor')


class GradeHorario(db.Model):
    __tablename__ = 'grade_horarios'

    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('alunos.id'), nullable=False)
    horario = db.Column(db.String(20), nullable=False)
    veiculo = db.Column(db.String(10), nullable=False)

    aluno = db.relationship('Aluno', backref=db.backref('horarios_fixos', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('horario', 'veiculo', name='uq_horario_veiculo'),
    )


def criar_parcelas_automaticas(aluno):
    saldo = (aluno.valor_total or 0) - (aluno.valor_entrada or 0)

    if saldo > 0 and aluno.qtd_parcelas >= 1:
        Parcela.query.filter_by(aluno_id=aluno.id).delete()

        valor_parcela = saldo / aluno.qtd_parcelas
        data_base = aluno.data_inscricao or date.today()

        for i in range(1, aluno.qtd_parcelas + 1):
            try:
                vencimento = data_base + relativedelta(months=i)
            except Exception:
                vencimento = data_base + timedelta(days=30 * i)

            nova_p = Parcela(
                aluno_id=aluno.id,
                numero_parcela=i,
                valor=round(valor_parcela, 2),
                data_vencimento=vencimento,
                paga=False
            )
            db.session.add(nova_p)

        print(f"DEBUG: {aluno.qtd_parcelas} parcelas criadas para {aluno.nome}")