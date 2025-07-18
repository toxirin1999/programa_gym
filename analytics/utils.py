def parse_reps(valor, default_series=1, default_reps=1):
    """
    Parsea un string como '3x8', '4×12' o '2 x 10' y devuelve (series, reps)
    """
    try:
        texto = str(valor).lower().replace('×', 'x').replace(' ', '')
        partes = texto.split('x')
        series = int(partes[0]) if len(partes) > 0 and partes[0].isdigit() else default_series
        reps = int(partes[1]) if len(partes) > 1 and partes[1].isdigit() else default_reps
        return series, reps
    except:
        return default_series, default_reps
