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
