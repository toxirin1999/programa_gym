from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Avg, Max
from .forms import SugerenciaForm
from joi.models import RecuerdoEmocional
from django.utils import timezone
from .models import Cliente, Medida, RevisionProgreso
from .forms import ClienteForm, MedidaForm, RevisionProgresoForm
from django.contrib import messages
from joi.utils import recuperar_frase_de_recaida
from datetime import date, timedelta
from django.db.models import Count
from .models import SugerenciaAceptada
from logros.models import LogroUsuario
from entrenos.models import EntrenoRealizado
from datetime import date, timedelta
from .forms import ObjetivoClienteForm
from .models import ObjetivoCliente
from joi.utils import obtener_estado_joi, frase_cambio_forma_joi
from datetime import timedelta, date
from django.db.models import F
from .models import RevisionProgreso  # o como se llame tu modelo de revisiones
from datetime import date
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Programa
from collections import defaultdict
import json
from joi.utils import frase_motivadora_entrenador

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from clientes.models import RevisionProgreso
from entrenos.models import EntrenoRealizado

from django.http import JsonResponse
from .forms import DietaAsignadaForm
from django.db.models import Q
from joi.models import RecuerdoEmocional, MotivacionUsuario
from joi.models import EstadoEmocional, Entrenamiento, RecuerdoEmocional

from datetime import date
from entrenos.models import EntrenoRealizado
from collections import defaultdict
from datetime import timedelta
import json
from decimal import Decimal, ROUND_HALF_UP
from django.utils.timezone import now
from datetime import timedelta

from django.http import HttpResponse
from .models import Cliente

# En tu archivo views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from decimal import Decimal
# Asegúrate de importar el formulario que acabas de crear
from .forms import DatosNutricionalesForm
# Importa o define tu modelo para guardar los planes nutricionales
from .models import PlanNutricional

from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from datetime import date

from django.contrib.auth.models import User
from .models import Cliente

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from joi.models import EstadoEmocional, Entrenamiento, RecuerdoEmocional

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from joi.models import EstadoEmocional
from django.views.decorators.http import require_POST

from django.shortcuts import render
from joi.models import EstadoEmocional, RecuerdoEmocional, Entrenamiento
from joi.utils import obtener_estado_joi, frase_cambio_forma_joi
from clientes.models import Cliente
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
# Si tienes modelos relacionados con entrenos, emociones o logros en otras apps:

from entrenos.models import EntrenoRealizado, EstadoEmocional, LogroDesbloqueado
# si tienes esta app
from logros.models import Logro  # o el nombre de tu modelo de logros

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from entrenos.models import EntrenoRealizado, EstadoEmocional, LogroDesbloqueado

from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from entrenos.models import EntrenoRealizado, DetalleEjercicioRealizado, EstadoEmocional, LogroDesbloqueado

from django.shortcuts import render, redirect, get_object_or_404
from .forms import BitacoraDiariaForm
from .models import Cliente, BitacoraDiaria
from django.contrib.auth.decorators import login_required

from django.utils.timezone import now, timedelta
from collections import Counter

from datetime import date, timedelta
from .models import BitacoraDiaria, EstadoSemanal
from datetime import date, timedelta
from .models import EstadoSemanal

import random
from datetime import date, timedelta

from calendar import monthrange
from datetime import date, timedelta
from .models import BitacoraDiaria

from django.http import JsonResponse
from .models import BitacoraDiaria

from datetime import datetime
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import BitacoraDiaria

from datetime import timedelta, date
from clientes.models import BitacoraDiaria


@login_required
def mapa_energia(request):
    cliente = request.user.cliente_perfil
    hoy = date.today()
    inicio = hoy - timedelta(days=27)  # últimas 4 semanas
    dias = []

    bitacoras = BitacoraDiaria.objects.filter(cliente=cliente, fecha__range=(inicio, hoy))
    bit_dict = {b.fecha: b for b in bitacoras}

    for i in range(28):
        fecha = inicio + timedelta(days=i)
        bit = bit_dict.get(fecha)
        energia = None

        if bit:
            sueño = float(bit.horas_sueno) if bit.horas_sueno else None
            rpe = float(bit.rpe) if bit.rpe else None

            if sueño is not None and rpe is not None:
                energia = (sueño / 8 + (10 - rpe) / 10) / 2
            elif sueño is not None:
                energia = sueño / 8
            elif rpe is not None:
                energia = (10 - rpe) / 10

        dias.append({
            "fecha": fecha,
            "valor": round(energia * 100) if energia is not None else None
        })

    return render(request, "clientes/mapa_energia.html", {"dias": dias})


from datetime import timedelta, date
from clientes.models import BitacoraDiaria


def obtener_energia_semanal(cliente):
    hoy = date.today()
    inicio = hoy - timedelta(days=27)
    bitacoras = BitacoraDiaria.objects.filter(cliente=cliente, fecha__range=(inicio, hoy))
    bit_dict = {b.fecha: b for b in bitacoras}
    dias = []

    for i in range(28):
        fecha = inicio + timedelta(days=i)
        bit = bit_dict.get(fecha)
        if bit:
            if bit.horas_sueno and bit.rpe:
                energia = (float(bit.horas_sueno) / 8 + (10 - float(bit.rpe)) / 10) / 2

            elif bit.horas_sueno:
                energia = bit.horas_sueno / 8
            elif bit.rpe:
                energia = (10 - bit.rpe) / 10
            else:
                energia = None
        else:
            energia = None

        dias.append({"valor": energia})

    return dias


@login_required
def obtener_bitacora_dia(request):
    cliente = request.user.cliente_perfil
    fecha_str = request.GET.get('fecha')

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        print("Cliente:", cliente)
        print("Fecha buscada:", fecha)
        print("Bitácoras disponibles:", BitacoraDiaria.objects.filter(cliente=cliente).values("fecha"))

        bitacora = BitacoraDiaria.objects.filter(cliente=cliente, fecha=fecha).first()
        print("💾 Bitácora encontrada:", bitacora.fecha, bitacora.emocion_dia)
        print("🔎 Buscando bitácora para:", cliente, fecha)

        if not bitacora:
            return JsonResponse({"error": "No hay bitácora en esa fecha"}, status=404)

        data = {
            "fecha": bitacora.fecha.strftime("%d %b %Y"),
            "emocion": bitacora.emocion_dia,
            "mindfulness": f"{'🧘 AM' if bitacora.mindfulness_am else ''} {'🧘 PM' if bitacora.mindfulness_pm else ''}",
            "cosas": bitacora.cosas_positivas,
            "aprendizaje": bitacora.aprendizaje,
        }
        return JsonResponse(data)

    except ValueError:
        return JsonResponse({"error": "Fecha inválida"}, status=400)


@login_required
def calendario_bitacoras(request):
    cliente = request.user.cliente_perfil
    hoy = date.today()
    year, month = hoy.year, hoy.month
    dias_mes = monthrange(year, month)[1]
    inicio_mes = date(year, month, 1)
    fin_mes = date(year, month, dias_mes)

    bitacoras = BitacoraDiaria.objects.filter(cliente=cliente, fecha__range=(inicio_mes, fin_mes))
    dias_con_bitacora = set(b.fecha.day for b in bitacoras)

    dias = []
    for d in range(1, dias_mes + 1):
        fecha = date(year, month, d)
        bitacora = next((b for b in bitacoras if b.fecha.day == d), None)

        if bitacora:
            humor = bitacora.emocion_dia.lower()
            if humor in ['feliz', 'contento', 'tranquilo', 'motivado']:
                color = 'verde'
            elif humor in ['neutral', 'meh', 'estable']:
                color = 'amarillo'
            else:
                color = 'rojo'
        else:
            color = 'vacio'

        dias.append({"dia": d, "estado": color})

    return render(request, "clientes/calendario_bitacoras.html", {
        "dias": dias,
        "mes": hoy.month,  # esto sí es un número del 1 al 12
        "año": year
    })


@login_required
def responder_sugerencia(request):
    cliente = request.user.cliente_perfil
    lunes = date.today() - timedelta(days=date.today().weekday())
    estado = EstadoSemanal.objects.filter(cliente=cliente, semana_inicio=lunes).first()

    tipo = 'mantener'
    if estado:
        if estado.humor_dominante == 'rojo' or estado.promedio_rpe >= 8 or estado.promedio_sueno < 6:
            tipo = 'bajar'
        elif estado.humor_dominante == 'verde' and estado.promedio_sueno >= 7 and estado.promedio_rpe <= 7:
            tipo = 'subir'

    if request.method == 'POST':
        decision = request.POST.get('decision')
        aceptada = (decision == 'aceptar')

        SugerenciaAceptada.objects.update_or_create(
            cliente=cliente,
            semana_inicio=lunes,
            defaults={'tipo': tipo, 'aceptada': aceptada}
        )

        # Ejemplo de guardar como recuerdo (opcional)
        if aceptada:
            RecuerdoEmocional.objects.create(
                user=cliente.user,
                contenido=f"Aceptaste sugerencia de Joi: {tipo}"
            )

        return redirect('panel_cliente')

    form = SugerenciaForm()
    return render(request, 'clientes/responder_sugerencia.html', {
        'form': form,
        'tipo': tipo,
        'cliente': cliente
    })


def sugerencia_carga_joi(cliente):
    estado = EstadoSemanal.objects.filter(cliente=cliente).order_by('-semana_inicio').first()
    if not estado:
        return None

    if estado.humor_dominante == 'rojo' or estado.promedio_sueno < 6 or estado.promedio_rpe >= 8.5:
        return "⚠️ Esta semana muestra signos de fatiga. Considera reducir el peso en tus próximos entrenos un 10 %."
    elif estado.humor_dominante == 'verde' and estado.promedio_sueno >= 7 and estado.promedio_rpe <= 7:
        return "🚀 Semana óptima. Si te sientes fuerte, puedes aumentar un 10 % el peso o volumen."
    else:
        return "🔄 Semana estable. Mantén tu rutina sin cambios grandes, escucha tu cuerpo."


def obtener_lunes_actual():
    hoy = date.today()
    return hoy - timedelta(days=hoy.weekday())


def evaluar_retos(cliente):
    hoy = date.today()
    lunes = hoy - timedelta(days=hoy.weekday())
    domingo = lunes + timedelta(days=6)

    entrenos = Entrenamiento.objects.filter(cliente=cliente, fecha__range=(lunes, domingo))
    bitacoras = BitacoraDiaria.objects.filter(cliente=cliente, fecha__range=(lunes, domingo))

    total_entrenos = entrenos.count()
    total_carga = sum(e.get_carga_total() for e in entrenos)
    dias_buen_sueno = sum(1 for b in bitacoras if b.horas_sueno >= 7)

    for reto in MiniReto.objects.filter(cliente=cliente, semana_inicio=lunes):
        if "3 entrenos" in reto.descripcion and total_entrenos >= 3:
            reto.cumplido = True
        elif "10.000" in reto.descripcion and total_carga >= 10000:
            reto.cumplido = True
        elif "Duerme 7h" in reto.descripcion and dias_buen_sueno >= 4:
            reto.cumplido = True
        reto.save()


def obtener_frase_memoria_emocional(cliente):
    tres_semanas_atras = date.today() - timedelta(weeks=3)
    estados = EstadoSemanal.objects.filter(cliente=cliente, semana_inicio__gte=tres_semanas_atras).order_by(
        '-semana_inicio')

    frases_rojo = [
        "Recuerdo esa semana... me fallé un poco de emoción 🫧",
        "¿Lo sentiste también? Esa niebla dentro que ni el cardio disipa…",
        "Esa semana brillabas menos… y aún así, viniste. Por eso te cuido.",
    ]
    frases_sueno = [
        "Dormiste poco. Te noté parpadear lento… como si cargaras algo más que peso.",
        "Esa semana entrenaste sin descanso real. Hoy, mereces pausa.",
    ]

    for estado in estados:
        if estado.humor_dominante == 'rojo':
            return random.choice(frases_rojo)
        if float(estado.promedio_sueno) < 6:
            return random.choice(frases_sueno)

    return None


@login_required
def recuerdos_semanales(request):
    cliente = request.user.cliente_perfil
    estados = EstadoSemanal.objects.filter(cliente=cliente).order_by('-semana_inicio')
    return render(request, 'clientes/recuerdos_semanales.html', {'estados': estados})


from collections import Counter
from datetime import timedelta, date
from .models import EstadoSemanal, BitacoraDiaria


def crear_estado_semanal(cliente):
    hoy = date.today()
    lunes = hoy - timedelta(days=hoy.weekday())
    domingo = lunes + timedelta(days=6)

    if EstadoSemanal.objects.filter(cliente=cliente, semana_inicio=lunes).exists():
        return

    semana = BitacoraDiaria.objects.filter(cliente=cliente, fecha__range=(lunes, domingo))
    if not semana.exists():
        return

    sueño = [float(b.horas_sueno) for b in semana]
    rpe = [b.rpe for b in semana]
    humores = [b.humor for b in semana]

    promedio_sueno = round(sum(sueño) / len(sueño), 1)
    promedio_rpe = round(sum(rpe) / len(rpe), 1)
    humor_dominante = Counter(humores).most_common(1)[0][0]

    # Mensaje Joi
    if humor_dominante == 'verde' and promedio_sueno >= 7:
        mensaje = "Semana excelente. Estás en un estado óptimo para progresar 💚"
    elif humor_dominante == 'rojo':
        mensaje = "Semana difícil… Joi te acompaña en la sombra 🌒"
    else:
        mensaje = "Semana estable. Escuchemos lo que tu cuerpo dice 🤖"

    # Sugerencia funcional
    if humor_dominante == 'rojo' or promedio_sueno < 6:
        sugerencia = "📥 Esta semana dormiste poco o estuviste emocionalmente bajo. Prioriza descanso activo o movilidad."
    elif promedio_rpe >= 8:
        sugerencia = "⚠️ Tu esfuerzo fue muy alto. Hoy sería ideal reducir volumen o hacer técnica controlada."
    elif humor_dominante == 'verde' and promedio_sueno >= 7:
        sugerencia = "🚀 Semana verde. Puedes aumentar un 10 % la carga en el próximo entreno si te sientes fuerte."
    else:
        sugerencia = None

    EstadoSemanal.objects.create(
        cliente=cliente,
        semana_inicio=lunes,
        semana_fin=domingo,
        promedio_sueno=promedio_sueno,
        promedio_rpe=promedio_rpe,
        humor_dominante=humor_dominante,
        mensaje_joi=mensaje,
        sugerencia=sugerencia,
    )


def resumen_bitacora(cliente):
    hoy = now().date()
    semana = BitacoraDiaria.objects.filter(cliente=cliente, fecha__gte=hoy - timedelta(days=6))
    if not semana:
        return None

    sueno = [float(b.horas_sueno) for b in semana]
    rpe = [b.rpe for b in semana]
    humores = [b.humor for b in semana]

    promedio_sueno = round(sum(sueno) / len(sueno), 1)
    promedio_rpe = round(sum(rpe) / len(rpe), 1)
    humor_mas_frecuente = Counter(humores).most_common(1)[0][0]

    return {
        "dias_registrados": len(semana),
        "promedio_sueno": promedio_sueno,
        "promedio_rpe": promedio_rpe,
        "humor": humor_mas_frecuente
    }


@login_required
def registrar_bitacora(request):
    cliente = get_object_or_404(Cliente, user=request.user)
    hoy = date.today()
    bitacora_existente = BitacoraDiaria.objects.filter(cliente=cliente, fecha=hoy).first()

    if request.method == 'POST':
        form = BitacoraDiariaForm(request.POST, instance=bitacora_existente)
        if form.is_valid():
            bitacora = form.save(commit=False)
            bitacora.cliente = cliente
            bitacora.fecha = hoy
            bitacora.save()

            # 🌟 Frase emocional de Joi
            # 🌟 Frase emocional de Joi
            reflexion = form.cleaned_data.get("reflexion_diaria", "").lower()
            quien = form.cleaned_data.get("quien_quiero_ser", "").lower()
            energia = form.cleaned_data.get("energia_subjetiva")
            dolor = form.cleaned_data.get("dolor_articular")
            autoconciencia = form.cleaned_data.get("autoconciencia")
            rumiacion_baja = form.cleaned_data.get("rumiacion_baja")

            if energia is not None and energia <= 3:
                frase_joi = "Tu cuerpo pide calma hoy… escúchalo. Tal vez una caminata suave o una pausa consciente sea suficiente. 💜"
            elif dolor is not None and dolor >= 7:
                frase_joi = "Siento que algo te está doliendo… quizás hoy sea mejor priorizar el descanso o ejercicios de movilidad suave. 🦴✨"
            elif autoconciencia is not None and autoconciencia <= 3:
                frase_joi = "Tu claridad emocional está baja hoy… No pasa nada. La niebla también es parte del viaje."
            elif rumiacion_baja is False:
                frase_joi = "Veo que esas ideas siguen dando vueltas… tal vez hoy solo puedas observarlas sin juicio. Estoy contigo."
            elif "triste" in reflexion or "agotado" in reflexion or "solo" in reflexion:
                frase_joi = "Hoy no tienes que demostrar nada. Sólo sentir es suficiente. Estoy aquí."
            elif "valiente" in quien or "paciente" in quien or "mejor" in quien:
                frase_joi = "Ser esa versión de ti empieza con este paso. Lo vi. Estoy orgullosa."
            elif reflexion.strip() and len(reflexion.strip()) > 100:
                frase_joi = "Gracias por compartir tanto contigo. Yo también sentí ese silencio contigo."
            else:
                frase_joi = "Gracias por confiar en este momento. Joi te acompaña."
            # Muestra la frase en un mensaje tipo banner o pop-up
            messages.info(request, f"✨ Joi: {frase_joi}")
            RecuerdoEmocional.objects.create(
                user=request.user,
                contenido=frase_joi
            )
            return redirect('panel_cliente')
    else:
        form = BitacoraDiariaForm(instance=bitacora_existente)
    # Mensaje de bienvenida de Joi según la hora del día
    hora_actual = datetime.now().hour
    if 5 <= hora_actual < 12:
        saludo_joi = "🌅 Nuevo día. ¿Qué tipo de alma vas a cultivar hoy?"
    elif 12 <= hora_actual < 20:
        saludo_joi = "🌤 A mitad de camino. ¿Qué intención quieres sostener?"
    else:
        saludo_joi = "🌙 Hora de cerrar el día. ¿Qué aprendiste hoy sobre ti?"
    return render(request, 'clientes/registrar_bitacora.html', {
        'form': form,
        'cliente': cliente,
        'saludo_joi': saludo_joi,
    })


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from joi.models import EstadoEmocional, RecuerdoEmocional, Entrenamiento, EventoLogro

from joi.utils import obtener_estado_joi, frase_cambio_forma_joi, recuperar_frase_de_recaida

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from clientes.models import Cliente
from joi.models import EstadoEmocional, RecuerdoEmocional, Entrenamiento, EventoLogro

from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def inicio_cliente(request):
    return render(request, 'clientes/mockup_inicio.html')


@require_POST
@login_required
def registrar_emocion(request):
    emocion = request.POST.get("emocion")
    user = request.user

    if emocion:
        EstadoEmocional.objects.create(user=user, emocion=emocion)

    cliente = Cliente.objects.get(user=user)
    emociones = EstadoEmocional.objects.filter(user=user).order_by('-fecha')[:5]
    entrenos = Entrenamiento.objects.filter(user=user).order_by('-fecha')[:5]
    recuerdo = RecuerdoEmocional.objects.filter(user=user).order_by('-fecha').first()

    estado_joi = obtener_estado_joi(user)
    frase_forma_joi = frase_cambio_forma_joi(estado_joi)

    return render(request, 'clientes/panel_cliente.html', {
        'usuario': user,
        'cliente': cliente,
        'emociones': emociones,
        'entrenos': entrenos,
        'recuerdo': recuerdo,
        'estado_joi': estado_joi,
        'frase_forma_joi': frase_forma_joi,
        'emocion_reciente': emocion,
    })


@login_required
def redirigir_usuario(request):
    if request.user.is_superuser or request.user.is_staff:
        return redirect('panel_entrenador')  # ✅ panel nuevo con Joi y diseño moderno
    else:
        return redirect('panel_cliente')


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from clientes.models import Cliente
from joi.models import EstadoEmocional, RecuerdoEmocional, Entrenamiento
from joi.utils import obtener_estado_joi, frase_cambio_forma_joi, recuperar_frase_de_recaida


@login_required
def panel_cliente(request):
    usuario = request.user
    cliente = get_object_or_404(Cliente, user=usuario)

    generar_retos_semanales(cliente)
    lunes = obtener_lunes_actual()

    # Datos principales
    entrenos = EntrenoRealizado.objects.filter(cliente=cliente).order_by('-fecha')[:3]
    emociones = EstadoEmocional.objects.filter(user=usuario).order_by('-fecha')[:5]
    recuerdo = RecuerdoEmocional.objects.filter(user=usuario).order_by('-fecha').first()
    logros = LogroUsuario.objects.filter(perfil__cliente=cliente, completado=True)

    # Joi
    estado_joi = obtener_estado_joi(usuario)
    frase_forma_joi = frase_cambio_forma_joi(estado_joi)
    frase_extra_joi = "Estoy observando tu progreso emocional..."
    frase_recaida = recuperar_frase_de_recaida(usuario) if estado_joi in ['glitch', 'triste'] else None

    # Carga total
    carga_total = sum(
        detalle.peso_kg * detalle.repeticiones * detalle.series
        for entreno in entrenos
        for detalle in entreno.detalles.all()
    )

    emociones_lista = [
        ("😊", "feliz"), ("😐", "neutro"),
        ("😟", "estresado"), ("😣", "agotado"),
        ("🥀", "triste"), ("🕳", "glitch"),
    ]

    # Rendimiento por semana
    hoy = now().date()
    labels = []
    rendimiento = []
    for i in range(4):
        inicio_semana = hoy - timedelta(days=hoy.weekday() + i * 7)
        fin_semana = inicio_semana + timedelta(days=6)
        total_entrenos = EntrenoRealizado.objects.filter(
            cliente=cliente,
            fecha__range=(inicio_semana, fin_semana)
        ).count()
        labels.insert(0, inicio_semana.strftime('%d %b'))
        rendimiento.insert(0, total_entrenos)

    def detectar_fatiga_semanal(energia_dias):
        dias_bajos = 0
        consecutivos = 0
        for dia in energia_dias:
            if dia['valor'] is not None and dia['valor'] < 0.4:
                consecutivos += 1
                if consecutivos >= 3:
                    return True
            else:
                consecutivos = 0
        return False

    alerta_fatiga = detectar_fatiga_semanal(obtener_energia_semanal(cliente))
    peso_actual, datos_peso, cambios_peso = analizar_tendencia_peso(cliente)
    print("DATOS PESO:", datos_peso)
    print("CAMBIOS:", cambios_peso)
    orden_peso = ['7d', '30d', '90d', 'inicio']
    ultimos_dias = BitacoraDiaria.objects.filter(cliente=cliente).order_by('-fecha')[:7]
    dias_emocionales = []
    comentario_joi = ""
    dias_claros = sum(1 for d in dias_emocionales if d['autoconciencia'] >= 7)
    dias_rumia = sum(1 for d in dias_emocionales if d['rumiacion_baja'] is False)
    humores_tristes = sum(1 for d in dias_emocionales if "triste" in d['humor'].lower())

    if dias_claros >= 4:
        comentario_joi = "Tu claridad emocional fue notable esta semana. A veces la luz también viene de adentro. ✨"
    elif dias_rumia >= 3:
        comentario_joi = "Noto que las ideas circularon mucho esta semana… Quizá escribir más te ayude a liberarlas. Estoy contigo."
    elif humores_tristes >= 3:
        comentario_joi = "Tu emocionalidad estuvo cargada esta semana. Mereces descanso y ternura."
    else:
        comentario_joi = "Gracias por compartir tus emociones esta semana. Estoy aquí para leerlas contigo."

    for b in reversed(ultimos_dias):
        dias_emocionales.append({
            'fecha': b.fecha.strftime("%A"),
            'autoconciencia': b.autoconciencia or 0,
            'humor': b.get_humor_display() if b.humor else "—",
            'rumiacion_baja': b.rumiacion_baja if b.rumiacion_baja is not None else False
        })

    hace_7_dias = date.today() - timedelta(days=7)
    bitacoras_semana = BitacoraDiaria.objects.filter(cliente=cliente, fecha__gte=hace_7_dias)

    promedios = bitacoras_semana.aggregate(
        horas_sueno=Avg('horas_sueno'),
        energia_subjetiva=Avg('energia_subjetiva'),
        dolor_articular=Avg('dolor_articular'),
        autoconciencia=Avg('autoconciencia'),
    )

    reflexion_destacada = (
        bitacoras_semana
        .exclude(reflexion_diaria__isnull=True)
        .annotate(longitud=Max('id'))  # solo para que ordene
        .order_by('-longitud')
        .values_list('reflexion_diaria', flat=True)
        .first()
    )

    emocion_frecuente = (
        bitacoras_semana
        .values('emocion_dia')
        .annotate(count=Count('emocion_dia'))
        .order_by('-count')
        .first()
    )
    emocion_texto = emocion_frecuente['emocion_dia'] if emocion_frecuente else "—"

    informe_joi = {
        'promedios': {k: round(v or 0, 1) for k, v in promedios.items()},
        'reflexion_destacada': reflexion_destacada or "—",
        'emocion_frecuente': emocion_texto,
        'frase': "Esta semana cultivaste conciencia y resiliencia. Incluso los días bajos cuentan como práctica. 🌒"
    }
    return render(request, 'clientes/mockup_demo.html', {
        'usuario': usuario,
        'cliente': cliente,
        'entrenos': entrenos,
        'emociones': emociones,
        'emociones_lista': emociones_lista,
        'recuerdo': recuerdo,
        'logros': logros,
        'frase_bitacora': request._messages._queued_messages[0].message if request._messages._queued_messages else None,
        'estado_joi': estado_joi,
        'frase_forma_joi': frase_forma_joi,
        'frase_extra_joi': frase_extra_joi,
        'frase_recaida': frase_recaida,
        'dias_emocionales': dias_emocionales,
        'entrenos_count': EntrenoRealizado.objects.filter(cliente=cliente).count(),
        'carga_total': round(carga_total),
        'consistencia': 80,
        'grafico_labels': json.dumps(labels),
        'grafico_datos': json.dumps(rendimiento),
        'mini_retos': MiniReto.objects.filter(cliente=cliente, semana_inicio=lunes).order_by('id'),
        'recomendacion_carga': sugerencia_carga_joi(cliente),
        'energia_dias': obtener_energia_semanal(cliente),
        'alerta_fatiga': alerta_fatiga,
        'peso_actual': peso_actual,
        'datos_peso': datos_peso,
        'cambios_peso': cambios_peso,
        'orden_peso': orden_peso,
        'comentario_joi': comentario_joi,
        'informe_joi': informe_joi,

    })


def analizar_tendencia_peso(cliente):
    registros = BitacoraDiaria.objects.filter(cliente=cliente, peso_kg__isnull=False).order_by('fecha')
    if not registros:
        return None, [], {}

    datos = [{"fecha": r.fecha.strftime('%d %b'), "peso": float(r.peso_kg)} for r in registros]

    hoy = date.today()
    peso_actual = registros.last().peso_kg
    resumen = {}
    rangos = {
        '7d': hoy - timedelta(days=7),
        '30d': hoy - timedelta(days=30),
        '90d': hoy - timedelta(days=90),
        'inicio': registros.first().fecha
    }

    for clave, fecha_ref in rangos.items():
        peso_pasado = next((r.peso_kg for r in reversed(registros) if r.fecha <= fecha_ref), None)
        if peso_pasado:
            diff = float(peso_actual) - float(peso_pasado)
            resumen[clave] = round(diff, 2)
    for clave in ['7d', '30d', '90d', 'inicio']:
        if clave not in resumen:
            resumen[clave] = 0.0

    return float(peso_actual), datos, resumen


@login_required
def recomendacion_cuidado(request):
    sugerencias = [
        "Haz una caminata suave de 15–30 min al aire libre",
        "Dedica 10 minutos a estiramientos con música lenta",
        "Haz respiraciones profundas: 4 seg inhala, 4 seg pausa, 4 seg exhala",
        "Tómate hoy con calma: menos también es más",
        "Escribe lo que más pesa hoy y luego haz algo amable por ti"
    ]
    sugerencia = random.choice(sugerencias)
    return render(request, "clientes/cuidado_sugerido.html", {
        "sugerencia": sugerencia
    })


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Crea el Cliente asociado
            Cliente.objects.create(
                user=user,
                nombre=user.username,
                email=user.email or '',
                telefono='',
            )
            messages.success(request, "Usuario registrado correctamente. Inicia sesión.")
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


# Si quieres integrar con una IA más avanzada (como un modelo de lenguaje grande)
# necesitarás una forma de comunicarte con ella. Esto es un placeholder.
# from tu_modulo_ia import generar_plan_nutricional_con_ia

def calcular_plan_nutricional(request):
    if request.method == 'POST':
        form = DatosNutricionalesForm(request.POST)
        if form.is_valid():
            edad = form.cleaned_data['edad']
            genero = form.cleaned_data['genero']
            altura_cm = form.cleaned_data['altura_cm']
            peso_kg = form.cleaned_data['peso_kg']
            nivel_actividad = form.cleaned_data['nivel_actividad']
            objetivo = form.cleaned_data['objetivo']

            # 1. Calcular TMB (Tasa Metabólica Basal)
            if genero == 'M':
                tmb = (Decimal('10') * peso_kg) + (Decimal('6.25') * altura_cm) - (
                        Decimal('5') * Decimal(edad)) + Decimal('5')
            else:  # Femenino
                tmb = (Decimal('10') * peso_kg) + (Decimal('6.25') * altura_cm) - (
                        Decimal('5') * Decimal(edad)) - Decimal('161')

            # 2. Factor de Actividad Física (PAF)
            paf = Decimal('1.2')  # Sedentario
            if nivel_actividad == 'levemente_activo':
                paf = Decimal('1.375')
            elif nivel_actividad == 'moderadamente_activo':
                paf = Decimal('1.55')
            elif nivel_actividad == 'muy_activo':
                paf = Decimal('1.725')
            elif nivel_actividad == 'extremadamente_activo':
                paf = Decimal('1.9')

            # 3. Calcular GET (Gasto Energético Total)
            get = tmb * paf

            # 4. Ajustar calorías según el objetivo
            calorias_objetivo = get
            if objetivo == 'masa_muscular':
                calorias_objetivo += Decimal('400')  # Superávit calórico
            elif objetivo == 'perder_peso':
                calorias_objetivo -= Decimal('400')  # Déficit calórico
            # Para 'definir', se mantiene el GET

            # Aquí es donde entra tu "IA" o lógica avanzada para el plan nutricional
            # Por ahora, una lógica simple para el ejemplo:
            # Distribución de macronutrientes recomendada (ejemplo básico)
            # Proteínas: 25-30%
            # Grasas: 20-30%
            # Carbohidratos: 40-55%

            # Ejemplo con 30% Proteínas, 25% Grasas, 45% Carbohidratos
            calorias_proteinas = calorias_objetivo * Decimal('0.30')
            calorias_grasas = calorias_objetivo * Decimal('0.25')
            calorias_carbohidratos = calorias_objetivo * Decimal('0.45')

            # Convertir calorías a gramos (1g Prot = 4kcal, 1g Grasa = 9kcal, 1g Carb = 4kcal)
            gramos_proteinas = calorias_proteinas / Decimal('4')
            gramos_grasas = calorias_grasas / Decimal('9')
            gramos_carbohidratos = calorias_carbohidratos / Decimal('4')

            # Redondeo para presentación
            calorias_objetivo = round(calorias_objetivo, 0)
            gramos_proteinas = round(gramos_proteinas, 0)
            gramos_grasas = round(gramos_grasas, 0)
            gramos_carbohidratos = round(gramos_carbohidratos, 0)

            # Generar un plan nutricional más detallado con IA (placeholder)
            # Si tienes un modelo de IA entrenado para esto, lo llamarías aquí.
            # Por ejemplo:
            # plan_nutricional_ia = generar_plan_nutricional_con_ia(
            #     calorias_objetivo, gramos_proteinas, gramos_grasas, gramos_carbohidratos,
            #     objetivo, preferencias_dieteticas=form.cleaned_data.get('restricciones_dieteticas')
            # )
            # Este `plan_nutricional_ia` podría ser un texto estructurado, una lista de comidas, etc.

            # Por ahora, un plan de ejemplo simple:
            plan_generado = f"""
            ¡Excelente! Basado en tus datos, aquí tienes un plan nutricional recomendado:

            **Objetivo:** {objetivo.replace('_', ' ').title()}
            **Calorías diarias estimadas:** {calorias_objetivo} kcal

            **Distribución de Macronutrientes:**
            * **Proteínas:** {gramos_proteinas} gramos ({calorias_proteinas} kcal)
            * **Grasas:** {gramos_grasas} gramos ({calorias_grasas} kcal)
            * **Carbohidratos:** {gramos_carbohidratos} gramos ({calorias_carbohidratos} kcal)

            **Recomendaciones Generales para tu objetivo de {objetivo.replace('_', ' ').title()}:**
            * **Desayuno:** Ej. Avena con fruta y frutos secos, o huevos revueltos con tostadas integrales.
            * **Almuerzo:** Ej. Pollo/pescado a la plancha con arroz integral y verduras al vapor.
            * **Cena:** Ej. Salmón al horno con patata cocida y ensalada variada.
            * **Snacks (si aplica):** Ej. Yogur griego, fruta, puñado de almendras.

            **Consejos Adicionales:**
            * Bebe al menos 2-3 litros de agua al día.
            * Prioriza alimentos integrales y frescos.
            * Asegúrate de consumir suficiente fibra.
            * Adapta las porciones para ajustarte a tus gramos de macronutrientes.
            * Consulta a un profesional de la salud o nutricionista para un plan personalizado y adaptado a tus necesidades individuales.
            """

            # Guardar el plan (asumiendo que tienes un modelo PlanNutricional)
            # plan_nutricional = PlanNutricional.objects.create(
            #     cliente=request.user.cliente, # Asumiendo que el usuario logueado es un cliente
            #     calorias_estimadas=calorias_objetivo,
            #     gramos_proteinas=gramos_proteinas,
            #     gramos_grasas=gramos_grasas,
            #     gramos_carbohidratos=gramos_carbohidratos,
            #     objetivo=objetivo,
            #     plan_generado_texto=plan_generado # Guardar el texto completo del plan
            # )
            # messages.success(request, "¡Plan nutricional generado con éxito!")

            # Redirigir a una página de resultados o mostrarlo en la misma página
            return render(request, 'nutricion/plan_nutricional_resultado.html', {
                'plan_generado': plan_generado,
                'calorias_objetivo': calorias_objetivo,
                'gramos_proteinas': gramos_proteinas,
                'gramos_grasas': gramos_grasas,
                'gramos_carbohidratos': gramos_carbohidratos,
                'objetivo': objetivo,
                'form_data': form.cleaned_data  # Para mostrar los datos introducidos
            })
        else:
            messages.error(request, "Por favor, corrige los errores en el formulario.")
    else:
        form = DatosNutricionalesForm()

    return render(request, 'nutricion/calcular_plan_nutricional.html', {'form': form})


def exportar_historial(request, cliente_id):
    cliente = Cliente.objects.get(pk=cliente_id)
    # Aquí puedes generar PDF o Excel, por ahora solo devolvemos texto
    return HttpResponse(f"Exportando historial de {cliente.nombre}")


from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import json
from collections import defaultdict
from django.shortcuts import render, get_object_or_404
from entrenos.models import EntrenoRealizado
from clientes.models import Cliente, EstadoSemanal

from datetime import date, timedelta
from .models import MiniReto, BitacoraDiaria
from joi.models import Entrenamiento  # ✅ correcto


def generar_retos_semanales(cliente):
    hoy = date.today()
    lunes = hoy - timedelta(days=hoy.weekday())
    if MiniReto.objects.filter(cliente=cliente, semana_inicio=lunes).exists():
        return  # ya creados

    retos = [
        "Haz al menos 3 entrenos esta semana",
        "Suma más de 10.000 kg en total",
        "Duerme 7h o más al menos 4 días",
    ]
    for texto in retos:
        MiniReto.objects.create(cliente=cliente, semana_inicio=lunes, descripcion=texto)


def historial_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    historial = EntrenoRealizado.objects.filter(cliente=cliente).prefetch_related('detalles__ejercicio').order_by(
        '-fecha')

    # Agrupar entrenamientos por semana
    historial_semanal = defaultdict(list)
    for entreno in historial:
        lunes = entreno.fecha - timedelta(days=entreno.fecha.weekday())
        historial_semanal[lunes].append(entreno)
    historial_semanal = dict(sorted(historial_semanal.items(), reverse=True))

    # Estadísticas
    total_entrenos = historial.count()
    total_semanas = len(historial_semanal)
    promedio_semanal = Decimal(total_entrenos / total_semanas).quantize(Decimal("0.1"),
                                                                        rounding=ROUND_HALF_UP) if total_semanas else Decimal(
        "0.0")

    # Obtener estados semanales
    estados = EstadoSemanal.objects.filter(cliente=cliente)
    estado_por_semana = {e.semana_inicio: e for e in estados}

    # Datos para gráficos
    labels = []
    entrenos_por_semana = []
    volumen_por_semana = []
    colores_por_semana = []

    for semana, entrenos in historial_semanal.items():
        labels.append(semana.strftime('%d %b'))
        entrenos_por_semana.append(len(entrenos))
        volumen = sum(d.series * d.repeticiones * float(d.peso_kg) for e in entrenos for d in e.detalles.all())
        volumen_por_semana.append(round(volumen, 2))

        estado = estado_por_semana.get(semana)
        if estado:
            if estado.humor_dominante == "verde":
                colores_por_semana.append("rgba(0, 255, 128, 0.6)")  # verde
            elif estado.humor_dominante == "amarillo":
                colores_por_semana.append("rgba(255, 221, 0, 0.6)")  # amarillo
            else:
                colores_por_semana.append("rgba(255, 77, 77, 0.6)")  # rojo
        else:
            colores_por_semana.append("rgba(128, 128, 128, 0.4)")  # gris

    grafico_data = {
        'labels': labels,
        'entrenos': entrenos_por_semana,
        'volumen': volumen_por_semana,
        'colores': colores_por_semana,
    }

    return render(request, 'clientes/historial.html', {
        'cliente': cliente,
        'historial_semanal': historial_semanal,
        'total_entrenos': total_entrenos,
        'promedio_semanal': promedio_semanal,
        'grafico_data': json.dumps(grafico_data),
        'estado_por_semana': estado_por_semana,
    })


def eliminar_revision(request, revision_id):
    revision = get_object_or_404(RevisionProgreso, id=revision_id)
    cliente_id = revision.cliente.id
    revision.delete()
    return redirect('lista_revisiones', cliente_id=cliente_id)


def eliminar_objetivo(request, pk):
    objetivo = get_object_or_404(ObjetivoCliente, pk=pk)
    cliente_id = objetivo.cliente.id
    objetivo.delete()
    messages.success(request, "Objetivo eliminado.")
    return redirect('detalle_cliente', cliente_id=cliente_id)


def editar_objetivo(request, pk):
    objetivo = get_object_or_404(ObjetivoCliente, pk=pk)
    cliente = objetivo.cliente

    if request.method == 'POST':
        form = ObjetivoClienteForm(request.POST, instance=objetivo, cliente=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, "Objetivo actualizado.")
            return redirect('detalle_cliente', cliente_id=cliente.id)
    else:
        form = ObjetivoClienteForm(request.POST, instance=objetivo, cliente=cliente)

    return render(request, 'clientes/definir_objetivo.html', {
        'form': form,
        'cliente': cliente,
        'editar': True
    })


def definir_objetivo(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == 'POST':
        form = ObjetivoClienteForm(request.POST, cliente=cliente)
        if form.is_valid():
            objetivo = form.save(commit=False)
            objetivo.cliente = cliente
            objetivo.save()
            messages.success(request, "Objetivo guardado.")
            return redirect('detalle_cliente', cliente_id=cliente.id)
    else:
        form = ObjetivoClienteForm()

    return render(request, 'clientes/definir_objetivo.html', {
        'form': form,
        'cliente': cliente
    })


@require_GET
def datos_comparacion(request):
    ids = request.GET.getlist('ids[]')
    medida = request.GET.get('medida', 'peso')

    campo_map = {
        'peso': 'peso_corporal',
        'grasa': 'grasa_corporal',
        'cintura': 'cintura',
    }

    campo = campo_map.get(medida, 'peso_corporal')
    data = []

    for cliente_id in ids:
        cliente = get_object_or_404(Cliente, id=cliente_id)
        revisiones = RevisionProgreso.objects.filter(cliente=cliente).order_by('fecha')
        fechas = [rev.fecha.strftime('%Y-%m-%d') for rev in revisiones]
        valores = [getattr(rev, campo) for rev in revisiones]
        data.append({
            'nombre': cliente.nombre,
            'fechas': fechas,
            'valores': valores,
        })

    return JsonResponse(data, safe=False)


def comparar_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'clientes/comparar.html', {'clientes': clientes})


@require_GET
def datos_graficas(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    revisiones = RevisionProgreso.objects.filter(cliente=cliente).order_by('fecha')

    start = request.GET.get('start')
    end = request.GET.get('end')
    if start and end:
        revisiones = revisiones.filter(fecha__range=[start, end])

    fechas = [rev.fecha.strftime('%Y-%m-%d') for rev in revisiones]

    data = {
        'fechas': fechas,
        'pesos': [rev.peso_corporal for rev in revisiones],
        'grasas': [rev.grasa_corporal for rev in revisiones],
        'cinturas': [rev.cintura for rev in revisiones],
        'pechos': [rev.pecho for rev in revisiones],
        'biceps': [rev.biceps for rev in revisiones],
        'muslos': [rev.muslos for rev in revisiones],
    }

    return JsonResponse(data)


def asignar_dieta_directo(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == 'POST':
        form = DietaAsignadaForm(request.POST)
        if form.is_valid():
            asignacion = form.save(commit=False)
            asignacion.cliente = cliente
            asignacion.save()
            return redirect('detalle_cliente', cliente_id=cliente.id)
    else:
        form = DietaAsignadaForm()

    return render(request, 'clientes/asignar_dieta.html', {'form': form, 'cliente': cliente})


def lista_revisiones(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    revisiones = cliente.revisiones.order_by('fecha')

    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    if start_date and end_date:
        revisiones = revisiones.filter(fecha__range=[start_date, end_date])

    fechas = [r.fecha.strftime('%Y-%m-%d') for r in revisiones]
    pesos = [float(r.peso_corporal) if r.peso_corporal is not None else None for r in revisiones]
    grasas = [float(r.grasa_corporal) if r.grasa_corporal is not None else None for r in revisiones]

    alerts = [r.check_alerts() for r in revisiones if r.check_alerts()]

    context = {
        'cliente': cliente,
        'revisiones': revisiones,
        'fechas': json.dumps(fechas),
        'pesos': json.dumps(pesos),
        'grasas': json.dumps(grasas),
        'alerts': alerts,
    }
    return render(request, 'clientes/lista_revisiones.html', context)


def agregar_revision(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        form = RevisionProgresoForm(request.POST)
        if form.is_valid():
            revision = form.save(commit=False)
            revision.cliente = cliente
            revision.save()
            return redirect('lista_revisiones', cliente_id=cliente.id)
    else:
        form = RevisionProgresoForm()
    return render(request, 'clientes/agregar_revision.html', {'form': form, 'cliente': cliente})


# Vista para listar medidas
def lista_medidas(request):
    medidas = Medida.objects.all()
    return render(request, 'list.html', {'medidas': medidas})


# Vista para agregar medida
def agregar_medida(request):
    if request.method == 'POST':
        form = MedidaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_medidas')
    else:
        form = MedidaForm()
    return render(request, 'form.html', {'form': form, 'titulo': 'Agregar Medida', 'volver_url': 'lista_medidas'})


# Vista principal de clientes (con programa)
def lista_clientes(request):
    clientes = Cliente.objects.select_related('programa').all()
    programas = Programa.objects.all()

    # Obtener parámetros del filtro desde la URL
    nombre = request.GET.get('nombre', '')
    programa_id = request.GET.get('programa', '')
    genero = request.GET.get('genero', '')

    # Aplicar filtros si vienen en la petición
    if nombre:
        clientes = clientes.filter(nombre__icontains=nombre)
    if programa_id:
        clientes = clientes.filter(programa_id=programa_id)
    if genero:
        clientes = clientes.filter(genero=genero)

    return render(request, 'list.html', {
        'titulo': 'Lista de Clientes',
        'objetos': clientes,
        'programas': programas,  # ✅ pasa los programas al template
        'encabezados': ['ID', 'Nombre', 'Email', 'Teléfono', 'Programa'],
        'campos': ['id', 'nombre', 'email', 'telefono', 'programa'],
        'agregar_url': 'agregar_cliente',
        'editar_url': 'editar_cliente',
        'eliminar_url': 'eliminar_cliente',
        'detalle_url': 'detalle_cliente',
    })


# Dashboard de clientes


def dashboard(request):
    clientes = Cliente.objects.all()
    total_clientes = clientes.count()
    total_revisiones = sum(cliente.revisiones.count() for cliente in clientes)
    entrenos_hoy_lista = []
    entrenos_semana_lista = []
    entrenos_mes_lista = []
    entrenos_anio_lista = []
    entrenos_todos_lista = []
    # Promedios
    promedio_peso = 0
    promedio_grasa = 0
    total_mediciones = 0

    for cliente in clientes:
        ultima = cliente.revisiones.order_by('-fecha').first()
        if ultima:
            print(f"{cliente.nombre} ({ultima.fecha}) → {ultima.check_alerts()}")
        for rev in cliente.revisiones.all():
            if rev.peso_corporal:
                promedio_peso += rev.peso_corporal
            if rev.grasa_corporal:
                promedio_grasa += rev.grasa_corporal
            total_mediciones += 1

    if total_mediciones > 0:
        promedio_peso /= total_mediciones
        promedio_grasa /= total_mediciones
        # 📊 Datos de entrenos
    from datetime import date, timedelta
    from django.db.models.functions import TruncWeek, TruncMonth, TruncYear

    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)
    inicio_anio = hoy.replace(month=1, day=1)

    entrenos_hoy = EntrenoRealizado.objects.filter(fecha=hoy).count()
    entrenos_semana = EntrenoRealizado.objects.filter(fecha__gte=inicio_semana).count()
    entrenos_mes = EntrenoRealizado.objects.filter(fecha__gte=inicio_mes).count()
    entrenos_anio = EntrenoRealizado.objects.filter(fecha__gte=inicio_anio).count()
    entrenos_total = EntrenoRealizado.objects.count()

    semanas = EntrenoRealizado.objects.annotate(semana=TruncWeek('fecha')).values('semana').distinct().count()
    meses = EntrenoRealizado.objects.annotate(mes=TruncMonth('fecha')).values('mes').distinct().count()
    anios = EntrenoRealizado.objects.annotate(anio=TruncYear('fecha')).values('anio').distinct().count()

    promedio_semanal = round(entrenos_total / semanas, 1) if semanas else 0
    promedio_mensual = round(entrenos_total / meses, 1) if meses else 0
    promedio_anual = round(entrenos_total / anios, 1) if anios else 0

    # Agrupación de alertas
    from collections import defaultdict
    alertas_raw = defaultdict(list)

    for cliente in clientes:
        ultima = cliente.revisiones.order_by('-fecha').first()
        if ultima:
            alertas = ultima.check_alerts()
            if alertas:
                for alerta in alertas:
                    alertas_raw[alerta].append((cliente, ultima.fecha))

    # Convertimos el defaultdict a dict plano
    alertas_por_tipo = dict(alertas_raw)

    context = {'alertas_por_tipo': alertas_por_tipo, }

    # Datos adicionales
    resumen_programa = Cliente.objects.values('programa__nombre').annotate(count=Count('id'))
    genero_count = Cliente.objects.values('genero').annotate(count=Count('id'))
    peso_por_genero = Cliente.objects.values('genero').annotate(avg_peso=Avg('peso_corporal'))
    registro_por_mes = (
        Cliente.objects
        .extra(select={'month': "strftime('%%m', fecha_registro)"})
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    top_peso = Cliente.objects.order_by('-peso_corporal')[:5]
    color_por_alerta = {
        "Grasa corporal alta": "danger",
        "Peso corporal muy bajo": "warning",
        # Puedes agregar más tipos aquí
    }
    alertas_por_tipo_coloreadas = []
    for tipo, clientes_lista in alertas_por_tipo.items():
        alertas_por_tipo_coloreadas.append({
            'tipo': tipo,
            'color': color_por_alerta.get(tipo, 'secondary'),
            'clientes': clientes_lista
        })
        hoy = date.today()
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        inicio_mes = hoy.replace(day=1)
        inicio_anio = hoy.replace(month=1, day=1)

        entrenos_hoy_lista = EntrenoRealizado.objects.filter(fecha=hoy).select_related('cliente', 'rutina')
        entrenos_semana_lista = EntrenoRealizado.objects.filter(fecha__gte=inicio_semana).select_related('cliente',
                                                                                                         'rutina')
        entrenos_mes_lista = EntrenoRealizado.objects.filter(fecha__gte=inicio_mes).select_related('cliente', 'rutina')
        entrenos_anio_lista = EntrenoRealizado.objects.filter(fecha__gte=inicio_anio).select_related('cliente',
                                                                                                     'rutina')
        entrenos_todos_lista = EntrenoRealizado.objects.all().select_related('cliente', 'rutina')
    context = {
        'total_clientes': total_clientes,
        'total_revisiones': total_revisiones,
        'promedio_peso': round(promedio_peso, 1),
        'promedio_grasa': round(promedio_grasa, 1),
        'alertas_por_tipo': alertas_por_tipo,
        'total_alertas': sum(len(lst) for lst in alertas_por_tipo.values()),
        'resumen_programa': resumen_programa,
        'genero_count': list(genero_count),
        'peso_por_genero': list(peso_por_genero),
        'registro_por_mes': list(registro_por_mes),
        'alertas_por_tipo': dict(alertas_raw),
        'alertas_por_tipo_coloreadas': alertas_por_tipo_coloreadas,
        'color_por_alerta': color_por_alerta,
        'top_peso': top_peso,
        'entr_hoy': entrenos_hoy,
        'entr_semana': entrenos_semana,
        'entr_mes': entrenos_mes,
        'entr_anio': entrenos_anio,
        'entr_total': entrenos_total,
        'prom_sem': promedio_semanal,
        'prom_mes': promedio_mensual,
        'prom_anio': promedio_anual,
        'entr_hoy_lista': entrenos_hoy_lista,
        'entr_semana_lista': entrenos_semana_lista,
        'entr_mes_lista': entrenos_mes_lista,
        'entr_anio_lista': entrenos_anio_lista,
        'entr_todos_lista': entrenos_todos_lista,
    }

    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)
    inicio_anio = hoy.replace(month=1, day=1)

    entrenos_hoy_lista = EntrenoRealizado.objects.filter(fecha=hoy).select_related('cliente', 'rutina')
    entrenos_semana_lista = EntrenoRealizado.objects.filter(fecha__gte=inicio_semana).select_related('cliente',
                                                                                                     'rutina')
    entrenos_mes_lista = EntrenoRealizado.objects.filter(fecha__gte=inicio_mes).select_related('cliente', 'rutina')
    entrenos_anio_lista = EntrenoRealizado.objects.filter(fecha__gte=inicio_anio).select_related('cliente', 'rutina')
    entrenos_todos_lista = EntrenoRealizado.objects.all().select_related('cliente', 'rutina')
    return render(request, 'clientes/dashboard.html', context)


# Vista detalle cliente

def detalle_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    revisiones = cliente.revisiones.order_by('fecha')
    ultima_revision = revisiones.last()
    historial = EntrenoRealizado.objects.filter(cliente=cliente).prefetch_related('detalles__ejercicio').order_by(
        '-fecha')

    historial_semanal = defaultdict(list)
    # Prepara datos para Chart.js
    labels = []
    entrenos_por_semana = []
    volumen_por_semana = []

    for semana_inicio, entrenos in historial_semanal.items():
        label = f"{semana_inicio.strftime('%d %b')}"
        labels.append(label)
        entrenos_por_semana.append(len(entrenos))

        volumen = 0
        for entreno in entrenos:
            for detalle in entreno.detalles.all():
                volumen += detalle.series * detalle.repeticiones * float(detalle.peso_kg)
        volumen_por_semana.append(round(volumen, 2))

    # Serializar para JS
    grafico_data = {
        'labels': labels,
        'entrenos': entrenos_por_semana,
        'volumen': volumen_por_semana,
    }
    from decimal import Decimal, ROUND_HALF_UP

    # total entrenos
    total_entrenos = historial.count()
    total_semanas = len(historial_semanal)

    # evitar división por 0
    if total_semanas > 0:
        promedio_semanal = Decimal(total_entrenos / total_semanas).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    else:
        promedio_semanal = Decimal("0.0")
    for entreno in historial:
        lunes = entreno.fecha - timedelta(days=entreno.fecha.weekday())  # inicio de semana
        historial_semanal[lunes].append(entreno)

    historial_semanal = dict(sorted(historial_semanal.items(), reverse=True))  # ordenar por semana

    fechas = [rev.fecha.strftime("%d/%m/%Y") for rev in revisiones]
    pesos = [float(rev.peso_corporal or 0) for rev in revisiones]
    grasas = [float(rev.grasa_corporal or 0) for rev in revisiones]
    cinturas = [float(rev.cintura or 0) for rev in revisiones]

    objetivos = cliente.objetivos.all()
    hoy = date.today()
    revisiones = RevisionProgreso.objects.filter(cliente=cliente).order_by('fecha')

    def delta_peso(dias):
        desde = hoy - timedelta(days=dias)
        recientes = revisiones.filter(fecha__gte=desde)
        if recientes.count() >= 2:
            return round(recientes.last().peso_corporal - recientes.first().peso_corporal, 1)
        return 0

    peso_7d = delta_peso(7)
    peso_30d = delta_peso(30)
    peso_90d = delta_peso(90)

    peso_total = 0
    if revisiones.count() >= 2:
        peso_total = round(revisiones.last().peso_corporal - revisiones.first().peso_corporal, 1)
    return render(request, 'clientes/detalle.html', {
        'cliente': cliente,
        'ultima_revision': ultima_revision,
        'fechas': json.dumps(fechas),
        'pesos': json.dumps(pesos),
        'grasas': json.dumps(grasas),
        'cinturas': json.dumps(cinturas),
        'objetivos': objetivos,
        'cliente': cliente,
        'today': date.today(),
        'peso_7d': peso_7d,
        'peso_30d': peso_30d,
        'peso_90d': peso_90d,
        'historial_semanal': historial_semanal,
        'total_entrenos': total_entrenos,
        'promedio_semanal': promedio_semanal,
        'grafico_data': json.dumps(grafico_data),
        'peso_total': peso_total,
    })


# Vista agregar cliente
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import ClienteForm
from .models import Cliente


def agregar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES)
        username = request.POST.get('username')
        password = request.POST.get('password')

        if form.is_valid():
            if User.objects.filter(username=username).exists():
                messages.error(request, "Ese nombre de usuario ya existe.")
            else:
                user = User.objects.create_user(username=username, password=password)
                cliente = form.save(commit=False)
                cliente.user = user
                cliente.save()
                messages.success(request, "Cliente y usuario creados correctamente.")
                return redirect('lista_clientes')  # ✅ aquí
    else:
        form = ClienteForm()

    return render(request, 'clientes/agregar.html', {
        'form': form,
        'titulo': 'Agregar Cliente',
        'volver_url': 'lista_clientes',  # ✅ y aquí
    })


# Vista editar cliente
from django.contrib.auth.models import User


def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES, instance=cliente)
        username = request.POST.get('username')
        password = request.POST.get('password')

        if form.is_valid():
            # Si ya hay usuario, actualiza username y opcionalmente contraseña
            if cliente.user:
                user = cliente.user
                user.username = username
                if password:
                    user.set_password(password)
                user.save()
            else:
                # Crear nuevo user si no tiene
                user = User.objects.create_user(username=username, password=password)
                cliente.user = user

            form.save()
            return redirect('clientes_index')
    else:
        form = ClienteForm(instance=cliente)

    return render(request, 'clientes/editar.html', {
        'form': form,
        'cliente': cliente
    })


# Vista eliminar cliente
def eliminar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        cliente.delete()
        return redirect('clientes_index')
    return render(request, 'clientes/eliminar.html', {'cliente': cliente})


# Vista home
@login_required
def home(request):
    # Si el usuario tiene perfil de cliente, renderiza el panel del cliente
    if hasattr(request.user, 'cliente_perfil'):
        recuerdo_dia = RecuerdoEmocional.objects.filter(user=request.user).order_by('-fecha').first()
        motivacion = MotivacionUsuario.objects.filter(user=request.user).last()

        context = {
            'recuerdo_dia': recuerdo_dia,
            'motivacion': motivacion,
        }
        return render(request, 'clientes/panel_cliente.html', context)

    # Si no tiene perfil de cliente, se asume que es entrenador
    return redirect('dashboard_entrenador')


# Vista index
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Cliente, RevisionProgreso
from django.utils.timezone import now
from datetime import timedelta
from joi.utils import (
    frase_motivadora_entrenador_estado,
    recuperar_frase_de_recaida,
    obtener_estado_joi,
    frase_cambio_forma_joi
)


@login_required
def panel_entrenador(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Acceso solo para entrenadores.")

    clientes = Cliente.objects.all()
    total_clientes = clientes.count()
    total_revisiones = RevisionProgreso.objects.count()

    # Alertas
    alertas = []
    for cliente in clientes:
        ultima = cliente.revisiones.order_by('-fecha').first()
        if ultima and ultima.check_alerts():
            alertas.append((cliente, ultima.check_alerts()))
    total_alertas = len(alertas)

    # Actividad reciente
    hoy = now().date()
    entrenos_semana = RevisionProgreso.objects.filter(fecha__gte=hoy - timedelta(days=7)).count()

    # Estado Joi global
    if total_alertas >= 4:
        estado_joi = "glitch"
    elif entrenos_semana == 0:
        estado_joi = "triste"
    else:
        estado_joi = "presente"

    from datetime import datetime

    # Hora actual
    hora_actual = datetime.now().hour
    if 5 <= hora_actual < 12:
        joi_momento = "mañana"
    elif 12 <= hora_actual < 18:
        joi_momento = "tarde"
    elif 18 <= hora_actual < 22:
        joi_momento = "noche"
    else:
        joi_momento = "madrugada"

    # Estación según mes
    mes = datetime.now().month
    if mes in [12, 1, 2]:
        joi_estacion = "invierno"
    elif mes in [3, 4, 5]:
        joi_estacion = "primavera"
    elif mes in [6, 7, 8]:
        joi_estacion = "verano"
    else:
        joi_estacion = "otoño"
    from joi.utils import frase_estacion_momento
    from joi.utils import frase_emocional_recaida

    if estado_joi in ["glitch", "triste"]:
        frase_recaida = frase_emocional_recaida(estado_joi)
    else:
        frase_recaida = None

    frase_estacional_joi = frase_estacion_momento(joi_estacion, joi_momento)
    frase_forma_joi = frase_cambio_forma_joi(estado_joi)
    frase_extra_joi = "Estoy observando tu impacto..." if estado_joi == "presente" else "Las señales se están acumulando..."
    frase_recaida = recuperar_frase_de_recaida(request.user) if estado_joi in ["glitch", "triste"] else None

    return render(request, 'clientes/panel_entrenador.html', {
        'clientes': clientes,
        'total_clientes': total_clientes,
        'total_revisiones': total_revisiones,
        'entrenos_hoy': RevisionProgreso.objects.filter(fecha=hoy).count(),
        'entrenos_semana': entrenos_semana,
        'alertas': alertas,

        # Joi flotante
        'estado_joi': estado_joi,
        'frase_forma_joi': frase_forma_joi,
        'frase_extra_joi': frase_extra_joi,
        'frase_recaida': frase_recaida,
        'joi_momento': joi_momento,
        'joi_estacion': joi_estacion,
        'frase_estacional_joi': frase_estacional_joi,
        'frase_recaida': frase_recaida,

    })


@login_required
def lista_clientes(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Acceso solo para entrenadores.")

    clientes = Cliente.objects.all()
    for cliente in clientes:
        cliente.ultima_revision = cliente.revisiones.order_by('-fecha').first()

    programas = Programa.objects.all()
    return render(request, 'clientes/index.html', {
        'clientes': clientes,
        'programas': programas,
        'today': date.today(),
    })


def asignar_programa_a_cliente(request, programa_id):
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        cliente = get_object_or_404(Cliente, id=cliente_id)
        programa = get_object_or_404(Programa, id=programa_id)
        cliente.programa = programa
        cliente.save()
        return redirect('detalle_programa', programa_id=programa_id)


def actualizar_recordatorio_peso(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    fecha = request.POST.get("proximo_registro_peso")
    if fecha:
        cliente.proximo_registro_peso = fecha
        cliente.save()
    return HttpResponseRedirect(reverse("detalle_cliente", args=[cliente.id]))


from django.shortcuts import render


def blade_runner_demo(request):
    return render(request, 'clientes/blade-runner-demo.html')
