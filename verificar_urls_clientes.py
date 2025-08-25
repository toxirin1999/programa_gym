import os
import re

# Ruta a la carpeta de templates
BASE_DIR = 'gymproject/clientes/templates'

# Namespace esperado
NAMESPACE = 'clientes'

# Patrón para detectar llamadas {% url 'algo' %}
pattern = re.compile(r"""{%\s*url\s+['"]([^'":\s]+)['"]""")

errores = []

for root, _, files in os.walk(BASE_DIR):
    for file in files:
        if file.endswith('.html'):
            path = os.path.join(root, file)
            with open(path, encoding='utf-8') as f:
                contenido = f.read()

            for match in pattern.finditer(contenido):
                nombre_url = match.group(1)
                if not nombre_url.startswith(NAMESPACE + ':'):
                    errores.append((path, nombre_url))

# Mostrar resultados
if errores:
    print("🚨 Se encontraron URLs sin namespace 'clientes:'\n")
    for archivo, nombre in errores:
        print(f" - {archivo}: {{% url '{nombre}' %}}")
else:
    print("✅ Todas las URLs usan el namespace correctamente.")
