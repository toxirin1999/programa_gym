# Archivo: entrenos/vendor/vendor.py
# VERSIÓN CORREGIDA Y ORGANIZADA

import re


# --- FUNCIONES DE ANÁLISIS BIOMÉTRICO ---

def analizar_entreno_whoop(registro):
    """
    Analiza un registro de datos biométricos (tipo Whoop) y devuelve un consejo
    de entrenamiento y un código de color.
    """
    hrv = registro.hrv
    rhr = registro.rhr
    recovery = registro.recovery
    horas_sueno = registro.horas_sueno.total_seconds() / 3600
    strain = registro.strain

    # Clasificaciones
    if hrv >= 90:
        hrv_estado = "alta"
    elif hrv >= 70:
        hrv_estado = "media"
    else:
        hrv_estado = "baja"

    if rhr <= 55:
        rhr_estado = "bajo"
    elif rhr <= 65:
        rhr_estado = "estable"
    else:
        rhr_estado = "alto"

    # Consejo principal
    if hrv_estado == "alta" and rhr_estado == "bajo" and recovery >= 66:
        consejo = "🟢 Entrenamiento intenso recomendado. Tu cuerpo está preparado para darlo todo."
        color = "green"
    elif hrv_estado == "media" and rhr_estado == "estable":
        consejo = "🟡 Entrenamiento moderado. Puedes rendir bien, pero no exijas al máximo."
        color = "yellow"
    elif hrv_estado == "baja" and rhr_estado == "alto":
        consejo = "🔴 Señales de fatiga o estrés. Mejor haz solo movilidad o descansa."
        color = "red"
    else:
        consejo = "⚠️ Revisa cómo te sientes. Hoy podría ser día de recuperación activa."
        color = "gray"

    # Ajustes adicionales
    if horas_sueno < 6:
        consejo += " 💤 Dormiste poco. Ajusta el entreno o enfócate en movilidad."
    if strain > 15:
        consejo += " ⚠️ Ayer tuviste un día exigente. Considera reducir intensidad hoy."

    return consejo, color


# --- FUNCIONES DE PARSEO Y NORMALIZACIÓN DE EJERCICIOS ---

def normalizar_nombre_ejercicio(nombre):
    """
    Estandariza el nombre de un ejercicio para consistencia.
    Ej: " press banca " -> "Press Banca"
    """
    if not isinstance(nombre, str):
        return nombre
    return nombre.strip().title()


def parsear_ejercicios_de_notas(notas):
    """
    Parsea un bloque de texto de notas y extrae una lista de diccionarios de ejercicios.
    """
    ejercicios = []
    if not notas:
        return ejercicios

    # Limpieza inicial del texto
    notas_limpias = notas.replace("\\n", "\n")
    if "Ejercicios Detallados:" in notas_limpias:
        notas_limpias = notas_limpias.split("Ejercicios Detallados:")[-1]

    lineas = notas_limpias.strip().splitlines()

    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue

        # Expresión regular para capturar el formato: [✓/✗/N] Nombre: Peso, SeriesxRepeticiones
        match = re.match(r'^[✓✗N]?\s*(.+?):\s*([\d.,PC]+),\s*(\d+x\d+.*)', linea, re.IGNORECASE)
        if match:
            nombre, peso, repeticiones_str = match.groups()
            completado_raw = linea.lstrip()[0] if linea.lstrip()[0] in '✓✗N' else ''

            ejercicios.append({
                'nombre': normalizar_nombre_ejercicio(nombre),
                'peso': peso.strip(),
                'repeticiones': repeticiones_str.strip(),
                'completado': completado_raw == '✓',
            })

    return ejercicios


def parse_reps_and_series(rep_str):
    """
    ✅ NUEVA FUNCIÓN ROBUSTA
    Parsea un string de repeticiones (ej: "3x10-12" o solo "12") y devuelve
    una tupla (series, repeticiones_promedio).
    Siempre devuelve una tupla para evitar errores de desempaquetado.
    """
    if not rep_str:
        return (1, 0)  # Devuelve valores por defecto si la entrada es vacía

    try:
        # Convertimos a string y limpiamos la entrada
        texto = str(rep_str).lower().replace('×', 'x').replace(' ', '')

        series = 1
        # Extraer series si existen (ej: 3x...)
        if 'x' in texto:
            parts = texto.split('x')
            # Asegurarse de que la parte de las series sea un número válido
            if parts[0].isdigit():
                series = int(parts[0])
            rep_part = parts[1]
        else:
            rep_part = texto

        # Extraer todos los números de la parte de las repeticiones (ej: 10-12 o solo 10)
        numeros = [int(n) for n in re.findall(r'\d+', rep_part)]

        if not numeros:
            return (series, 0)  # Si no se encontraron números, devuelve 0 reps

        # Calcular el promedio de las repeticiones encontradas
        repeticiones = int(sum(numeros) / len(numeros))

        return (series, repeticiones)

    except (ValueError, TypeError, IndexError):
        # Si ocurre cualquier error durante el proceso, devuelve valores seguros.
        return (1, 0)
