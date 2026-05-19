function preencherCategorias(selectElement, tipoProcesso, valorSelecionado = null) {
    let opcoes = [];
    if (tipoProcesso === '1ª Habilitação') opcoes = ['A', 'B', 'AB'];
    else if (tipoProcesso === 'Mudança de Categoria') opcoes = ['C', 'D', 'E'];
    else if (tipoProcesso === 'Inclusão') opcoes = ['A', 'B'];

    selectElement.innerHTML = '';
    opcoes.forEach(function (opcao) {
        const option = document.createElement('option');
        option.value = opcao;
        option.textContent = opcao;
        if (valorSelecionado === opcao) option.selected = true;
        selectElement.appendChild(option);
    });
    if ((!valorSelecionado || !opcoes.includes(valorSelecionado)) && opcoes.length > 0)
        selectElement.value = opcoes[0];
}

function toggleHorasNovo() {
    const tipo = $('#select_tipo_processo').val();
    const cat = $('#select_categoria').val();
    if (tipo === 'Mudança de Categoria') {
        $('#grupo_horas_a, #grupo_horas_b').hide();
        $('#horas_a_novo, #horas_b_novo').val(0);
        return;
    }
    if (tipo === 'Inclusão') {
        $('#grupo_horas_a').toggle(cat === 'A');
        $('#grupo_horas_b').toggle(cat === 'B');
        if (cat === 'A') $('#horas_b_novo').val(0);
        else if (cat === 'B') $('#horas_a_novo').val(0);
        return;
    }
    $('#grupo_horas_a').toggle(cat === 'A' || cat === 'AB');
    $('#grupo_horas_b').toggle(cat === 'B' || cat === 'AB');
    if (cat === 'A') $('#horas_b_novo').val(0);
    else if (cat === 'B') $('#horas_a_novo').val(0);
}

function atualizarFormularioNovo() {
    preencherCategorias(document.getElementById('select_categoria'), document.getElementById('select_tipo_processo').value);
    toggleHorasNovo();
}

function atualizarVisibilidadeHorasEdicao(alunoId) {
    const tipo = document.querySelector(`.tipo-processo-edit[data-aluno-id="${alunoId}"]`).value;
    const sel = document.getElementById(`categoria_edit_${alunoId}`);
    const cat = sel.value;
    const grupoA = document.getElementById(`grupo_horas_a_edit_${alunoId}`);
    const grupoB = document.getElementById(`grupo_horas_b_edit_${alunoId}`);
    const inputA = document.getElementById(`horas_a_edit_${alunoId}`);
    const inputB = document.getElementById(`horas_b_edit_${alunoId}`);

    if (tipo === 'Mudança de Categoria') {
        grupoA.style.display = grupoB.style.display = 'none';
        inputA.value = inputB.value = 0;
        return;
    }
    if (tipo === 'Inclusão') {
        grupoA.style.display = cat === 'A' ? 'block' : 'none';
        grupoB.style.display = cat === 'B' ? 'block' : 'none';
        if (cat === 'A') inputB.value = 0;
        else if (cat === 'B') inputA.value = 0;
        return;
    }
    if (cat === 'A') { grupoA.style.display = 'block'; grupoB.style.display = 'none'; inputB.value = 0; }
    else if (cat === 'B') { grupoA.style.display = 'none'; grupoB.style.display = 'block'; inputA.value = 0; }
    else if (cat === 'AB') { grupoA.style.display = grupoB.style.display = 'block'; }
}

function atualizarFormularioEdicao(alunoId) {
    const tipo = document.querySelector(`.tipo-processo-edit[data-aluno-id="${alunoId}"]`).value;
    const sel = document.getElementById(`categoria_edit_${alunoId}`);
    const valorAtual = sel.getAttribute('data-valor-atual') || sel.value;

    preencherCategorias(sel, tipo, valorAtual);
    if (!Array.from(sel.options).some(o => o.value === valorAtual))
        sel.value = sel.options[0]?.value || '';

    sel.setAttribute('data-valor-atual', sel.value);
    sel.onchange = function () {
        this.setAttribute('data-valor-atual', this.value);
        atualizarVisibilidadeHorasEdicao(alunoId);
    };
    atualizarVisibilidadeHorasEdicao(alunoId);
}

function togglePagamento() {
    const forma = $('#forma_pagamento').val();
    if (forma === 'parcelado') { $('.secao-parcelado').fadeIn(); calcularParcelas(); }
    else { $('.secao-parcelado').fadeOut(); $('#valor_entrada').val('0,00'); $('#qtd_parcelas').val(1); }
}

function calcularParcelas() {
    const total = parseFloat($('#valor_total').val().replace('.', '').replace(',', '.')) || 0;
    const entrada = parseFloat($('#valor_entrada').val().replace('.', '').replace(',', '.')) || 0;
    const qtd = parseInt($('#qtd_parcelas').val()) || 1;

    if (total > 0 && $('#forma_pagamento').val() === 'parcelado') {
        const saldo = total - entrada;
        if (saldo < 0) { $('#resumo_parcelas').html('<span class="text-danger">A entrada não pode ser maior que o total!</span>'); return; }
        $('#resumo_parcelas').html(
            `Saldo a parcelar: <strong>R$ ${saldo.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</strong><br>` +
            `Ficará em: <strong>${qtd}x de R$ ${(saldo / qtd).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</strong>`
        );
    }
}

$(document).ready(function () {
    // Tooltips
    [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
        .map(el => new bootstrap.Tooltip(el));

    // Busca na tabela
    $('#inputBusca').on('keyup', function () {
        const value = $(this).val().toLowerCase();
        $('#tabelaAlunos tbody tr.linha-aluno').filter(function () {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });
    });

    // Máscaras
    function aplicarMascaras() {
        $('.cpf_mask').mask('000.000.000-00');
        $('.fone_mask').mask('(00) 00000-0000');
        $('.money_mask').mask('#.##0,00', { reverse: true });
    }
    aplicarMascaras();
    $('.modal').on('shown.bs.modal', aplicarMascaras);

    // Formulário novo aluno
    atualizarFormularioNovo();

    // Formulários de edição
    document.querySelectorAll('.tipo-processo-edit').forEach(function (select) {
        atualizarFormularioEdicao(select.getAttribute('data-aluno-id'));
    });
    document.querySelectorAll('.categoria-edit').forEach(function (select) {
        select.addEventListener('change', function () {
            const id = this.id.replace('categoria_edit_', '');
            this.setAttribute('data-valor-atual', this.value);
            atualizarVisibilidadeHorasEdicao(id);
        });
    });
    document.querySelectorAll('.modal').forEach(function (modal) {
        modal.addEventListener('shown.bs.modal', function () {
            document.querySelectorAll('.tipo-processo-edit').forEach(s => atualizarFormularioEdicao(s.getAttribute('data-aluno-id')));
            aplicarMascaras();
        });
    });

    // Recalcular parcelas ao digitar
    $(document).on('input', '#valor_total, #valor_entrada, #qtd_parcelas', calcularParcelas);
});