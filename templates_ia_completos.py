# 🎨 TEMPLATES COMPLETOS PARA DASHBOARDS DE IA
# Templates HTML para todos los sistemas de Inteligencia Artificial

# ============================================================================
# TEMPLATE: DASHBOARD PRINCIPAL DE IA
# ============================================================================

DASHBOARD_IA_PRINCIPAL = """
<!-- 🤖 DASHBOARD PRINCIPAL DE INTELIGENCIA ARTIFICIAL -->
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Centro de Inteligencia Artificial - {{ cliente.nombre }}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        :root {
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --accent-color: #f093fb;
            --success-color: #4facfe;
            --warning-color: #43e97b;
            --danger-color: #fa709a;
            --dark-color: #2c3e50;
            --light-color: #ecf0f1;
            --gradient-primary: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            --gradient-accent: linear-gradient(135deg, var(--accent-color), var(--success-color));
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: var(--dark-color);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }
        
        .header h1 {
            font-size: 2.5rem;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .header .subtitle {
            font-size: 1.2rem;
            color: var(--dark-color);
            opacity: 0.7;
        }
        
        .ia-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }
        
        .ia-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .ia-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
        }
        
        .ia-card-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .ia-card-icon {
            width: 50px;
            height: 50px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin-right: 15px;
            color: white;
        }
        
        .icon-predicciones { background: var(--gradient-primary); }
        .icon-recomendaciones { background: var(--gradient-accent); }
        .icon-patrones { background: linear-gradient(135deg, #43e97b, #38f9d7); }
        .icon-optimizacion { background: linear-gradient(135deg, #fa709a, #fee140); }
        
        .ia-card-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: var(--dark-color);
        }
        
        .ia-metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid rgba(0, 0, 0, 0.1);
        }
        
        .ia-metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            font-weight: 500;
            color: var(--dark-color);
        }
        
        .metric-value {
            font-weight: 600;
            color: var(--primary-color);
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-left: 10px;
        }
        
        .status-active { background-color: var(--success-color); }
        .status-training { background-color: var(--warning-color); }
        .status-inactive { background-color: var(--danger-color); }
        
        .recomendaciones-prioritarias {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
        }
        
        .recomendacion-item {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid var(--primary-color);
        }
        
        .recomendacion-titulo {
            font-weight: 600;
            color: var(--dark-color);
            margin-bottom: 8px;
        }
        
        .recomendacion-descripcion {
            color: var(--dark-color);
            opacity: 0.8;
            line-height: 1.5;
        }
        
        .prioridad-alta { border-left-color: var(--danger-color); }
        .prioridad-media { border-left-color: var(--warning-color); }
        .prioridad-baja { border-left-color: var(--success-color); }
        
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 20px;
        }
        
        .btn-ia {
            background: var(--gradient-primary);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            margin: 5px;
        }
        
        .btn-ia:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }
        
        .alertas-inteligentes {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            max-width: 350px;
        }
        
        .alerta {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            border-left: 4px solid var(--primary-color);
            animation: slideIn 0.5s ease;
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .alerta-critica { border-left-color: var(--danger-color); }
        .alerta-importante { border-left-color: var(--warning-color); }
        .alerta-info { border-left-color: var(--success-color); }
        
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        @media (max-width: 768px) {
            .ia-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .alertas-inteligentes {
                position: relative;
                top: auto;
                right: auto;
                max-width: 100%;
                margin-bottom: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🤖 Centro de Inteligencia Artificial</h1>
            <p class="subtitle">{{ cliente.nombre }} - Análisis avanzado con IA | Actualizado: {{ fecha_actualizacion }}</p>
        </div>
        
        <!-- Alertas Inteligentes -->
        <div class="alertas-inteligentes" id="alertasContainer">
            {% for alerta in dashboard_ia.alertas_inteligentes %}
            <div class="alerta alerta-{{ alerta.tipo }}">
                <strong>{{ alerta.titulo }}</strong><br>
                {{ alerta.mensaje }}
            </div>
            {% endfor %}
        </div>
        
        <!-- Grid Principal de IA -->
        <div class="ia-grid">
            <!-- Modelos Predictivos -->
            <div class="ia-card">
                <div class="ia-card-header">
                    <div class="ia-card-icon icon-predicciones">🔮</div>
                    <div>
                        <div class="ia-card-title">Modelos Predictivos</div>
                        <span class="status-indicator status-{{ sistemas_activos.modelos_predictivos|yesno:'active,inactive' }}"></span>
                    </div>
                </div>
                <div class="ia-metric">
                    <span class="metric-label">Modelos Entrenados</span>
                    <span class="metric-value">{{ dashboard_ia.datos_ia.predicciones.modelos_activos|default:0 }}</span>
                </div>
                <div class="ia-metric">
                    <span class="metric-label">Precisión Promedio</span>
                    <span class="metric-value">{{ dashboard_ia.datos_ia.predicciones.precision_promedio|default:0 }}%</span>
                </div>
                <div class="ia-metric">
                    <span class="metric-label">Predicciones Generadas</span>
                    <span class="metric-value">{{ dashboard_ia.datos_ia.predicciones.total_predicciones|default:0 }}</span>
                </div>
                <a href="{% url 'predicciones_avanzadas' cliente.id %}" class="btn-ia">Ver Predicciones</a>
            </div>
            
            <!-- Sistema de Recomendaciones -->
            <div class="ia-card">
                <div class="ia-card-header">
                    <div class="ia-card-icon icon-recomendaciones">💡</div>
                    <div>
                        <div class="ia-card-title">Recomendaciones IA</div>
                        <span class="status-indicator status-active"></span>
                    </div>
                </div>
                <div class="ia-metric">
                    <span class="metric-label">Recomendaciones Activas</span>
                    <span class="metric-value">{{ dashboard_ia.datos_ia.recomendaciones.total_activas|default:0 }}</span>
                </div>
                <div class="ia-metric">
                    <span class="metric-label">Confianza Sistema</span>
                    <span class="metric-value">{{ dashboard_ia.datos_ia.recomendaciones.confianza|default:0 }}%</span>
                </div>
                <div class="ia-metric">
                    <span class="metric-label">Rutinas Optimizadas</span>
                    <span class="metric-value">{{ dashboard_ia.datos_ia.recomendaciones.rutinas_generadas|default:0 }}</span>
                </div>
                <a href="{% url 'recomendaciones_inteligentes' cliente.id %}" class="btn-ia">Ver Recomendaciones</a>
            </div>
            
            <!-- Detección de Patrones -->
            <div class="ia-card">
                <div class="ia-card-header">
                    <div class="ia-card-icon icon-patrones">🔍</div>
                    <div>
                        <div class="ia-card-title">Detección de Patrones</div>
                        <span class="status-indicator status-active"></span>
                    </div>
                </div>
                <div class="ia-metric">
                    <span class="metric-label">Patrones Detectados</span>
                    <span class="metric-value">{{ dashboard_ia.datos_ia.patrones.total_patrones|default:0 }}</span>
                </div>
                <div class="ia-metric">
                    <span class="metric-label">Anomalías Encontradas</span>
                    <span class="metric-value">{{ dashboard_ia.datos_ia.patrones.anomalias|default:0 }}</span>
                </div>
                <div class="ia-metric">
                    <span class="metric-label">Estancamientos</span>
                    <span class="metric-value">{{ dashboard_ia.datos_ia.patrones.estancamientos|default:0 }}</span>
                </div>
                <a href="{% url 'deteccion_patrones' cliente.id %}" class="btn-ia">Analizar Patrones</a>
            </div>
            
            <!-- Optimización -->
            <div class="ia-card">
                <div class="ia-card-header">
                    <div class="ia-card-icon icon-optimizacion">⚡</div>
                    <div>
                        <div class="ia-card-title">Optimización IA</div>
                        <span class="status-indicator status-active"></span>
                    </div>
                </div>
                <div class="ia-metric">
                    <span class="metric-label">Mejora Estimada</span>
                    <span class="metric-value">{{ dashboard_ia.datos_ia.optimizaciones.mejora_estimada|default:0 }}%</span>
                </div>
                <div class="ia-metric">
                    <span class="metric-label">Algoritmos Activos</span>
                    <span class="metric-value">{{ dashboard_ia.datos_ia.optimizaciones.algoritmos_activos|default:0 }}</span>
                </div>
                <div class="ia-metric">
                    <span class="metric-label">Optimizaciones Realizadas</span>
                    <span class="metric-value">{{ dashboard_ia.datos_ia.optimizaciones.total_optimizaciones|default:0 }}</span>
                </div>
                <a href="{% url 'optimizacion_entrenamientos' cliente.id %}" class="btn-ia">Optimizar Entrenamientos</a>
            </div>
        </div>
        
        <!-- Recomendaciones Prioritarias -->
        <div class="recomendaciones-prioritarias">
            <h2>🎯 Recomendaciones Prioritarias de IA</h2>
            {% for recomendacion in dashboard_ia.recomendaciones_prioritarias %}
            <div class="recomendacion-item prioridad-{{ recomendacion.prioridad }}">
                <div class="recomendacion-titulo">{{ recomendacion.titulo }}</div>
                <div class="recomendacion-descripcion">{{ recomendacion.descripcion }}</div>
            </div>
            {% empty %}
            <div class="recomendacion-item">
                <div class="recomendacion-titulo">🎉 ¡Excelente trabajo!</div>
                <div class="recomendacion-descripcion">No hay recomendaciones críticas en este momento. Continúa con tu rutina actual.</div>
            </div>
            {% endfor %}
        </div>
        
        <!-- Gráfico de Métricas Consolidadas -->
        <div class="ia-card">
            <h3>📊 Métricas Consolidadas de IA</h3>
            <div class="chart-container">
                <canvas id="metricsChart"></canvas>
            </div>
        </div>
    </div>
    
    <script>
        // Configuración del gráfico de métricas
        const ctx = document.getElementById('metricsChart').getContext('2d');
        const metricsChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Predicciones', 'Recomendaciones', 'Patrones', 'Optimización', 'Adherencia', 'Progreso'],
                datasets: [{
                    label: 'Rendimiento IA',
                    data: [
                        {{ dashboard_ia.metricas_consolidadas.predicciones|default:0 }},
                        {{ dashboard_ia.metricas_consolidadas.recomendaciones|default:0 }},
                        {{ dashboard_ia.metricas_consolidadas.patrones|default:0 }},
                        {{ dashboard_ia.metricas_consolidadas.optimizacion|default:0 }},
                        {{ dashboard_ia.metricas_consolidadas.adherencia|default:0 }},
                        {{ dashboard_ia.metricas_consolidadas.progreso|default:0 }}
                    ],
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(102, 126, 234, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(102, 126, 234, 1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
        
        // Función para actualizar datos en tiempo real
        async function actualizarDatosIA() {
            try {
                const response = await axios.get(`/analytics/api/ia/dashboard/{{ cliente.id }}/`);
                if (response.data.success) {
                    // Actualizar métricas en tiempo real
                    console.log('Datos de IA actualizados:', response.data);
                }
            } catch (error) {
                console.error('Error actualizando datos de IA:', error);
            }
        }
        
        // Actualizar cada 30 segundos
        setInterval(actualizarDatosIA, 30000);
        
        // Animaciones de entrada
        document.addEventListener('DOMContentLoaded', function() {
            const cards = document.querySelectorAll('.ia-card');
            cards.forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    card.style.transition = 'all 0.5s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 100);
            });
        });
    </script>
</body>
</html>
"""

# ============================================================================
# TEMPLATE: PREDICCIONES AVANZADAS
# ============================================================================

PREDICCIONES_AVANZADAS = """
<!-- 🔮 PREDICCIONES AVANZADAS CON IA -->
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Predicciones Avanzadas - {{ cliente.nombre }}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        /* Estilos similares al dashboard principal con adaptaciones específicas */
        :root {
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --accent-color: #f093fb;
            --success-color: #4facfe;
            --warning-color: #43e97b;
            --danger-color: #fa709a;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }
        
        .prediccion-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
        }
        
        .controles {
            display: flex;
            gap: 15px;
            margin-bottom: 25px;
            flex-wrap: wrap;
        }
        
        .control-group {
            display: flex;
            flex-direction: column;
        }
        
        .control-group label {
            font-weight: 600;
            margin-bottom: 5px;
            color: var(--primary-color);
        }
        
        .control-group select,
        .control-group input {
            padding: 10px 15px;
            border: 2px solid rgba(102, 126, 234, 0.2);
            border-radius: 10px;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .control-group select:focus,
        .control-group input:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .btn-predecir {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            align-self: end;
        }
        
        .btn-predecir:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }
        
        .prediccion-resultado {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
            margin-top: 25px;
        }
        
        .prediccion-grafico {
            height: 400px;
            position: relative;
        }
        
        .prediccion-detalles {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
            border-radius: 15px;
            padding: 20px;
        }
        
        .prediccion-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid rgba(0, 0, 0, 0.1);
        }
        
        .prediccion-item:last-child {
            border-bottom: none;
        }
        
        .confianza-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .confianza-bar {
            width: 100px;
            height: 8px;
            background: rgba(0, 0, 0, 0.1);
            border-radius: 4px;
            overflow: hidden;
        }
        
        .confianza-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--danger-color), var(--warning-color), var(--success-color));
            transition: width 0.5s ease;
        }
        
        .riesgo-lesion {
            background: linear-gradient(135deg, rgba(250, 112, 154, 0.1), rgba(254, 225, 64, 0.1));
            border-radius: 15px;
            padding: 20px;
            margin-top: 25px;
        }
        
        .riesgo-nivel {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: 600;
            color: white;
            margin-left: 10px;
        }
        
        .riesgo-bajo { background: var(--success-color); }
        .riesgo-moderado { background: var(--warning-color); }
        .riesgo-alto { background: var(--danger-color); }
        .riesgo-critico { background: #e74c3c; }
        
        @media (max-width: 768px) {
            .prediccion-resultado {
                grid-template-columns: 1fr;
            }
            
            .controles {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🔮 Predicciones Avanzadas con IA</h1>
            <p>{{ cliente.nombre }} - Modelos predictivos de rendimiento</p>
        </div>
        
        <!-- Controles de Predicción -->
        <div class="prediccion-card">
            <h3>⚙️ Configurar Predicción</h3>
            <form method="GET" class="controles">
                <div class="control-group">
                    <label for="ejercicio">Ejercicio:</label>
                    <select name="ejercicio" id="ejercicio">
                        <option value="">Seleccionar ejercicio...</option>
                        {% for ejercicio in ejercicios_disponibles %}
                        <option value="{{ ejercicio }}" {% if ejercicio == ejercicio_seleccionado %}selected{% endif %}>
                            {{ ejercicio }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="control-group">
                    <label for="semanas">Semanas a predecir:</label>
                    <input type="number" name="semanas" id="semanas" value="{{ semanas_prediccion }}" min="1" max="12">
                </div>
                
                <button type="submit" class="btn-predecir">
                    <span class="loading-spinner" style="display: none;"></span>
                    Generar Predicción
                </button>
            </form>
        </div>
        
        <!-- Resultados de Predicción -->
        {% if predicciones_rendimiento.prediccion_disponible %}
        <div class="prediccion-card">
            <h3>📈 Predicción de Rendimiento - {{ predicciones_rendimiento.ejercicio }}</h3>
            
            <div class="prediccion-resultado">
                <div class="prediccion-grafico">
                    <canvas id="prediccionChart"></canvas>
                </div>
                
                <div class="prediccion-detalles">
                    <h4>📊 Detalles de la Predicción</h4>
                    
                    <div class="prediccion-item">
                        <span>Algoritmo Usado:</span>
                        <strong>{{ predicciones_rendimiento.algoritmo_usado|title }}</strong>
                    </div>
                    
                    <div class="prediccion-item">
                        <span>Precisión del Modelo:</span>
                        <div class="confianza-indicator">
                            <div class="confianza-bar">
                                <div class="confianza-fill" style="width: {{ predicciones_rendimiento.precision_modelo }}%"></div>
                            </div>
                            <span>{{ predicciones_rendimiento.precision_modelo }}%</span>
                        </div>
                    </div>
                    
                    <div class="prediccion-item">
                        <span>Tendencia General:</span>
                        <strong>{{ predicciones_rendimiento.tendencia_general }}</strong>
                    </div>
                    
                    <h5 style="margin-top: 20px;">🔑 Factores Clave:</h5>
                    {% for factor in predicciones_rendimiento.factores_clave %}
                    <div style="font-size: 0.9rem; margin: 5px 0;">• {{ factor }}</div>
                    {% endfor %}
                </div>
            </div>
            
            <!-- Predicciones Semanales -->
            <div style="margin-top: 25px;">
                <h4>📅 Predicciones Semanales</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                    {% for prediccion in predicciones_rendimiento.predicciones %}
                    <div style="background: rgba(102, 126, 234, 0.1); border-radius: 10px; padding: 15px;">
                        <div style="font-weight: 600; color: var(--primary-color);">Semana {{ prediccion.semana }}</div>
                        <div style="font-size: 1.2rem; font-weight: 600; margin: 5px 0;">{{ prediccion.peso_predicho }} kg</div>
                        <div style="font-size: 0.9rem; color: #666;">
                            Rango: {{ prediccion.intervalo_confianza.minimo }} - {{ prediccion.intervalo_confianza.maximo }} kg
                        </div>
                        <div style="font-size: 0.9rem; color: #666;">
                            Probabilidad: {{ prediccion.probabilidad_exito }}%
                        </div>
                        <div style="font-size: 0.8rem; margin-top: 8px; font-style: italic;">
                            {{ prediccion.recomendacion }}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% else %}
        <div class="prediccion-card">
            <h3>ℹ️ Información</h3>
            <p>{{ predicciones_rendimiento.razon }}</p>
        </div>
        {% endif %}
        
        <!-- Evaluación de Riesgo de Lesión -->
        <div class="prediccion-card">
            <h3>🛡️ Evaluación de Riesgo de Lesión</h3>
            
            <div class="riesgo-lesion">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <span style="font-size: 1.1rem; font-weight: 600;">Nivel de Riesgo:</span>
                    <span class="riesgo-nivel riesgo-{{ riesgo_lesion.nivel_riesgo }}">
                        {{ riesgo_lesion.nivel_riesgo|title }}
                    </span>
                    <span style="margin-left: 10px;">({{ riesgo_lesion.puntuacion_riesgo }}/100)</span>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                    {% for factor in riesgo_lesion.factores_riesgo %}
                    <div style="background: rgba(255, 255, 255, 0.5); border-radius: 8px; padding: 10px;">
                        <div style="font-weight: 600;">{{ factor.nombre }}</div>
                        <div style="font-size: 0.9rem; color: #666;">{{ factor.descripcion }}</div>
                    </div>
                    {% endfor %}
                </div>
                
                <div style="margin-top: 15px;">
                    <h5>💡 Recomendaciones Preventivas:</h5>
                    {% for recomendacion in riesgo_lesion.recomendaciones_prevencion %}
                    <div style="margin: 5px 0;">• {{ recomendacion }}</div>
                    {% endfor %}
                </div>
            </div>
        </div>
        
        <!-- Optimización de Carga -->
        <div class="prediccion-card">
            <h3>⚡ Optimización de Carga de Entrenamiento</h3>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                <div>
                    <h5>🎯 Objetivo: {{ optimizacion_carga.objetivo|title }}</h5>
                    <div class="prediccion-item">
                        <span>Mejora Estimada:</span>
                        <strong>{{ optimizacion_carga.mejora_estimada }}%</strong>
                    </div>
                    <div class="prediccion-item">
                        <span>Confianza:</span>
                        <strong>{{ optimizacion_carga.confianza_optimizacion }}%</strong>
                    </div>
                    <div class="prediccion-item">
                        <span>Período:</span>
                        <strong>{{ optimizacion_carga.periodo_semanas }} semanas</strong>
                    </div>
                </div>
                
                <div>
                    <h5>📋 Plan Optimizado:</h5>
                    {% for aspecto, valor in optimizacion_carga.plan_optimizado.items %}
                    <div style="margin: 8px 0;">
                        <strong>{{ aspecto|title }}:</strong> {{ valor }}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Gráfico de predicciones
        {% if predicciones_rendimiento.prediccion_disponible %}
        const ctx = document.getElementById('prediccionChart').getContext('2d');
        const prediccionChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [
                    'Actual',
                    {% for prediccion in predicciones_rendimiento.predicciones %}
                    'Semana {{ prediccion.semana }}',
                    {% endfor %}
                ],
                datasets: [{
                    label: 'Peso Predicho (kg)',
                    data: [
                        null, // Punto actual
                        {% for prediccion in predicciones_rendimiento.predicciones %}
                        {{ prediccion.peso_predicho }},
                        {% endfor %}
                    ],
                    borderColor: 'rgba(102, 126, 234, 1)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Rango Mínimo',
                    data: [
                        null,
                        {% for prediccion in predicciones_rendimiento.predicciones %}
                        {{ prediccion.intervalo_confianza.minimo }},
                        {% endfor %}
                    ],
                    borderColor: 'rgba(102, 126, 234, 0.3)',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    fill: false
                }, {
                    label: 'Rango Máximo',
                    data: [
                        null,
                        {% for prediccion in predicciones_rendimiento.predicciones %}
                        {{ prediccion.intervalo_confianza.maximo }},
                        {% endfor %}
                    ],
                    borderColor: 'rgba(102, 126, 234, 0.3)',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Predicción de Rendimiento - {{ predicciones_rendimiento.ejercicio }}'
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Peso (kg)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Tiempo'
                        }
                    }
                }
            }
        });
        {% endif %}
        
        // Función para actualizar predicción en tiempo real
        async function actualizarPrediccion() {
            const ejercicio = document.getElementById('ejercicio').value;
            const semanas = document.getElementById('semanas').value;
            
            if (!ejercicio) return;
            
            try {
                const response = await axios.post(`/analytics/api/ia/prediccion/{{ cliente.id }}/`, {
                    ejercicio: ejercicio,
                    semanas: parseInt(semanas)
                });
                
                if (response.data.success) {
                    console.log('Predicción actualizada:', response.data.prediccion);
                    // Aquí se actualizaría la UI con los nuevos datos
                }
            } catch (error) {
                console.error('Error actualizando predicción:', error);
            }
        }
        
        // Event listeners
        document.getElementById('ejercicio').addEventListener('change', actualizarPrediccion);
        document.getElementById('semanas').addEventListener('change', actualizarPrediccion);
    </script>
</body>
</html>
"""

# ============================================================================
# SCRIPT PARA EXTRAER TEMPLATES
# ============================================================================

def extraer_templates():
    """
    Extrae todos los templates a archivos HTML individuales
    """
    templates = {
        'dashboard_ia_principal.html': DASHBOARD_IA_PRINCIPAL,
        'predicciones_avanzadas.html': PREDICCIONES_AVANZADAS,
    }
    
    import os
    
    # Crear directorio de templates si no existe
    os.makedirs('templates/analytics', exist_ok=True)
    
    for nombre_archivo, contenido in templates.items():
        ruta_archivo = f'templates/analytics/{nombre_archivo}'
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            f.write(contenido)
        print(f"✅ Template creado: {ruta_archivo}")

if __name__ == "__main__":
    extraer_templates()
    print("🎨 TODOS LOS TEMPLATES DE IA CREADOS EXITOSAMENTE")

