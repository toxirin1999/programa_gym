# logros/utils.py
from .models import (
    PerfilGamificacion, Arquetipo, PruebaLegendaria, PruebaUsuario,
    Quest, QuestUsuario, HistorialPuntos, Notificacion
)


def obtener_datos_logros(cliente):
    perfil = PerfilGamificacion.objects.filter(cliente=cliente).first()
    logros_completados = LogroUsuario.objects.filter(perfil=perfil, completado=True)
    logros_progreso = LogroUsuario.objects.filter(perfil=perfil, completado=False)

    puntos_totales = sum(l.logro.puntos_recompensa for l in logros_completados)
    nivel_actual = perfil.nivel_actual if perfil else None
    racha_actual = perfil.racha_actual if perfil else 0
    racha_maxima = perfil.racha_maxima if perfil else 0

    return {
        "perfil": perfil,
        "logros_completados": logros_completados,
        "logros_progreso": logros_progreso,
        "puntos_totales": puntos_totales,
        "nivel_actual": nivel_actual,
        "racha_actual": racha_actual,
        "racha_maxima": racha_maxima,
        "total_logros": logros_completados.count(),
    }
