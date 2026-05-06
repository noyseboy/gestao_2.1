from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Aluno, Presenca, GradeHorario
from datetime import datetime

treinamento_bp = Blueprint('treinamento', __name__)


@treinamento_bp.route('/treinamento')
def treinamento():
    if 'usuario_logado' not in session:
        return redirect(url_for('auth.login'))

    hoje = datetime.now().date()
    grade_fixa = GradeHorario.query.all()
    mapa_ocupacao = {f"{g.horario}-{g.veiculo}": g.aluno_id for g in grade_fixa}
    presencas_hoje = Presenca.query.filter_by(data_aula=hoje).all()
    todos_ativos = Aluno.query.filter_by(concluido=False).order_by(Aluno.nome).all()

    return render_template(
        'treinamento.html',
        alunos=todos_ativos,
        mapa=mapa_ocupacao,
        total_em_aula=len(presencas_hoje),
        now_date=hoje.strftime('%Y-%m-%d')
    )


@treinamento_bp.route('/salvar_treinamento', methods=['POST'])
def salvar_treinamento():
    if 'usuario_logado' not in session:
        return redirect(url_for('auth.login'))

    aluno_id = request.form.get('aluno_id')
    data_str = request.form.get('data_aula')
    horario = request.form.get('horario')
    veiculo = request.form.get('veiculo')
    aulas_marcadas = request.form.getlist('aulas_marcadas')

    try:
        aluno = Aluno.query.get(aluno_id)
        data_aula = datetime.strptime(data_str, '%Y-%m-%d').date()
        salvas = 0

        for numero_aula in aulas_marcadas:
            existe = Presenca.query.filter_by(
                aluno_id=aluno.id, data_aula=data_aula,
                horario_aula=horario, veiculo=veiculo, numero_aula=numero_aula
            ).first()
            if not existe:
                db.session.add(Presenca(
                    aluno_id=aluno.id, data_aula=data_aula,
                    horario_aula=horario, veiculo=veiculo, numero_aula=numero_aula
                ))
                salvas += 1

        if salvas > 0:
            aluno.em_treinamento = True
            db.session.commit()
            flash(f"{salvas} aula(s) registrada(s)!", "success")
        else:
            flash("Aula já registrada.", "info")

    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao salvar: {e}", "danger")

    return redirect(url_for('treinamento.treinamento'))


@treinamento_bp.route('/fixar_aluno_grade', methods=['POST'])
def fixar_aluno_grade():
    aluno_id = request.form.get('aluno_id')
    horario = request.form.get('horario')
    veiculo = request.form.get('veiculo')

    if not aluno_id:
        existente = GradeHorario.query.filter_by(horario=horario, veiculo=veiculo).first()
        if existente:
            db.session.delete(existente)
            db.session.commit()
        return redirect(url_for('treinamento.treinamento'))

    try:
        existente = GradeHorario.query.filter_by(horario=horario, veiculo=veiculo).first()
        if existente:
            existente.aluno_id = aluno_id
        else:
            db.session.add(GradeHorario(aluno_id=aluno_id, horario=horario, veiculo=veiculo))
        db.session.commit()
        flash("Grade atualizada!", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao fixar aluno.", "danger")

    return redirect(url_for('treinamento.treinamento'))


@treinamento_bp.route('/liberar_horario/<horario>/<veiculo>')
def liberar_horario(horario, veiculo):
    reserva = GradeHorario.query.filter_by(horario=horario, veiculo=veiculo).first()
    if reserva:
        db.session.delete(reserva)
        db.session.commit()
        flash("Horário liberado.", "info")
    return redirect(url_for('treinamento.treinamento'))