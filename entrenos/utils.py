import re


# entrenos/utils.py

def normalizar_nombre_ejercicio(nombre):
    if not isinstance(nombre, str):
        return nombre
    return nombre.strip().title()


def extraer_ejercicios(notas_texto):
    ejercicios = []

    if not notas:
        return ejercicios

    # Reemplazar "\n" y "\\n" por saltos de línea reales
    notas = notas.replace("\\n", "\n").replace("\n", "\n")

    # Cortar encabezado si existe
    if "Ejercicios Detallados:" in notas:
        notas = notas.split("Ejercicios Detallados:")[-1]

    lineas = notas.strip().splitlines()

    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue

        match = re.match(r'^([✓✗N]?)\s*(.+?):\s*([\d.,PC]+),\s*(\d+x\d+)', linea)
        if match:
            completado_raw, nombre, peso, repeticiones = match.groups()
            nombre = re.sub(r'^[✓✗N\s\\n]*', '', nombre.strip())
            ejercicios.append({
                'nombre': nombre,
                'peso': peso.strip(),
                'repeticiones': repeticiones.strip(),
                'completado': completado_raw == '✓',
            })

    return ejercicios


import re


def parsear_ejercicios(notas):
    ejercicios = []

    if not notas:
        return ejercicios

    # Reemplazar "\n" y "\\n" por saltos de línea reales
    notas = notas.replace("\\n", "\n").replace("\n", "\n")

    # Cortar encabezado si existe
    if "Ejercicios Detallados:" in notas:
        notas = notas.split("Ejercicios Detallados:")[-1]

    lineas = notas.strip().splitlines()

    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue

        match = re.match(r'^([✓✗N]?)\s*(.+?):\s*([\d.,PC]+),\s*(\d+x\d+)', linea)
        if match:
            completado_raw, nombre, peso, repeticiones = match.groups()
            nombre = re.sub(r'^[✓✗N\s\\n]*', '', nombre.strip())
            ejercicios.append({
                'nombre': nombre,
                'peso': peso.strip(),
                'repeticiones': repeticiones.strip(),
                'completado': completado_raw == '✓',
            })

    return ejercicios


def analizar_entreno_whoop(registro):
    hrv = registro.hrv
    rhr = registro.rhr
    recovery = registro.recovery
    horas_sueno = registro.horas_sueno.total_seconds() / 3600
    strain = registro.strain

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

    if horas_sueno < 6:
        consejo += " 💤 Dormiste poco. Ajusta el entreno o enfócate en movilidad."
    if strain > 15:
        consejo += " ⚠️ Ayer tuviste un día exigente. Considera reducir intensidad hoy."

    return consejo, color
