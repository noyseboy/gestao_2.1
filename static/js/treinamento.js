function gerarControle(select) {
    const card = select.closest('.card-horario');
    const grupoCheckboxes = card.querySelector('.checkbox-group');
    if (!grupoCheckboxes) return;

    const option = select.options[select.selectedIndex];
    const total = parseInt(option.dataset.horas) || 0;
    const realizadas = parseInt(option.dataset.realizadas) || 0;

    grupoCheckboxes.innerHTML = '';

    if (total > 0) {
        for (let i = 1; i <= total; i++) {
            const isDone = i <= realizadas;
            const container = document.createElement('div');
            container.innerHTML = `
                <input type="checkbox" class="form-check-input"
                    ${isDone ? 'checked disabled' : ''}
                    ${isDone ? '' : 'name="aulas_marcadas" value="' + i + '"'}
                    style="width: 15px; height: 15px;">
            `;
            grupoCheckboxes.appendChild(container);
        }
    }
}

function liberarVaga(btn) {
    if (confirm("Liberar este horário?")) {
        const select = btn.closest('.card-horario').querySelector('.aluno-select');
        select.disabled = false;
        select.value = "";
        select.closest('form').submit();
    }
}

window.onload = function () {
    document.querySelectorAll('.aluno-select').forEach(s => {
        if (s.value !== "") gerarControle(s);
    });
};