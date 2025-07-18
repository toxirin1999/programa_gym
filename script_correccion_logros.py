#!/usr/bin/env python3
"""
Script de Corrección de Datos del Sistema de Logros
==================================================

Este script corrige las inconsistencias en el sistema de logros:
1. Recalcula los puntos totales reales desde LogroUsuario
2. Sincroniza el PerfilGamificacion
3. Corrige los niveles basándose en los puntos reales
4. Actualiza el progreso de logros pendientes

Uso:
    python script_correccion_logros.py

Nota: Este script debe ejecutarse desde el directorio del proyecto Django
con el entorno virtual activado.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_project.settings')
django.setup()

from django.db import transaction
from django.db.models import Sum
from logros.models import PerfilGamificacion, LogroUsuario, Nivel, Logro
from clientes.models import Cliente
from entrenos.models import EntrenoRealizado

def corregir_datos_logros():
    """
    Función principal que corrige todos los datos de logros
    """
    print("=" * 60)
    print("INICIANDO CORRECCIÓN DE DATOS DEL SISTEMA DE LOGROS")
    print("=" * 60)
    
    # Obtener todos los perfiles de gamificación
    perfiles = PerfilGamificacion.objects.all()
    print(f"Perfiles encontrados: {perfiles.count()}")
    
    if perfiles.count() == 0:
        print("No se encontraron perfiles de gamificación.")
        return
    
    with transaction.atomic():
        for perfil in perfiles:
            print(f"\n--- Procesando perfil de: {perfil.cliente.nombre} ---")
            
            # 1. Recalcular puntos totales reales
            puntos_reales = LogroUsuario.objects.filter(
                perfil=perfil,
                completado=True
            ).aggregate(
                total=Sum('logro__puntos_recompensa')
            )['total'] or 0
            
            print(f"Puntos en BD: {perfil.puntos_totales}")
            print(f"Puntos reales calculados: {puntos_reales}")
            
            if perfil.puntos_totales != puntos_reales:
                print(f"  ⚠️  INCONSISTENCIA DETECTADA: {perfil.puntos_totales} -> {puntos_reales}")
                perfil.puntos_totales = puntos_reales
                print(f"  ✅ Puntos corregidos")
            else:
                print(f"  ✅ Puntos ya están correctos")
            
            # 2. Recalcular entrenamientos totales
            entrenamientos_reales = EntrenoRealizado.objects.filter(
                cliente=perfil.cliente
            ).count()
            
            print(f"Entrenamientos en perfil: {perfil.entrenos_totales}")
            print(f"Entrenamientos reales: {entrenamientos_reales}")
            
            if perfil.entrenos_totales != entrenamientos_reales:
                print(f"  ⚠️  INCONSISTENCIA EN ENTRENAMIENTOS: {perfil.entrenos_totales} -> {entrenamientos_reales}")
                perfil.entrenos_totales = entrenamientos_reales
                print(f"  ✅ Entrenamientos corregidos")
            else:
                print(f"  ✅ Entrenamientos ya están correctos")
            
            # 3. Corregir nivel basándose en puntos reales
            nivel_correcto = calcular_nivel_correcto(puntos_reales)
            
            if perfil.nivel_actual is None or perfil.nivel_actual.numero != nivel_correcto['numero']:
                nivel_obj, created = Nivel.objects.get_or_create(
                    numero=nivel_correcto['numero'],
                    defaults={
                        'nombre': nivel_correcto['nombre'],
                        'puntos_requeridos': nivel_correcto['puntos_requeridos']
                    }
                )
                
                print(f"Nivel en BD: {perfil.nivel_actual.numero if perfil.nivel_actual else 'None'}")
                print(f"Nivel correcto: {nivel_correcto['numero']}")
                print(f"  ⚠️  INCONSISTENCIA EN NIVEL: -> Nivel {nivel_correcto['numero']}")
                
                perfil.nivel_actual = nivel_obj
                print(f"  ✅ Nivel corregido")
            else:
                print(f"  ✅ Nivel ya está correcto: {perfil.nivel_actual.numero}")
            
            # 4. Guardar cambios
            perfil.save()
            
            # 5. Mostrar resumen del perfil corregido
            logros_completados = LogroUsuario.objects.filter(
                perfil=perfil, 
                completado=True
            ).count()
            
            print(f"  📊 RESUMEN FINAL:")
            print(f"     - Puntos totales: {perfil.puntos_totales}")
            print(f"     - Logros completados: {logros_completados}")
            print(f"     - Nivel: {perfil.nivel_actual.numero} ({perfil.nivel_actual.nombre})")
            print(f"     - Entrenamientos: {perfil.entrenos_totales}")
            print(f"     - Racha actual: {perfil.racha_actual}")
    
    print("\n" + "=" * 60)
    print("CORRECCIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 60)

def calcular_nivel_correcto(puntos_totales):
    """
    Calcula el nivel correcto basándose en los puntos totales
    Sistema: cada 1000 puntos = 1 nivel
    """
    if puntos_totales < 1000:
        nivel_numero = 1
        puntos_requeridos = 0
    else:
        nivel_numero = (puntos_totales // 1000) + 1
        puntos_requeridos = (nivel_numero - 1) * 1000
    
    # Nombres de niveles
    nombres_niveles = {
        1: 'Principiante',
        2: 'Novato', 
        3: 'Intermedio',
        4: 'Avanzado',
        5: 'Experto',
        6: 'Maestro',
        7: 'Leyenda'
    }
    
    nombre = nombres_niveles.get(nivel_numero, f'Leyenda Nivel {nivel_numero}')
    
    return {
        'numero': nivel_numero,
        'nombre': nombre,
        'puntos_requeridos': puntos_requeridos
    }

def verificar_logros_pendientes():
    """
    Verifica y muestra información sobre logros pendientes
    """
    print("\n" + "=" * 60)
    print("VERIFICANDO LOGROS PENDIENTES")
    print("=" * 60)
    
    perfiles = PerfilGamificacion.objects.all()
    
    for perfil in perfiles:
        print(f"\n--- Logros pendientes para: {perfil.cliente.nombre} ---")
        
        # Obtener logros que el usuario NO ha completado
        logros_pendientes = Logro.objects.exclude(
            usuarios__perfil=perfil,
            usuarios__completado=True
        )
        
        print(f"Logros pendientes: {logros_pendientes.count()}")
        
        # Mostrar los primeros 3 logros pendientes con su progreso
        for logro in logros_pendientes[:3]:
            progreso_actual = calcular_progreso_logro(perfil, logro)
            porcentaje = (progreso_actual / logro.meta_valor) * 100 if logro.meta_valor > 0 else 0
            
            print(f"  📋 {logro.nombre}")
            print(f"     Progreso: {progreso_actual}/{logro.meta_valor} ({porcentaje:.1f}%)")
            print(f"     Recompensa: {logro.puntos_recompensa} puntos")

def calcular_progreso_logro(perfil, logro):
    """
    Calcula el progreso actual para un logro específico
    """
    cliente = perfil.cliente
    nombre_logro = logro.nombre.lower()
    
    try:
        # Logros de entrenamientos de Liftin
        if "liftin" in nombre_logro:
            if "principiante" in nombre_logro:
                return EntrenoRealizado.objects.filter(
                    cliente=cliente, 
                    fuente_datos='liftin'
                ).count()
        
        # Logros de calorías
        if "quemador" in nombre_logro or "calorias" in nombre_logro:
            # Buscar el valor objetivo en el nombre o usar meta_valor
            if "300" in nombre_logro or logro.meta_valor == 300:
                return EntrenoRealizado.objects.filter(
                    cliente=cliente,
                    calorias_quemadas__gte=300
                ).count()
        
        # Logros de entrenamientos generales
        if "hito" in nombre_logro or "entrenamientos" in nombre_logro:
            return perfil.entrenos_totales
        
        # Logros de racha
        if "racha" in nombre_logro:
            return perfil.racha_actual
            
    except Exception as e:
        print(f"Error calculando progreso para {logro.nombre}: {e}")
        return 0
    
    return 0

def mostrar_estadisticas_generales():
    """
    Muestra estadísticas generales del sistema de logros
    """
    print("\n" + "=" * 60)
    print("ESTADÍSTICAS GENERALES DEL SISTEMA")
    print("=" * 60)
    
    total_perfiles = PerfilGamificacion.objects.count()
    total_logros = Logro.objects.count()
    total_logros_completados = LogroUsuario.objects.filter(completado=True).count()
    
    print(f"📊 Perfiles de gamificación: {total_perfiles}")
    print(f"🏆 Logros disponibles: {total_logros}")
    print(f"✅ Logros completados (total): {total_logros_completados}")
    
    if total_perfiles > 0:
        promedio_logros = total_logros_completados / total_perfiles
        print(f"📈 Promedio de logros por usuario: {promedio_logros:.1f}")
    
    # Top 3 usuarios con más puntos
    top_usuarios = PerfilGamificacion.objects.order_by('-puntos_totales')[:3]
    print(f"\n🥇 TOP 3 USUARIOS CON MÁS PUNTOS:")
    for i, perfil in enumerate(top_usuarios, 1):
        logros_count = LogroUsuario.objects.filter(perfil=perfil, completado=True).count()
        print(f"  {i}. {perfil.cliente.nombre}: {perfil.puntos_totales} puntos ({logros_count} logros)")

if __name__ == "__main__":
    try:
        print("Iniciando script de corrección de logros...")
        
        # 1. Corregir datos inconsistentes
        corregir_datos_logros()
        
        # 2. Verificar logros pendientes
        verificar_logros_pendientes()
        
        # 3. Mostrar estadísticas generales
        mostrar_estadisticas_generales()
        
        print(f"\n🎉 ¡Script completado exitosamente!")
        print(f"💡 Ahora puedes refrescar tu dashboard para ver los datos corregidos.")
        
    except Exception as e:
        print(f"❌ Error ejecutando el script: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

