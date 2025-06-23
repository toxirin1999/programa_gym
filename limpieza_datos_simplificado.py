"""
Script de limpieza de datos para corregir valores no numéricos en campos decimales.
Este script detecta y corrige valores corruptos en la base de datos, especialmente
en el campo peso_kg de SerieRealizada.

Para ejecutar:
python manage.py shell
>>> exec(open('limpieza_datos.py').read())
"""

from decimal import Decimal, InvalidOperation
import logging
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('limpieza_datos.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Importar modelos necesarios
try:
    from entrenos.models import SerieRealizada, EntrenoRealizado, PlanPersonalizado
    # Intentar obtener todos los modelos para diagnóstico
    try:
        from django.apps import apps
        entrenos_models = apps.get_app_config('entrenos').get_models()
        logger.info(f"Modelos disponibles en entrenos: {[model.__name__ for model in entrenos_models]}")
    except:
        pass
    
    logger.info("Modelos importados correctamente")
except ImportError as e:
    logger.error(f"Error al importar modelos: {str(e)}")
    sys.exit(1)

def limpiar_series_realizadas():
    """Limpia valores no numéricos en SerieRealizada.peso_kg"""
    logger.info("Iniciando limpieza de SerieRealizada.peso_kg")
    
    # Obtener todas las series
    series = SerieRealizada.objects.all()
    total = series.count()
    corregidas = 0
    problematicas = 0
    
    logger.info(f"Total de series a procesar: {total}")
    
    for serie in series:
        try:
            # Intentar convertir a Decimal para verificar si es válido
            if serie.peso_kg is not None:
                try:
                    Decimal(str(serie.peso_kg))
                    # Si llega aquí, el valor es válido
                except (InvalidOperation, ValueError, TypeError):
                    # Valor inválido, intentar corregir
                    problematicas += 1
                    valor_original = serie.peso_kg
                    
                    # Intentar limpiar y convertir
                    try:
                        # Convertir a string y reemplazar coma por punto
                        valor_str = str(valor_original).replace(',', '.')
                        # Eliminar caracteres no numéricos excepto punto decimal
                        valor_limpio = ''.join(c for c in valor_str if c.isdigit() or c == '.')
                        
                        if valor_limpio:
                            # Si quedó algo después de limpiar
                            nuevo_valor = Decimal(valor_limpio)
                            serie.peso_kg = nuevo_valor
                            serie.save()
                            corregidas += 1
                            logger.info(f"Serie ID {serie.id}: Valor corregido de '{valor_original}' a '{nuevo_valor}'")
                        else:
                            # Si no quedó nada válido, establecer a 0
                            serie.peso_kg = Decimal('0')
                            serie.save()
                            corregidas += 1
                            logger.info(f"Serie ID {serie.id}: Valor inválido '{valor_original}' establecido a 0")
                    except Exception as e:
                        # Si todo falla, establecer a 0
                        logger.warning(f"Serie ID {serie.id}: Error al corregir '{valor_original}': {str(e)}")
                        serie.peso_kg = Decimal('0')
                        serie.save()
                        corregidas += 1
                        logger.info(f"Serie ID {serie.id}: Valor problemático establecido a 0")
        except Exception as e:
            logger.error(f"Error al procesar serie ID {serie.id}: {str(e)}")
    
    logger.info(f"Limpieza de SerieRealizada.peso_kg completada:")
    logger.info(f"- Total series procesadas: {total}")
    logger.info(f"- Series problemáticas encontradas: {problematicas}")
    logger.info(f"- Series corregidas: {corregidas}")
    
    return problematicas, corregidas

def limpiar_plan_personalizado():
    """Limpia valores no numéricos en PlanPersonalizado.peso_objetivo"""
    logger.info("Iniciando limpieza de PlanPersonalizado.peso_objetivo")
    
    # Obtener todos los planes
    planes = PlanPersonalizado.objects.all()
    total = planes.count()
    corregidas = 0
    problematicas = 0
    
    logger.info(f"Total de planes a procesar: {total}")
    
    for plan in planes:
        try:
            # Intentar convertir a Decimal para verificar si es válido
            if plan.peso_objetivo is not None:
                try:
                    Decimal(str(plan.peso_objetivo))
                    # Si llega aquí, el valor es válido
                except (InvalidOperation, ValueError, TypeError):
                    # Valor inválido, intentar corregir
                    problematicas += 1
                    valor_original = plan.peso_objetivo
                    
                    # Intentar limpiar y convertir
                    try:
                        # Convertir a string y reemplazar coma por punto
                        valor_str = str(valor_original).replace(',', '.')
                        # Eliminar caracteres no numéricos excepto punto decimal
                        valor_limpio = ''.join(c for c in valor_str if c.isdigit() or c == '.')
                        
                        if valor_limpio:
                            # Si quedó algo después de limpiar
                            nuevo_valor = Decimal(valor_limpio)
                            plan.peso_objetivo = nuevo_valor
                            plan.save()
                            corregidas += 1
                            logger.info(f"Plan ID {plan.id}: Valor corregido de '{valor_original}' a '{nuevo_valor}'")
                        else:
                            # Si no quedó nada válido, establecer a 0
                            plan.peso_objetivo = Decimal('0')
                            plan.save()
                            corregidas += 1
                            logger.info(f"Plan ID {plan.id}: Valor inválido '{valor_original}' establecido a 0")
                    except Exception as e:
                        # Si todo falla, establecer a 0
                        logger.warning(f"Plan ID {plan.id}: Error al corregir '{valor_original}': {str(e)}")
                        plan.peso_objetivo = Decimal('0')
                        plan.save()
                        corregidas += 1
                        logger.info(f"Plan ID {plan.id}: Valor problemático establecido a 0")
        except Exception as e:
            logger.error(f"Error al procesar plan ID {plan.id}: {str(e)}")
    
    logger.info(f"Limpieza de PlanPersonalizado.peso_objetivo completada:")
    logger.info(f"- Total planes procesados: {total}")
    logger.info(f"- Planes problemáticos encontrados: {problematicas}")
    logger.info(f"- Planes corregidos: {corregidas}")
    
    return problematicas, corregidos

def ejecutar_limpieza():
    """Ejecuta todas las funciones de limpieza y reporta resultados"""
    logger.info("=== INICIANDO PROCESO DE LIMPIEZA DE DATOS ===")
    
    try:
        # Limpiar SerieRealizada.peso_kg
        series_problematicas, series_corregidas = limpiar_series_realizadas()
        
        # Limpiar PlanPersonalizado.peso_objetivo
        planes_problematicos, planes_corregidos = limpiar_plan_personalizado()
        
        # Resumen final
        logger.info("=== RESUMEN DE LIMPIEZA DE DATOS ===")
        logger.info(f"SerieRealizada.peso_kg: {series_problematicas} problemas, {series_corregidas} corregidos")
        logger.info(f"PlanPersonalizado.peso_objetivo: {planes_problematicos} problemas, {planes_corregidos} corregidos")
        
        total_problemas = series_problematicas + planes_problematicos
        total_corregidos = series_corregidas + planes_corregidos
        
        logger.info(f"TOTAL: {total_problemas} problemas encontrados, {total_corregidos} corregidos")
        logger.info("=== PROCESO DE LIMPIEZA COMPLETADO ===")
        
        return total_problemas, total_corregidos
    except Exception as e:
        logger.error(f"Error durante el proceso de limpieza: {str(e)}")
        return 0, 0

# Ejecutar limpieza si se ejecuta como script principal
if __name__ == "__main__":
    ejecutar_limpieza()

# Ejecutar limpieza automáticamente
ejecutar_limpieza()
