# ============================
# SCRIPT DE SINCRONIZACIÓN DE DATOS DE LOGROS
# Versión: 1.0 - Corrige inconsistencias
# ============================

"""
Script para sincronizar los datos de logros y corregir inconsistencias
detectadas en el análisis del sistema.

PROBLEMAS DETECTADOS:
- Puntos en perfil: 600, Puntos reales: 1000 (diferencia: -400)
- Entrenamientos en perfil: 1, Entrenamientos reales: 3 (diferencia: -2)

SOLUCIONES:
- Recalcular puntos totales basado en logros desbloqueados
- Actualizar contador de entrenamientos
- Verificar integridad de datos
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymproject.settings')
django.setup()

from django.db.models import Sum, Count
from logros.models import PerfilGamificacion, LogroUsuario, Logro
from entrenos.models import EntrenoRealizado
from clientes.models import Cliente

def sincronizar_perfil_cliente(cliente_id):
    """
    Sincroniza los datos de un cliente específico
    """
    print(f"\n🔄 Sincronizando datos del cliente ID: {cliente_id}")
    
    try:
        # Obtener cliente y perfil
        cliente = Cliente.objects.get(id=cliente_id)
        perfil = PerfilGamificacion.objects.filter(cliente=cliente).first()
        
        if not perfil:
            print(f"❌ No se encontró perfil de gamificación para cliente {cliente.nombre}")
            return False
        
        print(f"👤 Cliente: {cliente.nombre}")
        print(f"📊 Estado actual del perfil:")
        print(f"   - Puntos totales: {perfil.puntos_totales}")
        print(f"   - Entrenamientos totales: {perfil.entrenos_totales}")
        print(f"   - Racha actual: {perfil.racha_actual}")
        print(f"   - Racha máxima: {perfil.racha_maxima}")
        
        # Calcular datos reales
        print(f"\n🔍 Calculando datos reales...")
        
        # 1. Puntos reales basados en logros desbloqueados
        logros_desbloqueados = LogroUsuario.objects.filter(
            perfil=perfil,
            completado=True
        )
        
        puntos_reales = logros_desbloqueados.aggregate(
            total=Sum('logro__puntos_recompensa')
        )['total'] or 0
        
        # 2. Entrenamientos reales
        entrenamientos_reales = EntrenoRealizado.objects.filter(
            cliente=cliente
        ).count()
        
        # 3. Entrenamientos de Liftin
        entrenamientos_liftin = EntrenoRealizado.objects.filter(
            cliente=cliente,
            fuente_datos='liftin'
        ).count()
        
        print(f"📈 Datos calculados:")
        print(f"   - Puntos reales: {puntos_reales}")
        print(f"   - Entrenamientos reales: {entrenamientos_reales}")
        print(f"   - Entrenamientos Liftin: {entrenamientos_liftin}")
        print(f"   - Logros desbloqueados: {logros_desbloqueados.count()}")
        
        # Mostrar diferencias
        print(f"\n📊 Diferencias detectadas:")
        diff_puntos = puntos_reales - perfil.puntos_totales
        diff_entrenamientos = entrenamientos_reales - perfil.entrenos_totales
        
        print(f"   - Puntos: {diff_puntos:+d} ({perfil.puntos_totales} -> {puntos_reales})")
        print(f"   - Entrenamientos: {diff_entrenamientos:+d} ({perfil.entrenos_totales} -> {entrenamientos_reales})")
        
        # Actualizar perfil
        print(f"\n✅ Actualizando perfil...")
        perfil.puntos_totales = puntos_reales
        perfil.entrenos_totales = entrenamientos_reales
        perfil.save()
        
        print(f"✅ Perfil actualizado exitosamente")
        
        # Mostrar logros desbloqueados
        print(f"\n🏆 Logros desbloqueados ({logros_desbloqueados.count()}):")
        for logro_usuario in logros_desbloqueados:
            print(f"   - {logro_usuario.logro.nombre}: +{logro_usuario.logro.puntos_recompensa} puntos")
        
        return True
        
    except Cliente.DoesNotExist:
        print(f"❌ Cliente con ID {cliente_id} no encontrado")
        return False
    except Exception as e:
        print(f"❌ Error sincronizando cliente {cliente_id}: {str(e)}")
        return False


def sincronizar_todos_los_perfiles():
    """
    Sincroniza todos los perfiles de gamificación
    """
    print("🚀 Iniciando sincronización de todos los perfiles...")
    
    perfiles = PerfilGamificacion.objects.all()
    print(f"📊 Encontrados {perfiles.count()} perfiles")
    
    exitosos = 0
    errores = 0
    
    for perfil in perfiles:
        if sincronizar_perfil_cliente(perfil.cliente.id):
            exitosos += 1
        else:
            errores += 1
    
    print(f"\n📈 Resumen de sincronización:")
    print(f"   - Exitosos: {exitosos}")
    print(f"   - Errores: {errores}")
    print(f"   - Total: {perfiles.count()}")


def verificar_integridad_datos():
    """
    Verifica la integridad de los datos de logros
    """
    print("\n🔍 Verificando integridad de datos...")
    
    # Verificar perfiles sin cliente
    perfiles_huerfanos = PerfilGamificacion.objects.filter(cliente__isnull=True)
    if perfiles_huerfanos.exists():
        print(f"⚠️  Encontrados {perfiles_huerfanos.count()} perfiles sin cliente")
    
    # Verificar logros sin perfil
    logros_huerfanos = LogroUsuario.objects.filter(perfil__isnull=True)
    if logros_huerfanos.exists():
        print(f"⚠️  Encontrados {logros_huerfanos.count()} logros sin perfil")
    
    # Verificar logros con puntos negativos
    logros_negativos = Logro.objects.filter(puntos_recompensa__lt=0)
    if logros_negativos.exists():
        print(f"⚠️  Encontrados {logros_negativos.count()} logros con puntos negativos")
    
    # Verificar perfiles con puntos negativos
    perfiles_negativos = PerfilGamificacion.objects.filter(puntos_totales__lt=0)
    if perfiles_negativos.exists():
        print(f"⚠️  Encontrados {perfiles_negativos.count()} perfiles con puntos negativos")
    
    print("✅ Verificación de integridad completada")


def mostrar_estadisticas_generales():
    """
    Muestra estadísticas generales del sistema de logros
    """
    print("\n📊 ESTADÍSTICAS GENERALES DEL SISTEMA DE LOGROS")
    print("=" * 50)
    
    # Perfiles
    total_perfiles = PerfilGamificacion.objects.count()
    print(f"👥 Total de perfiles: {total_perfiles}")
    
    # Logros
    total_logros = Logro.objects.count()
    logros_desbloqueados = LogroUsuario.objects.filter(completado=True).count()
    print(f"🏆 Logros disponibles: {total_logros}")
    print(f"🎯 Logros desbloqueados: {logros_desbloqueados}")
    
    # Puntos
    puntos_totales = PerfilGamificacion.objects.aggregate(
        total=Sum('puntos_totales')
    )['total'] or 0
    print(f"💎 Puntos totales en el sistema: {puntos_totales}")
    
    # Entrenamientos
    entrenamientos_totales = EntrenoRealizado.objects.count()
    entrenamientos_liftin = EntrenoRealizado.objects.filter(fuente_datos='liftin').count()
    print(f"🏋️  Total entrenamientos: {entrenamientos_totales}")
    print(f"📱 Entrenamientos Liftin: {entrenamientos_liftin}")
    
    # Top clientes por puntos
    print(f"\n🏆 TOP 5 CLIENTES POR PUNTOS:")
    top_clientes = PerfilGamificacion.objects.select_related('cliente').order_by('-puntos_totales')[:5]
    for i, perfil in enumerate(top_clientes, 1):
        print(f"   {i}. {perfil.cliente.nombre}: {perfil.puntos_totales} puntos")


def main():
    """
    Función principal del script
    """
    print("🚀 SCRIPT DE SINCRONIZACIÓN DE DATOS DE LOGROS")
    print("=" * 50)
    
    # Mostrar estadísticas iniciales
    mostrar_estadisticas_generales()
    
    # Verificar integridad
    verificar_integridad_datos()
    
    # Sincronizar cliente específico (ID: 1 basado en el análisis)
    print(f"\n🎯 SINCRONIZACIÓN ESPECÍFICA - CLIENTE ID: 1")
    print("=" * 50)
    sincronizar_perfil_cliente(1)
    
    # Opción para sincronizar todos
    respuesta = input("\n¿Deseas sincronizar TODOS los perfiles? (s/N): ")
    if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        sincronizar_todos_los_perfiles()
    
    # Mostrar estadísticas finales
    print(f"\n📊 ESTADÍSTICAS FINALES")
    print("=" * 50)
    mostrar_estadisticas_generales()
    
    print(f"\n✅ Sincronización completada exitosamente!")


if __name__ == "__main__":
    main()

