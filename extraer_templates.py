#!/usr/bin/env python3
# 📄 SCRIPT PARA EXTRAER TEMPLATES DEL CENTRO DE ANÁLISIS
# Uso: python3 extraer_templates.py

import re
import os

def extraer_templates():
    """
    Extrae los templates del archivo analytics_templates_completos.py
    y los guarda como archivos HTML individuales
    """
    
    # Crear directorio si no existe
    os.makedirs('templates/analytics', exist_ok=True)
    
    # Leer archivo de templates
    try:
        with open('analytics_templates_completos.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ Error: No se encontró el archivo analytics_templates_completos.py")
        return
    
    # Definir templates a extraer
    templates_config = {
        'progresion.html': 'TEMPLATE_PROGRESION',
        'comparativas.html': 'TEMPLATE_COMPARATIVAS', 
        'recomendaciones.html': 'TEMPLATE_RECOMENDACIONES',
        'predicciones.html': 'TEMPLATE_PREDICCIONES'
    }
    
    print("🚀 Extrayendo templates del centro de análisis...")
    print("=" * 60)
    
    # Extraer cada template
    for filename, variable_name in templates_config.items():
        try:
            # Buscar el contenido del template
            pattern = rf'{variable_name} = \'\'\'(.*?)\'\'\''
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                template_content = match.group(1)
                
                # Guardar template
                filepath = f'templates/analytics/{filename}'
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(template_content)
                
                print(f"✅ Creado: {filepath}")
                
                # Mostrar estadísticas del template
                lines = template_content.count('\n')
                size = len(template_content)
                print(f"   📊 {lines} líneas, {size} caracteres")
                
            else:
                print(f"❌ Error: No se encontró {variable_name} en el archivo")
                
        except Exception as e:
            print(f"❌ Error extrayendo {filename}: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Extracción completada!")
    print("\n📁 Templates creados en: templates/analytics/")
    print("   - progresion.html")
    print("   - comparativas.html") 
    print("   - recomendaciones.html")
    print("   - predicciones.html")
    
    print("\n🔧 Próximo paso:")
    print("   Copiar estos archivos a tu proyecto Django")

if __name__ == "__main__":
    extraer_templates()

