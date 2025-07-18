from entrenos.models import EntrenoRealizado
from entrenos.utils import parsear_ejercicios
from datetime import datetime, timedelta

cliente_id = 1  # Cambia si es necesario
fecha_limite = datetime.now().date() - timedelta(days=30)

entrenos = EntrenoRealizado.objects.filter(
    cliente_id=cliente_id,
    fecha__gte=fecha_limite
).exclude(notas_liftin__isnull=True).exclude(notas_liftin='')

print(f"Analizando entrenamientos del cliente {cliente_id} desde {fecha_limite}\n")

for entreno in entrenos:
    ejercicios = parsear_ejercicios(entreno.notas_liftin)
    print(f"Entreno {entreno.fecha}:")
    for ej in ejercicios:
        nombre = ej.get("nombre", "").strip()
        peso = ej.get("peso", "")
        reps_raw = ej.get("repeticiones", "")
        try:
            peso_val = float(peso) if peso != "PC" else 0
            reps = int(reps_raw.lower().replace('×', 'x').split('x')[-1]) if 'x' in reps_raw else int(reps_raw)
        except:
            print(f" - Ignorado: {nombre} (peso={peso}, reps={reps_raw}) - Formato inválido")
            continue

        if reps > 12:
            print(f" - {nombre} - Reps {reps} > 12 → descartado")
        elif peso_val == 0 and nombre.lower() != "dominadas":
            print(f" - {nombre} - Peso 0 → descartado (excepto dominadas)")
        elif nombre.strip() == "":
            print(f" - Sin nombre → descartado")
        else:
            print(f" + {nombre} - peso: {peso_val}, reps: {reps}")
    print("")
