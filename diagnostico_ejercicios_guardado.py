from entrenos.models import EntrenoRealizado
from entrenos.utils import parsear_ejercicios
from datetime import datetime, timedelta

cliente_id = 1
fecha_limite = datetime.now().date() - timedelta(days=30)

entrenos = EntrenoRealizado.objects.filter(
    cliente_id=cliente_id,
    fecha__gte=fecha_limite
).exclude(notas_liftin__isnull=True).exclude(notas_liftin='')

output_lines = []
output_lines.append(f"Analisis de entrenamientos del cliente {cliente_id} desde {fecha_limite}\n")

for entreno in entrenos:
    ejercicios = parsear_ejercicios(entreno.notas_liftin)
    output_lines.append(f"Entreno {entreno.fecha}:")
    for ej in ejercicios:
        nombre = ej.get("nombre", "").strip()
        peso = ej.get("peso", "")
        reps_raw = ej.get("repeticiones", "")
        try:
            peso_val = float(peso) if peso != "PC" else 0
            reps = int(reps_raw.lower().replace('×', 'x').split('x')[-1]) if 'x' in reps_raw else int(reps_raw)
        except:
            output_lines.append(f" - Ignorado: {nombre} (peso={peso}, reps={reps_raw}) - Formato invalido")
            continue

        if reps > 12:
            output_lines.append(f" - {nombre} - Reps {reps} mayores a 12: descartado")
        elif peso_val == 0 and nombre.lower() != "dominadas":
            output_lines.append(f" - {nombre} - Peso 0: descartado (excepto dominadas)")
        elif nombre.strip() == "":
            output_lines.append(f" - Sin nombre: descartado")
        else:
            output_lines.append(f" + {nombre} - peso: {peso_val}, reps: {reps}")
    output_lines.append("")

# Mostrar en pantalla
for line in output_lines:
    print(line)

# Guardar en archivo
with open("diagnostico_resultado.txt", "w", encoding="utf-8") as f:
    for line in output_lines:
        f.write(line + "\n")
