# Script para ejecutar una sola vez
def migrar_clientes_existentes():
    clientes = Cliente.objects.filter(dias_disponibles__isnull=True)

    for cliente in clientes:
        # Valores por defecto basados en experiencia
        if cliente.experiencia_años < 1:
            cliente.dias_disponibles = 3
            cliente.tiempo_por_sesion = 60
        elif cliente.experiencia_años < 3:
            cliente.dias_disponibles = 4
            cliente.tiempo_por_sesion = 75
        else:
            cliente.dias_disponibles = 5
            cliente.tiempo_por_sesion = 90

        # Valores estándar de autorregulación
        cliente.nivel_estres = 5
        cliente.calidad_sueño = 7
        cliente.nivel_energia = 7
        cliente.flexibilidad_horario = True

        cliente.save()

    print(f"Migrados {clientes.count()} clientes")
