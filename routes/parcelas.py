from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Aluno, Parcela
from datetime import datetime, date
from sqlalchemy import or_

parcelas_bp = Blueprint('parcelas', __name__)


@parcelas_bp.route('/gestao_parcelas')
def gestao_parcelas():
    if 'usuario_logado' not in session:
        return redirect(url_for('auth.login'))
    if session.get('role') == 'instrutor':
        return redirect(url_for('treinamento.treinamento'))

    search = request.args.get('search', '').strip()
    status_filtro = request.args.get('status', '').strip()
    hoje = date.today()

    query = Aluno.query.filter(Aluno.forma_pagamento == 'parcelado')

    if search:
        search_cpf = ''.join(filter(str.isdigit, search))
        filtros = [Aluno.nome.ilike(f'%{search}%')]
        if search_cpf:
            filtros.append(Aluno.cpf.like(f'%{search_cpf}%'))
        query = query.filter(or_(*filtros))

    alunos_parcelados = query.all()

    if status_filtro == 'atrasado':
        alunos_parcelados = [
            a for a in alunos_parcelados
            if any(not p.paga and p.data_vencimento < hoje for p in a.parcelas)
        ]

    total_pendente = sum(
        p.valor for p in Parcela.query.filter_by(paga=False).all() if p.valor
    )

    return render_template(
        'gestao_parcelas.html',
        alunos=alunos_parcelados,
        total_geral=total_pendente,
        hoje=hoje,
        search=search,
        status_filtro=status_filtro
    )


@parcelas_bp.route('/baixar_parcela/<int:id>')
def baixar_parcela(id):
    if 'usuario_logado' not in session:
        return redirect(url_for('auth.login'))
    if session.get('role') == 'instrutor':
        return redirect(url_for('treinamento.treinamento'))

    parcela = Parcela.query.get_or_404(id)
    parcela.paga = True
    parcela.data_pagamento = datetime.now().date()
    db.session.commit()
    flash(f"Pagamento da {parcela.numero_parcela}ª parcela de {parcela.aluno.nome} registrado!", "success")
    return redirect(url_for('parcelas.gestao_parcelas'))