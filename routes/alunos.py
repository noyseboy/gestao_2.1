from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, Aluno, Presenca, GradeHorario, Parcela, criar_parcelas_automaticas
from utils import moeda_para_float
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError

alunos_bp = Blueprint('alunos', __name__)


@alunos_bp.route('/dashboard')
def dashboard():
    if 'usuario_logado' not in session:
        return redirect(url_for('auth.login'))
    if session.get('role') == 'instrutor':
        flash("Acesso restrito: Instrutores só podem acessar a Grade de Treinamento.", "warning")
        return redirect(url_for('treinamento.treinamento'))

    alunos = Aluno.query.filter_by(concluido=False).order_by(
        Aluno.em_treinamento.desc(),
        Aluno.data_prova.is_(None),
        Aluno.data_prova.asc()
    ).all()

    total_geral = sum(a.valor_total or 0 for a in alunos)

    # — Parcelas em atraso
    hoje = date.today()
    parcelas_atrasadas = Parcela.query.filter(
        Parcela.paga == False,
        Parcela.data_vencimento < hoje
    ).all()

    alunos_inadimplentes = len(set(p.aluno_id for p in parcelas_atrasadas))
    valor_total_atraso  = sum(p.valor or 0 for p in parcelas_atrasadas)

    return render_template(
        'dashboard.html',
        alunos=alunos,
        total_geral=total_geral,
        now_date=datetime.now().strftime('%Y-%m-%d'),
        alunos_inadimplentes=alunos_inadimplentes,
        valor_total_atraso=valor_total_atraso
    )


@alunos_bp.route('/historico')
def historico():
    if 'usuario_logado' not in session:
        return redirect(url_for('auth.login'))
    if session.get('role') == 'instrutor':
        return redirect(url_for('treinamento.treinamento'))

    busca = request.args.get('q', '').strip()
    query = Aluno.query.filter_by(concluido=True)

    if busca:
        query = query.filter(db.or_(
            Aluno.nome.ilike(f'%{busca}%'),
            Aluno.cpf.ilike(f'%{busca}%'),
            Aluno.categoria.ilike(f'%{busca}%'),
            Aluno.tipo_processo.ilike(f'%{busca}%')
        ))

    alunos = query.order_by(Aluno.nome).all()
    return render_template('historico.html', alunos=alunos, busca=busca)


@alunos_bp.route('/cadastrar_aluno', methods=['POST'])
def cadastrar_aluno():
    if session.get('role') == 'instrutor':
        return redirect(url_for('treinamento.treinamento'))

    try:
        forma_pagamento = str(request.form.get('forma_pagamento') or '').strip().lower()
        qtd_parcelas = int(request.form.get('qtd_parcelas') or 1)

        data_p = request.form.get('data_prova')
        data_i = request.form.get('data_inscricao')

        novo = Aluno(
            nome=request.form.get('nome'),
            cpf=request.form.get('cpf'),
            contato=request.form.get('contato'),
            tipo_processo=request.form.get('tipo_processo') or '1ª Habilitação',
            categoria=request.form.get('categoria'),
            origem=request.form.get('origem'),
            observacoes=request.form.get('observacoes'),
            horas_a=int(request.form.get('horas_a') or 0),
            horas_b=int(request.form.get('horas_b') or 0),
            valor_total=moeda_para_float(request.form.get('valor')),
            valor_entrada=moeda_para_float(request.form.get('valor_entrada')),
            forma_pagamento=forma_pagamento,
            qtd_parcelas=qtd_parcelas,
            data_prova=datetime.strptime(data_p, '%Y-%m-%d').date() if data_p else None,
            data_inscricao=datetime.strptime(data_i, '%Y-%m-%d').date() if data_i else datetime.now().date(),
            concluido=False,
            em_treinamento=False
        )

        db.session.add(novo)
        db.session.flush()

        if forma_pagamento == 'parcelado':
            criar_parcelas_automaticas(novo)

        db.session.commit()
        flash("Aluno cadastrado com sucesso!", "success")

    except IntegrityError:
        db.session.rollback()
        flash("Aluno já cadastrado. Verifique o CPF.", "danger")
    except Exception as e:
        db.session.rollback()
        print(f"ERRO NO CADASTRO: {type(e).__name__} - {e}")
        flash("Erro ao cadastrar aluno.", "danger")

    return redirect(url_for('alunos.dashboard'))


@alunos_bp.route('/editar_aluno/<int:id>', methods=['POST'])
def editar_aluno(id):
    if session.get('role') == 'instrutor':
        return redirect(url_for('treinamento.treinamento'))

    aluno = Aluno.query.get_or_404(id)
    try:
        aluno.nome = request.form.get('nome')
        aluno.cpf = request.form.get('cpf')
        aluno.contato = request.form.get('contato')
        aluno.tipo_processo = request.form.get('tipo_processo') or '1ª Habilitação'
        aluno.categoria = request.form.get('categoria')
        aluno.origem = request.form.get('origem')
        aluno.observacoes = request.form.get('observacoes')

        horas_a = int(request.form.get('horas_a') or 0)
        horas_b = int(request.form.get('horas_b') or 0)

        if aluno.tipo_processo == 'Mudança de Categoria':
            horas_a = horas_b = 0
        elif aluno.tipo_processo == 'Inclusão':
            if aluno.categoria == 'A':
                horas_b = 0
            elif aluno.categoria == 'B':
                horas_a = 0

        aluno.horas_a = horas_a
        aluno.horas_b = horas_b

        valor_raw = request.form.get('valor')
        if valor_raw:
            aluno.valor_total = float(valor_raw.replace('.', '').replace(',', '.'))

        dt_p = request.form.get('data_prova')
        aluno.data_prova = datetime.strptime(dt_p, '%Y-%m-%d').date() if dt_p else None

        dt_i = request.form.get('data_inscricao')
        if dt_i:
            aluno.data_inscricao = datetime.strptime(dt_i, '%Y-%m-%d').date()

        db.session.commit()
        flash("Cadastro atualizado com sucesso!", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao atualizar os dados.", "danger")

    return redirect(url_for('alunos.dashboard'))


@alunos_bp.route('/concluir_aluno/<int:id>', methods=['POST'])
def concluir_aluno(id):
    if session.get('role') == 'instrutor':
        return redirect(url_for('treinamento.treinamento'))

    aluno = Aluno.query.get_or_404(id)
    aluno.concluido = True
    aluno.em_treinamento = False
    aluno.data_conclusao = datetime.now().date()
    db.session.commit()
    flash(f"Processo de {aluno.nome} finalizado!", "success")
    return redirect(url_for('alunos.dashboard'))


@alunos_bp.route('/excluir_aluno/<int:id>', methods=['POST'])
def excluir_aluno(id):
    if session.get('role') == 'instrutor':
        return redirect(url_for('treinamento.treinamento'))

    aluno = Aluno.query.get_or_404(id)
    try:
        GradeHorario.query.filter_by(aluno_id=aluno.id).delete()
        Presenca.query.filter_by(aluno_id=aluno.id).delete()
        db.session.delete(aluno)
        db.session.commit()
        flash(f"Aluno {aluno.nome} removido permanentemente!", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir: {str(e)}", "danger")

    return redirect(url_for('alunos.dashboard'))


@alunos_bp.route('/treinamento_aluno/<int:id>', methods=['POST'])
def treinamento_aluno(id):
    if 'usuario_logado' not in session:
        return redirect(url_for('auth.login'))
    if session.get('role') == 'instrutor':
        return redirect(url_for('treinamento.treinamento'))

    aluno = Aluno.query.get_or_404(id)
    aluno.em_treinamento = not aluno.em_treinamento
    db.session.commit()
    return redirect(url_for('alunos.dashboard'))


@alunos_bp.route('/historico/reabrir/<int:aluno_id>', methods=['POST'])
def reabrir_aluno(aluno_id):
    if 'usuario_logado' not in session or session.get('role') == 'instrutor':
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.login'))

    try:
        aluno = Aluno.query.get_or_404(aluno_id)
        if not aluno.concluido:
            flash('Este aluno já está ativo.', 'warning')
            return redirect(url_for('alunos.historico'))

        aluno.concluido = False
        aluno.data_conclusao = None
        aluno.em_treinamento = False
        db.session.commit()
        flash(f'Aluno "{aluno.nome}" reaberto com sucesso!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Erro ao reabrir aluno.', 'error')
    except Exception:
        db.session.rollback()
        flash('Erro inesperado.', 'error')

    q = request.args.get('q')
    return redirect(url_for('alunos.historico', q=q) if q else url_for('alunos.historico'))


@alunos_bp.route('/aluno/<int:id>')
def perfil_aluno(id):
    if 'usuario_logado' not in session:
        return redirect(url_for('auth.login'))
    if session.get('role') == 'instrutor':
        return redirect(url_for('treinamento.treinamento'))

    aluno = Aluno.query.get_or_404(id)
    parcelas = aluno.parcelas.order_by(Parcela.numero_parcela).all()
    aulas = aluno.aulas.order_by(Presenca.data_aula.desc(), Presenca.horario_aula).all()

    hoje = date.today()

    if aluno.forma_pagamento == 'a_vista':
        # Pagamento à vista: valor já foi pago integralmente na inscrição
        total_pago     = aluno.valor_total or 0
        total_pendente = 0.0
        total_atrasado = 0.0
    else:
        total_pago     = sum(p.valor or 0 for p in parcelas if p.paga)
        total_pendente = sum(p.valor or 0 for p in parcelas if not p.paga)
        total_atrasado = sum(p.valor or 0 for p in parcelas
                            if not p.paga and p.data_vencimento and p.data_vencimento < hoje)

    progresso_a = 0
    if aluno.horas_a:
        progresso_a = round((aluno.aulas_a_realizadas / aluno.horas_a) * 100)

    progresso_b = 0
    if aluno.horas_b:
        progresso_b = round((aluno.aulas_b_realizadas / aluno.horas_b) * 100)

    return render_template(
        'perfil_aluno.html',
        aluno=aluno,
        parcelas=parcelas,
        aulas=aulas,
        total_pago=total_pago,
        total_pendente=total_pendente,
        total_atrasado=total_atrasado,
        progresso_a=progresso_a,
        progresso_b=progresso_b,
        today=hoje
    )


@alunos_bp.route('/buscar')
def buscar():
    if 'usuario_logado' not in session:
        return redirect(url_for('auth.login'))
    if session.get('role') == 'instrutor':
        return redirect(url_for('treinamento.treinamento'))

    q = request.args.get('q', '').strip()
    resultados = []

    if q:
        filtro = db.or_(
            Aluno.nome.ilike(f'%{q}%'),
            Aluno.cpf.ilike(f'%{q}%')
        )
        resultados = Aluno.query.filter(filtro).order_by(
            Aluno.concluido.asc(),
            Aluno.nome.asc()
        ).limit(50).all()

    # Suporte a AJAX (retorna JSON)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = [{
            'id': a.id,
            'nome': a.nome,
            'cpf': a.cpf,
            'categoria': a.categoria,
            'tipo_processo': a.tipo_processo or '1ª Habilitação',
            'origem': a.origem or 'Auto Escola',
            'concluido': a.concluido,
            'em_treinamento': a.em_treinamento,
            'data_prova': a.data_prova.strftime('%d/%m/%Y') if a.data_prova else None,
            'url': url_for('alunos.perfil_aluno', id=a.id)
        } for a in resultados]
        return jsonify(data)

    return render_template('buscar.html', resultados=resultados, q=q)