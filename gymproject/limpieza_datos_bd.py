"""
Script para limpiar y corregir valores decimales problemáticos en la base de datos.
Versión mejorada que usa SQL directo para manejar casos extremos de corrupción de datos.

Este script identifica registros con valores decimales inválidos en las tablas
SerieRealizada y PlanPersonalizado, y los corrige aplicando reglas de limpieza
seguras.

Uso:
    python limpieza_datos_simplificado.py

Autor: Manus AI
Fecha: Mayo 2025
"""

import os
import sys
import django
import re
from decimal import Decimal, InvalidOperation
from django.db import connection

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymproject.settings')
django.setup()


def limpiar_valor_decimal(valor):
    """
    Limpia y convierte un valor a decimal de forma segura.

    Args:
        valor: Valor a limpiar y convertir

    Returns:
        str: Valor decimal limpio como string o '0' si no es convertible
    """
    if valor is None:
        return '0'

    try:
        # Intentar convertir directamente
        return str(Decimal(str(valor).replace(',', '.')))
    except (InvalidOperation, ValueError, TypeError):
        try:
            # Limpiar y extraer solo dígitos y punto decimal
            valor_str = str(valor).replace(',', '.')
            # Usar expresión regular para extraer un número válido
            match = re.search(r'[-+]?\d*\.?\d+', valor_str)
            if match:
                return match.group(0)
            else:
                return '0'
        except (InvalidOperation, ValueError, TypeError):
            return '0'


def limpiar_series_realizadas():
    """
    Identifica y corrige valores decimales problemáticos en SerieRealizada usando SQL directo.

    Returns:
        tuple: (registros_revisados, registros_corregidos)
    """
    print("\n=== Limpiando tabla SerieRealizada ===")
    registros_revisados = 0
    registros_corregidos = 0

    with connection.cursor() as cursor:
        # Obtener todas las series
        cursor.execute("SELECT id, peso_kg FROM entrenos_serierealizada")
        series = cursor.fetchall()
        total_series = len(series)
        print(f"Total de series a revisar: {total_series}")

        for serie_id, peso_kg in series:
            registros_revisados += 1

            # Mostrar progreso cada 100 registros
            if registros_revisados % 100 == 0:
                print(f"Progreso: {registros_revisados}/{total_series} series revisadas")

            # Intentar convertir a decimal para verificar si es válido
            try:
                if peso_kg is not None:
                    Decimal(str(peso_kg))
                # Si no lanza excepción, el valor es válido
            except (InvalidOperation, ValueError, TypeError):
                # Valor inválido, corregirlo
                valor_original = peso_kg
                valor_corregido = limpiar_valor_decimal(valor_original)

                # Actualizar en la base de datos
                cursor.execute(
                    "UPDATE entrenos_serierealizada SET peso_kg = %s WHERE id = %s",
                    [valor_corregido, serie_id]
                )
                registros_corregidos += 1
                print(f"  Corregido: Serie {serie_id} - peso_kg: '{valor_original}' -> '{valor_corregido}'")

    print(f"Series revisadas: {registros_revisados}")
    print(f"Series corregidas: {registros_corregidos}")
    return registros_revisados, registros_corregidos


def limpiar_planes_personalizados():
    """
    Identifica y corrige valores decimales problemáticos en PlanPersonalizado usando SQL directo.

    Returns:
        tuple: (registros_revisados, registros_corregidos)
    """
    print("\n=== Limpiando tabla PlanPersonalizado ===")
    registros_revisados = 0
    registros_corregidos = 0

    with connection.cursor() as cursor:
        # Obtener todos los planes
        cursor.execute("SELECT id, peso_objetivo FROM entrenos_planpersonalizado")
        planes = cursor.fetchall()
        total_planes = len(planes)
        print(f"Total de planes a revisar: {total_planes}")

        for plan_id, peso_objetivo in planes:
            registros_revisados += 1

            # Mostrar progreso cada 100 registros
            if registros_revisados % 100 == 0:
                print(f"Progreso: {registros_revisados}/{total_planes} planes revisados")

            # Intentar convertir a decimal para verificar si es válido
            try:
                if peso_objetivo is not None:
                    Decimal(str(peso_objetivo))
                # Si no lanza excepción, el valor es válido
            except (InvalidOperation, ValueError, TypeError):
                # Valor inválido, corregirlo
                valor_original = peso_objetivo
                valor_corregido = limpiar_valor_decimal(valor_original)

                # Actualizar en la base de datos
                cursor.execute(
                    "UPDATE entrenos_planpersonalizado SET peso_objetivo = %s WHERE id = %s",
                    [valor_corregido, plan_id]
                )
                registros_corregidos += 1
                print(f"  Corregido: Plan {plan_id} - peso_objetivo: '{valor_original}' -> '{valor_corregido}'")

    print(f"Planes revisados: {registros_revisados}")
    print(f"Planes corregidos: {registros_corregidos}")
    return registros_revisados, registros_corregidos


def limpiar_rutina_ejercicios():
    """
    Identifica y corrige valores decimales problemáticos en RutinaEjercicio usando SQL directo.

    Returns:
        tuple: (registros_revisados, registros_corregidos)
    """
    print("\n=== Limpiando tabla RutinaEjercicio ===")
    registros_revisados = 0
    registros_corregidos = 0

    with connection.cursor() as cursor:
        # Obtener todos los ejercicios
        cursor.execute("SELECT id, peso_kg FROM rutinas_rutinaejercicio")
        ejercicios = cursor.fetchall()
        total_ejercicios = len(ejercicios)
        print(f"Total de ejercicios a revisar: {total_ejercicios}")

        for ejercicio_id, peso_kg in ejercicios:
            registros_revisados += 1

            # Mostrar progreso cada 100 registros
            if registros_revisados % 100 == 0:
                print(f"Progreso: {registros_revisados}/{total_ejercicios} ejercicios revisados")

            # Intentar convertir a decimal para verificar si es válido
            try:
                if peso_kg is not None:
                    Decimal(str(peso_kg))
                # Si no lanza excepción, el valor es válido
            except (InvalidOperation, ValueError, TypeError):
                # Valor inválido, corregirlo
                valor_original = peso_kg
                valor_corregido = limpiar_valor_decimal(valor_original)

                # Actualizar en la base de datos
                cursor.execute(
                    "UPDATE rutinas_rutinaejercicio SET peso_kg = %s WHERE id = %s",
                    [valor_corregido, ejercicio_id]
                )
                registros_corregidos += 1
                print(f"  Corregido: Ejercicio {ejercicio_id} - peso_kg: '{valor_original}' -> '{valor_corregido}'")

    print(f"Ejercicios revisados: {registros_revisados}")
    print(f"Ejercicios corregidos: {registros_corregidos}")
    return registros_revisados, registros_corregidos


def identificar_entrenos_problematicos():
    """
    Identifica entrenos con series que tienen valores decimales problemáticos usando SQL directo.

    Returns:
        list: Lista de IDs de entrenos con problemas
    """
    print("\n=== Identificando entrenos problemáticos ===")
    entrenos_problematicos = set()

    with connection.cursor() as cursor:
        # Obtener series con valores decimales potencialmente inválidos
        cursor.execute("""
            SELECT sr.entreno_id, sr.id, sr.peso_kg, e.fecha, c.nombre
            FROM entrenos_serierealizada sr
            JOIN entrenos_entrenorealizado e ON sr.entreno_id = e.id
            JOIN clientes_cliente c ON e.cliente_id = c.id
        """)
        series = cursor.fetchall()

        for entreno_id, serie_id, peso_kg, fecha, cliente_nombre in series:
            # Intentar convertir a decimal para verificar si es válido
            try:
                if peso_kg is not None:
                    Decimal(str(peso_kg))
                # Si no lanza excepción, el valor es válido
            except (InvalidOperation, ValueError, TypeError):
                entrenos_problematicos.add((entreno_id, fecha, cliente_nombre))

    if entrenos_problematicos:
        print(f"Se encontraron {len(entrenos_problematicos)} entrenos con series problemáticas:")
        for entreno_id, fecha, cliente_nombre in entrenos_problematicos:
            print(f"  - Entreno {entreno_id} de {cliente_nombre} ({fecha})")
    else:
        print("No se encontraron entrenos con series problemáticas")

    return [entreno_id for entreno_id, _, _ in entrenos_problematicos]


def main():
    """
    Función principal que ejecuta la limpieza de datos.
    """
    print("=== LIMPIEZA DE DATOS DE LA BASE DE DATOS ===")
    print("Este script corregirá valores decimales problemáticos en la base de datos.")

    try:
        # Identificar entrenos problemáticos antes de la limpieza
        print("Identificando entrenos problemáticos antes de la limpieza...")
        entrenos_problematicos_antes = identificar_entrenos_problematicos()

        # Limpiar tablas
        series_revisadas, series_corregidas = limpiar_series_realizadas()
        planes_revisados, planes_corregidos = limpiar_planes_personalizados()
        ejercicios_revisados, ejercicios_corregidos = limpiar_rutina_ejercicios()

        # Identificar entrenos problemáticos después de la limpieza
        print("Identificando entrenos problemáticos después de la limpieza...")
        entrenos_problematicos_despues = identificar_entrenos_problematicos()

        # Resumen final
        print("\n=== RESUMEN DE LIMPIEZA ===")
        print(f"Series revisadas: {series_revisadas}, corregidas: {series_corregidas}")
        print(f"Planes revisados: {planes_revisados}, corregidos: {planes_corregidos}")
        print(f"Ejercicios revisados: {ejercicios_revisados}, corregidos: {ejercicios_corregidos}")
        print(f"Entrenos problemáticos antes: {len(entrenos_problematicos_antes)}")
        print(f"Entrenos problemáticos después: {len(entrenos_problematicos_despues)}")

        if len(entrenos_problematicos_despues) == 0:
            print("\n✅ LIMPIEZA COMPLETADA CON ÉXITO")
            print("Todos los valores decimales en la base de datos son ahora válidos.")
        else:
            print("\n⚠️ LIMPIEZA PARCIAL")
            print("Algunos valores decimales siguen siendo inválidos. Se recomienda revisar manualmente.")

    except Exception as e:
        print(f"\n❌ ERROR DURANTE LA LIMPIEZA: {str(e)}")
        print("Se recomienda revisar el error y volver a intentar.")


if __name__ == "__main__":
    main()
