from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Aluno, Parcela
from datetime import datetime, date
from sqlalchemy import func, extract

financeiro_bp = Blueprint('financeiro', __name__)


@financeiro_bp.route('/financeiro')
def financeiro():
    if 'usuario_logado' not in session:
        return redirect(url_for('auth.login'))
    if session.get('role') == 'instrutor':
        flash("Acesso negado ao Financeiro.", "danger")
        return redirect(url_for('treinamento.treinamento'))

    mes = request.args.get('mes', datetime.now().month, type=int)
    ano = request.args.get('ano', datetime.now().year, type=int)

    query_base = Aluno.query.filter(
        extract('month', Aluno.data_inscricao) == mes,
        extract('year', Aluno.data_inscricao) == ano
    )
    alunos_novos = query_base.all()

    parcelas_pagas_no_mes = Parcela.query.filter(
        Parcela.paga == True,
        extract('month', Parcela.data_pagamento) == mes,
        extract('year', Parcela.data_pagamento) == ano
    ).all()

    valor_parcelas_pagas = sum(p.valor for p in parcelas_pagas_no_mes if p.valor)
    qtd_parcelas_pagas = len(parcelas_pagas_no_mes)

    total_pendente = db.session.query(func.sum(Parcela.valor)).filter(
        Parcela.paga == False,
        extract('month', Parcela.data_vencimento) == mes,
        extract('year', Parcela.data_vencimento) == ano
    ).scalar() or 0.0

    soma_ae = soma_detran = 0
    for aluno in alunos_novos:
        valor_inicial = aluno.valor_total if aluno.forma_pagamento == 'a_vista' else (aluno.valor_entrada or 0)
        if aluno.origem == 'Auto Escola':
            soma_ae += valor_inicial
        else:
            soma_detran += valor_inicial

    soma_ae += valor_parcelas_pagas
    total_geral = soma_ae + soma_detran

    return render_template(
        'financeiro.html',
        total_geral=total_geral,
        total_pendente=total_pendente,
        soma_ae=soma_ae,
        soma_detran=soma_detran,
        qtd_parcelas_pagas=qtd_parcelas_pagas,
        valor_parcelas_pagas=valor_parcelas_pagas,
        hab_a=query_base.filter(Aluno.tipo_processo == '1ª Habilitação', Aluno.categoria == 'A').count(),
        hab_b=query_base.filter(Aluno.tipo_processo == '1ª Habilitação', Aluno.categoria == 'B').count(),
        hab_ab=query_base.filter(Aluno.tipo_processo == '1ª Habilitação', Aluno.categoria == 'AB').count(),
        inc_a=query_base.filter(Aluno.tipo_processo == 'Inclusão', Aluno.categoria == 'A').count(),
        inc_b=query_base.filter(Aluno.tipo_processo == 'Inclusão', Aluno.categoria == 'B').count(),
        mud_c=query_base.filter(Aluno.tipo_processo == 'Mudança de Categoria', Aluno.categoria == 'C').count(),
        mud_d=query_base.filter(Aluno.tipo_processo == 'Mudança de Categoria', Aluno.categoria == 'D').count(),
        mud_e=query_base.filter(Aluno.tipo_processo == 'Mudança de Categoria', Aluno.categoria == 'E').count(),
        total_alunos=len(alunos_novos),
        mes_atual=mes,
        ano_atual=ano
    )


@financeiro_bp.route('/relatorio_mensal')
def relatorio_mensal():
    if 'usuario_logado' not in session:
        return redirect(url_for('auth.login'))
    if session.get('role') == 'instrutor':
        flash("Acesso negado ao Relatório.", "danger")
        return redirect(url_for('treinamento.treinamento'))

    mes = int(request.args.get('mes', date.today().month))
    ano = int(request.args.get('ano', date.today().year))

    alunos_novos = Aluno.query.filter(
        extract('month', Aluno.data_inscricao) == mes,
        extract('year', Aluno.data_inscricao) == ano
    ).all()

    parcelas_pagas_no_mes = Parcela.query.filter(
        Parcela.paga == True,
        extract('month', Parcela.data_pagamento) == mes,
        extract('year', Parcela.data_pagamento) == ano
    ).all()

    ids_com_parcela = [p.aluno_id for p in parcelas_pagas_no_mes]
    alunos_com_pagamento = Aluno.query.filter(Aluno.id.in_(ids_com_parcela)).all() if ids_com_parcela else []

    todos = list({a.id: a for a in (alunos_novos + alunos_com_pagamento)}.values())

    lista_final = []
    soma_entradas_mes = valor_parcelas_pagas = 0

    for aluno in todos:
        valor_inicial = 0
        if aluno.data_inscricao and aluno.data_inscricao.month == mes and aluno.data_inscricao.year == ano:
            valor_inicial = aluno.valor_total if aluno.forma_pagamento == 'a_vista' else (aluno.valor_entrada or 0)
            soma_entradas_mes += valor_inicial

        total_parcelas = sum(
            p.valor for p in aluno.parcelas
            if p.paga and p.data_pagamento and p.data_pagamento.month == mes and p.data_pagamento.year == ano
        )
        valor_parcelas_pagas += total_parcelas

        lista_final.append({
            'obj': aluno,
            'valor_inicial': valor_inicial,
            'eh_a_vista': aluno.forma_pagamento == 'a_vista'
        })

    def conta(tipo=None, cat=None, origem=None):
        return len([
            a for a in alunos_novos
            if (not tipo or (a.tipo_processo or '').strip().upper() == tipo.upper())
            and (not cat or (a.categoria or '').strip().upper() == cat.upper())
            and (not origem or (a.origem or '').strip().upper() == origem.upper())
        ])

    return render_template(
        'relatorio_mensal.html',
        alunos=lista_final,
        mes_atual=mes,
        ano_atual=ano,
        soma_entradas_mes=soma_entradas_mes,
        valor_parcelas_pagas=valor_parcelas_pagas,
        total_alunos_periodo=len(alunos_novos),
        qtd_primeira_hab=conta(tipo='1ª habilitação'),
        qtd_mudanca_cat=conta(tipo='mudança de categoria'),
        qtd_inclusao=conta(tipo='inclusão'),
        qtd_vindos_cfc=conta(origem='auto escola'),
        qtd_vindos_detran=conta(origem='detran'),
    )