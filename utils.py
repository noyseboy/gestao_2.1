def moeda_para_float(valor):
    """Converte string em moeda BR (ex: 1.500,00) para float (ex: 1500.0)"""
    if not valor:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    try:
        return float(str(valor).replace('.', '').replace(',', '.'))
    except ValueError:
        return 0.0