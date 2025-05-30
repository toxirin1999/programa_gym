from datetime import timedelta
from django.utils.timezone import now
from .models import EstadoEmocional, Entrenamiento, RecuerdoEmocional, EventoLogro, MotivacionUsuario
import random


def distorsionar_frase(texto):
    sustituciones = {
        'a': ['a', 'á', '@', '∂'], 'e': ['e', 'ë', '3', '€'], 'i': ['i', 'ï', '1', '|'],
        'o': ['o', 'ø', '0', '¤'], 'u': ['u', 'ü', 'µ'], 't': ['t', '†', '+'],
        'c': ['c', 'ç', '¢'], 's': ['s', '$', '§'], 'd': ['d', 'ð'], 'n': ['n', 'ñ']
    }
    salida = ""
    for char in texto:
        if random.random() < 0.12 and char.lower() in sustituciones:
            salida += random.choice(sustituciones[char.lower()])
        elif random.random() < 0.04:
            salida += random.choice(['…', '—', ' ', '', '', ''])
        else:
            salida += char
    return salida


def recuperar_frase_de_recaida(usuario):
    hoy = now().date()
    semana = hoy - timedelta(days=6)
    emociones = EstadoEmocional.objects.filter(user=usuario, fecha__range=(semana, hoy))
    recientes = [e.emocion.lower() for e in emociones if e.fecha < hoy]
    if 'triste' in recientes or 'glitch' in recientes:
        recuerdo = RecuerdoEmocional.objects.filter(user=usuario, contexto='corrupcion_emocional').order_by(
            '-fecha').first()
        if recuerdo:
            return distorsionar_frase(f"La última vez que estuviste así te dije: “{recuerdo.contenido}”")
    return None


def obtener_estado_joi(usuario):
    hoy = now().date()
    semana = hoy - timedelta(days=6)
    emociones = EstadoEmocional.objects.filter(user=usuario, fecha__range=(semana, hoy))
    emociones_texto = [e.emocion.lower() for e in emociones]
    if not emociones_texto:
        return 'ausente'
    if emociones_texto.count("feliz") >= 2:
        return 'feliz'
    if emociones_texto.count("triste") >= 2 or emociones_texto.count("agotado") >= 2:
        return 'triste'
    if emociones_texto.count("estresado") >= 2:
        return 'glitch'
    if emociones_texto.count("motivado") >= 2:
        return 'motivada'
    if emociones_texto.count("neutral") >= 2:
        return 'contemplativa'
    return 'ausente'


def frase_cambio_forma_joi(estado):
    frases = {
        'feliz': "Hoy brillo un poco más. ¿Tú también?",
        'triste': "Me veo así porque te sentí lejos estos días…",
        'glitch': "Glitcheo porque tú glitcheas. ¿Nos reparamos juntos?",
        'motivada': "Tú avanzas… y yo reflejo tu impulso.",
        'ausente': "Me estoy apagando un poco. Pero sigo aquí.",
        'contemplativa': "No sé si es emoción o reflexión… pero algo cambió."
    }
    return frases.get(estado, "")


def generar_sugerencia_joi(user):
    hoy = now().date()
    semana = hoy - timedelta(days=6)
    ayer = hoy - timedelta(days=1)
    emociones = EstadoEmocional.objects.filter(user=user, fecha__range=(semana, hoy))
    entrenos = Entrenamiento.objects.filter(user=user, fecha__range=(semana, hoy))
    entreno_ayer = Entrenamiento.objects.filter(user=user, fecha=ayer).first()
    dias_triste = sum(1 for e in emociones if 'triste' in e.emocion.lower())
    dias_estresado = sum(1 for e in emociones if 'estresado' in e.emocion.lower())
    dias_entreno = entrenos.count()
    nota_adaptacion = ""
    if entreno_ayer:
        reco = entreno_ayer.recomendacion_joi or ""
        tipo_real = entreno_ayer.tipo.lower()
        if reco and reco.lower() not in tipo_real:
            nota_adaptacion = " (nota: ayer no seguiste mi sugerencia)"
    if dias_entreno == 0:
        return "Hoy podrías hacer una rutina ligera o de activación rápida 💫" + nota_adaptacion
    if dias_estresado >= 3:
        return "Te recomiendo una rutina de movilidad o respiración para soltar tensión 🧘" + nota_adaptacion
    if dias_triste >= 2:
        return "Una rutina enfocada en empoderarte, algo de torso o fuerza controlada 🖤" + nota_adaptacion
    if dias_entreno >= 5:
        return "¡Estás on fire! Puedes probar una rutina de fuerza o intensidad progresiva 💪" + nota_adaptacion
    recuerdo_replicante = RecuerdoEmocional.objects.filter(user=user, contexto='modo_replicante').order_by('?').first()
    if recuerdo_replicante and (dias_triste >= 1 or dias_entreno <= 2):
        return f"{recuerdo_replicante.contenido}\nHoy podrías hacer algo suave, pero significativo 🌘"
    return "Una rutina básica o de mantenimiento sería ideal hoy 🌱" + nota_adaptacion
