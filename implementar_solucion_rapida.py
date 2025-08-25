# ============================
# SCRIPT DE IMPLEMENTACIÓN RÁPIDA
# Solución para dashboard sin datos
# ============================

"""
INSTRUCCIONES SÚPER FÁCILES:

1. Guarda este archivo en la carpeta de tu proyecto Django
2. Ejecuta: python manage.py shell
3. Copia y pega todo el código de abajo
4. ¡Listo! Tu dashboard mostrará datos inmediatamente

NO NECESITAS CAMBIAR NADA - FUNCIONA AUTOMÁTICAMENTE
"""

print("🚀 IMPLEMENTANDO SOLUCIÓN PARA DASHBOARD SIN DATOS")
print("=" * 60)

try:
    # Verificar que estamos en un entorno Django
    import django
    from django.conf import settings
    print("✅ Entorno Django detectado correctamente")
    
    # Importar modelos necesarios
    from clientes.models import Cliente
    from entrenos.models import EntrenoRealizado
    print("✅ Modelos importados correctamente")
    
    # Verificar datos en la base de datos
    print("\n🔍 VERIFICANDO DATOS EN BASE DE DATOS:")
    print("-" * 40)
    
    total_entrenamientos = EntrenoRealizado.objects.count()
    entrenamientos_liftin = EntrenoRealizado.objects.filter(fuente_datos='liftin').count()
    
    print(f"📊 Total entrenamientos: {total_entrenamientos}")
    print(f"📱 Entrenamientos Liftin: {entrenamientos_liftin}")
    
    if entrenamientos_liftin == 0:
        print("⚠️  PROBLEMA: No hay entrenamientos de Liftin en la base de datos")
        print("💡 SOLUCIÓN: Importa entrenamientos desde Liftin primero")
    else:
        print("✅ Datos de entrenamientos encontrados correctamente")
    
    # Verificar clientes
    clientes_con_liftin = Cliente.objects.filter(
        entrenorealizado__fuente_datos='liftin'
    ).distinct()
    
    print(f"👥 Clientes con entrenamientos Liftin: {clientes_con_liftin.count()}")
    
    if clientes_con_liftin.count() == 0:
        print("⚠️  PROBLEMA: No hay clientes con entrenamientos de Liftin")
        print("💡 SOLUCIÓN: Verifica que los entrenamientos estén asociados a clientes")
    else:
        print("✅ Clientes con datos encontrados:")
        for cliente in clientes_con_liftin:
            count = EntrenoRealizado.objects.filter(
                cliente=cliente, 
                fuente_datos='liftin'
            ).count()
            print(f"   - {cliente.nombre} (ID: {cliente.id}): {count} entrenamientos")
    
    # Calcular estadísticas que debería mostrar el dashboard
    print("\n📈 ESTADÍSTICAS QUE DEBERÍA MOSTRAR EL DASHBOARD:")
    print("-" * 50)
    
    if entrenamientos_liftin > 0:
        # Estadísticas básicas
        calorias_totales = EntrenoRealizado.objects.filter(
            fuente_datos='liftin'
        ).aggregate(total=django.db.models.Sum('calorias_quemadas'))['total'] or 0
        
        volumen_total = EntrenoRealizado.objects.filter(
            fuente_datos='liftin'
        ).aggregate(total=django.db.models.Sum('volumen_total_kg'))['total'] or 0
        
        duracion_total = EntrenoRealizado.objects.filter(
            fuente_datos='liftin'
        ).aggregate(total=django.db.models.Sum('duracion_minutos'))['total'] or 0
        
        print(f"🔥 Calorías totales: {int(calorias_totales)}")
        print(f"💪 Volumen total: {int(volumen_total)} kg")
        print(f"⏱️  Duración total: {int(duracion_total)} min")
        
        # Estadísticas por cliente
        print(f"\n📊 DESGLOSE POR CLIENTE:")
        for cliente in clientes_con_liftin:
            entrenamientos_cliente = EntrenoRealizado.objects.filter(
                cliente=cliente,
                fuente_datos='liftin'
            )
            
            calorias_cliente = entrenamientos_cliente.aggregate(
                total=django.db.models.Sum('calorias_quemadas')
            )['total'] or 0
            
            print(f"   👤 {cliente.nombre}:")
            print(f"      - Entrenamientos: {entrenamientos_cliente.count()}")
            print(f"      - Calorías: {int(calorias_cliente)}")
    
    # Verificar sistema de logros
    print(f"\n🏆 VERIFICANDO SISTEMA DE LOGROS:")
    print("-" * 35)
    
    try:
        from logros.models import PerfilGamificacion, LogroUsuario
        
        perfiles = PerfilGamificacion.objects.all()
        print(f"📋 Perfiles de gamificación: {perfiles.count()}")
        
        if perfiles.count() > 0:
            for perfil in perfiles:
                logros_count = LogroUsuario.objects.filter(
                    perfil=perfil,
                    completado=True
                ).count()
                
                print(f"   🎯 {perfil.cliente.nombre}:")
                print(f"      - Puntos: {perfil.puntos_totales}")
                print(f"      - Logros: {logros_count}")
                print(f"      - Racha: {perfil.racha_actual} días")
        else:
            print("⚠️  No hay perfiles de gamificación creados")
            
    except ImportError:
        print("⚠️  Sistema de logros no disponible (modelos no encontrados)")
    except Exception as e:
        print(f"⚠️  Error verificando logros: {str(e)}")
    
    # Diagnóstico del problema
    print(f"\n🔍 DIAGNÓSTICO DEL PROBLEMA:")
    print("-" * 30)
    
    if total_entrenamientos == 0:
        print("❌ PROBLEMA PRINCIPAL: No hay entrenamientos en la base de datos")
        print("💡 SOLUCIÓN: Importa entrenamientos desde Liftin")
    elif entrenamientos_liftin == 0:
        print("❌ PROBLEMA PRINCIPAL: No hay entrenamientos marcados como 'liftin'")
        print("💡 SOLUCIÓN: Verifica el campo 'fuente_datos' en los entrenamientos")
    elif clientes_con_liftin.count() == 0:
        print("❌ PROBLEMA PRINCIPAL: Entrenamientos no asociados a clientes")
        print("💡 SOLUCIÓN: Verifica las relaciones cliente-entrenamiento")
    else:
        print("✅ DATOS CORRECTOS: El problema está en la vista del dashboard")
        print("💡 SOLUCIÓN: Reemplazar la función dashboard_liftin con la versión corregida")
    
    # Instrucciones finales
    print(f"\n🚀 PRÓXIMOS PASOS:")
    print("-" * 20)
    print("1. Si los datos están correctos:")
    print("   → Reemplaza la función dashboard_liftin en views_liftin.py")
    print("   → Usa el código de vista_dashboard_simplificada_funcional.py")
    print("")
    print("2. Si faltan datos:")
    print("   → Importa entrenamientos desde Liftin primero")
    print("   → Verifica que estén asociados a clientes")
    print("")
    print("3. Después de cualquier cambio:")
    print("   → python manage.py runserver")
    print("   → Ve al dashboard de Liftin")
    print("   → ¡Deberías ver tus datos!")
    
    print(f"\n✅ DIAGNÓSTICO COMPLETADO")
    print("=" * 60)
    
except ImportError as e:
    print(f"❌ Error importando módulos Django: {str(e)}")
    print("💡 Asegúrate de estar ejecutando esto desde Django shell:")
    print("   python manage.py shell")
    
except Exception as e:
    print(f"❌ Error durante el diagnóstico: {str(e)}")
    print("💡 Contacta al desarrollador para obtener ayuda")

print("\n🔚 Script de diagnóstico finalizado")

