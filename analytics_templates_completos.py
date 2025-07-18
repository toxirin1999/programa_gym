# 📊 TEMPLATES COMPLETOS PARA EL CENTRO DE ANÁLISIS
# Archivos: templates/analytics/

# ============================================================================
# 1. TEMPLATE DE PROGRESIÓN
# ============================================================================

TEMPLATE_PROGRESION = '''
<!-- 📈 ANÁLISIS DE PROGRESIÓN -->
<!-- Archivo: templates/analytics/progresion.html -->

{% extends 'base.html' %}
{% load static %}

{% block title %}Análisis de Progresión - {{ cliente.nombre }}{% endblock %}

{% block extra_css %}
<link href="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.min.css" rel="stylesheet">
<style>
    :root {
        --primary-color: #3b82f6;
        --secondary-color: #1e40af;
        --accent-color: #06b6d4;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --dark-bg: #0f172a;
        --card-bg: #1e293b;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --border-color: #334155;
    }

    body {
        background: linear-gradient(135deg, var(--dark-bg) 0%, #1e293b 100%);
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        min-height: 100vh;
    }

    .analytics-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 2rem;
    }

    .analytics-header {
        background: linear-gradient(135deg, var(--success-color), var(--accent-color));
        border-radius: 1rem;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
    }

    .analytics-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0 0 0.5rem 0;
    }

    .exercise-selector {
        background: var(--card-bg);
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid var(--border-color);
    }

    .exercise-selector select {
        width: 100%;
        padding: 1rem;
        background: var(--dark-bg);
        border: 1px solid var(--border-color);
        border-radius: 0.5rem;
        color: var(--text-primary);
        font-size: 1rem;
    }

    .progress-grid {
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 2rem;
        margin-bottom: 2rem;
    }

    .chart-card {
        background: var(--card-bg);
        border-radius: 1rem;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
    }

    .chart-title {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .stats-card {
        background: var(--card-bg);
        border-radius: 1rem;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
    }

    .stat-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 1px solid var(--border-color);
    }

    .stat-item:last-child {
        border-bottom: none;
    }

    .stat-label {
        color: var(--text-secondary);
        font-size: 0.9rem;
    }

    .stat-value {
        font-weight: 600;
        color: var(--text-primary);
    }

    .predictions-section {
        background: var(--card-bg);
        border-radius: 1rem;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
        margin-bottom: 2rem;
    }

    .prediction-item {
        background: rgba(59, 130, 246, 0.1);
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid var(--primary-color);
    }

    .prediction-item:last-child {
        margin-bottom: 0;
    }

    .prediction-date {
        font-size: 0.8rem;
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
    }

    .prediction-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--primary-color);
    }

    @media (max-width: 768px) {
        .progress-grid {
            grid-template-columns: 1fr;
        }
    }
</style>
{% endblock %}

{% block content %}
<div class="analytics-container">
    <!-- Header -->
    <div class="analytics-header">
        <h1>📈 Análisis de Progresión</h1>
        <p>Seguimiento detallado del progreso en ejercicios específicos</p>
    </div>

    <!-- Selector de Ejercicio -->
    <div class="exercise-selector">
        <label for="ejercicio-select" style="display: block; margin-bottom: 0.5rem; font-weight: 600;">
            Seleccionar Ejercicio:
        </label>
        <select id="ejercicio-select" onchange="cambiarEjercicio()">
            {% for ejercicio in ejercicios %}
            <option value="{{ ejercicio }}" {% if ejercicio == ejercicio_seleccionado %}selected{% endif %}>
                {{ ejercicio }}
            </option>
            {% endfor %}
        </select>
    </div>

    {% if ejercicio_seleccionado %}
    <!-- Gráfico de Progresión y Estadísticas -->
    <div class="progress-grid">
        <div class="chart-card">
            <div class="chart-title">
                🏋️‍♂️ Progresión de {{ ejercicio_seleccionado }}
            </div>
            <canvas id="progressChart" width="400" height="200"></canvas>
        </div>

        <div class="stats-card">
            <div class="chart-title">
                📊 Estadísticas
            </div>
            {% if tendencia %}
            <div class="stat-item">
                <span class="stat-label">Tendencia General</span>
                <span class="stat-value" style="color: {% if tendencia.tendencia_general > 0 %}var(--success-color){% else %}var(--danger-color){% endif %}">
                    {% if tendencia.tendencia_general > 0 %}↗️{% else %}↘️{% endif %}
                    {{ tendencia.tendencia_general|floatformat:1 }}%
                </span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Peso Máximo</span>
                <span class="stat-value">{{ tendencia.peso_maximo }} kg</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Sesiones Totales</span>
                <span class="stat-value">{{ tendencia.sesiones_totales }}</span>
            </div>
            {% else %}
            <div class="stat-item">
                <span class="stat-label">Estado</span>
                <span class="stat-value">Calculando tendencias...</span>
            </div>
            {% endif %}
        </div>
    </div>

    <!-- Predicciones -->
    {% if predicciones %}
    <div class="predictions-section">
        <div class="chart-title">
            🔮 Predicciones de Rendimiento
        </div>
        {% for prediccion in predicciones %}
        <div class="prediction-item">
            <div class="prediction-date">{{ prediccion.fecha_prediccion|date:"d/m/Y" }}</div>
            <div class="prediction-value">
                Peso estimado: {{ prediccion.peso_estimado }} kg
                ({{ prediccion.confianza }}% confianza)
            </div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% else %}
    <div style="text-align: center; padding: 4rem; color: var(--text-secondary);">
        <h3>No hay ejercicios disponibles para análisis</h3>
        <p>Realiza algunos entrenamientos para ver el análisis de progresión.</p>
    </div>
    {% endif %}

    <!-- Navegación -->
    <div style="text-align: center; margin-top: 2rem;">
        <a href="{% url 'analytics:dashboard' cliente.id %}" 
           style="background: var(--primary-color); color: white; padding: 1rem 2rem; border-radius: 0.5rem; text-decoration: none; font-weight: 600;">
            ← Volver al Dashboard
        </a>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.min.js"></script>
<script>
function cambiarEjercicio() {
    const select = document.getElementById('ejercicio-select');
    const ejercicio = select.value;
    if (ejercicio) {
        window.location.href = `?ejercicio=${encodeURIComponent(ejercicio)}`;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const datosProgresion = {{ datos_progresion|safe }};
    
    if (datosProgresion && datosProgresion.length > 0) {
        const ctx = document.getElementById('progressChart');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: datosProgresion.map(d => d.fecha),
                datasets: [{
                    label: 'Peso (kg)',
                    data: datosProgresion.map(d => d.peso),
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Volumen (kg)',
                    data: datosProgresion.map(d => d.volumen),
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f8fafc'
                        }
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        ticks: {
                            color: '#cbd5e1'
                        },
                        grid: {
                            color: '#334155'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        ticks: {
                            color: '#cbd5e1'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    },
                    x: {
                        ticks: {
                            color: '#cbd5e1'
                        },
                        grid: {
                            color: '#334155'
                        }
                    }
                }
            }
        });
    }
});
</script>
{% endblock %}
'''

# ============================================================================
# 2. TEMPLATE DE COMPARATIVAS
# ============================================================================

TEMPLATE_COMPARATIVAS = '''
<!-- 🔄 ANÁLISIS COMPARATIVO -->
<!-- Archivo: templates/analytics/comparativas.html -->

{% extends 'base.html' %}
{% load static %}

{% block title %}Análisis Comparativo - {{ cliente.nombre }}{% endblock %}

{% block extra_css %}
<style>
    :root {
        --primary-color: #3b82f6;
        --secondary-color: #1e40af;
        --accent-color: #06b6d4;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --dark-bg: #0f172a;
        --card-bg: #1e293b;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --border-color: #334155;
    }

    body {
        background: linear-gradient(135deg, var(--dark-bg) 0%, #1e293b 100%);
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        min-height: 100vh;
    }

    .analytics-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 2rem;
    }

    .analytics-header {
        background: linear-gradient(135deg, var(--warning-color), var(--accent-color));
        border-radius: 1rem;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
    }

    .controls-section {
        background: var(--card-bg);
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid var(--border-color);
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
    }

    .control-group {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .control-group label {
        font-weight: 600;
        color: var(--text-secondary);
        font-size: 0.9rem;
    }

    .control-group select,
    .control-group input {
        padding: 0.75rem;
        background: var(--dark-bg);
        border: 1px solid var(--border-color);
        border-radius: 0.5rem;
        color: var(--text-primary);
    }

    .comparison-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
        margin-bottom: 2rem;
    }

    .comparison-card {
        background: var(--card-bg);
        border-radius: 1rem;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
        position: relative;
        overflow: hidden;
    }

    .comparison-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
    }

    .metric-name {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: var(--text-primary);
    }

    .comparison-values {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }

    .value-item {
        text-align: center;
        flex: 1;
    }

    .value-label {
        font-size: 0.8rem;
        color: var(--text-secondary);
        margin-bottom: 0.25rem;
    }

    .value-number {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    .comparison-change {
        text-align: center;
        padding: 0.75rem;
        border-radius: 0.5rem;
        font-weight: 600;
        font-size: 0.9rem;
    }

    .change-positive {
        background: rgba(16, 185, 129, 0.2);
        color: var(--success-color);
    }

    .change-negative {
        background: rgba(239, 68, 68, 0.2);
        color: var(--danger-color);
    }

    .change-neutral {
        background: rgba(107, 114, 128, 0.2);
        color: var(--text-secondary);
    }

    .exercises-comparison {
        background: var(--card-bg);
        border-radius: 1rem;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
        margin-bottom: 2rem;
    }

    .exercise-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 1px solid var(--border-color);
    }

    .exercise-item:last-child {
        border-bottom: none;
    }

    .exercise-name {
        font-weight: 600;
        color: var(--text-primary);
        flex: 1;
    }

    .exercise-stats {
        display: flex;
        gap: 2rem;
        align-items: center;
    }

    .exercise-stat {
        text-align: center;
    }

    .exercise-stat-label {
        font-size: 0.7rem;
        color: var(--text-secondary);
        margin-bottom: 0.25rem;
    }

    .exercise-stat-value {
        font-weight: 600;
        color: var(--text-primary);
    }

    @media (max-width: 768px) {
        .controls-section {
            grid-template-columns: 1fr;
        }
        
        .comparison-grid {
            grid-template-columns: 1fr;
        }
        
        .exercise-stats {
            flex-direction: column;
            gap: 0.5rem;
        }
    }
</style>
{% endblock %}

{% block content %}
<div class="analytics-container">
    <!-- Header -->
    <div class="analytics-header">
        <h1>🔄 Análisis Comparativo</h1>
        <p>Compara tu rendimiento en diferentes períodos y contextos</p>
    </div>

    <!-- Controles -->
    <form method="get" class="controls-section">
        <div class="control-group">
            <label for="tipo">Tipo de Comparativa:</label>
            <select name="tipo" id="tipo" onchange="this.form.submit()">
                <option value="temporal" {% if tipo_comparativa == 'temporal' %}selected{% endif %}>
                    Temporal (vs período anterior)
                </option>
                <option value="ejercicios" {% if tipo_comparativa == 'ejercicios' %}selected{% endif %}>
                    Entre Ejercicios
                </option>
            </select>
        </div>

        <div class="control-group">
            <label for="periodo">Período (días):</label>
            <select name="periodo" id="periodo" onchange="this.form.submit()">
                <option value="7" {% if periodo == '7' %}selected{% endif %}>7 días</option>
                <option value="30" {% if periodo == '30' %}selected{% endif %}>30 días</option>
                <option value="90" {% if periodo == '90' %}selected{% endif %}>90 días</option>
            </select>
        </div>

        <div class="control-group">
            <label>&nbsp;</label>
            <button type="submit" style="background: var(--primary-color); color: white; border: none; padding: 0.75rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer;">
                Actualizar Análisis
            </button>
        </div>
    </form>

    {% if tipo_comparativa == 'temporal' %}
    <!-- Comparativas Temporales -->
    <div class="comparison-grid">
        {% for metrica, datos in comparativas_data.items %}
        <div class="comparison-card">
            <div class="metric-name">
                {% if metrica == 'volumen_total' %}🏋️‍♂️ Volumen Total
                {% elif metrica == 'intensidad_promedio' %}⚡ Intensidad Promedio
                {% elif metrica == 'calorias_totales' %}🔥 Calorías Totales
                {% elif metrica == 'consistencia' %}🎯 Consistencia
                {% endif %}
            </div>
            
            <div class="comparison-values">
                <div class="value-item">
                    <div class="value-label">Período Anterior</div>
                    <div class="value-number">{{ datos.anterior|floatformat:1 }}</div>
                </div>
                <div class="value-item">
                    <div class="value-label">Período Actual</div>
                    <div class="value-number">{{ datos.actual|floatformat:1 }}</div>
                </div>
            </div>
            
            <div class="comparison-change {% if datos.diferencia_pct > 0 %}change-positive{% elif datos.diferencia_pct < 0 %}change-negative{% else %}change-neutral{% endif %}">
                {% if datos.diferencia_pct > 0 %}↗️{% elif datos.diferencia_pct < 0 %}↘️{% else %}➡️{% endif %}
                {{ datos.diferencia_pct|floatformat:1 }}%
                ({{ datos.diferencia|floatformat:1 }})
            </div>
        </div>
        {% endfor %}
    </div>

    {% elif tipo_comparativa == 'ejercicios' %}
    <!-- Comparativas entre Ejercicios -->
    <div class="exercises-comparison">
        <h3 style="margin: 0 0 1.5rem 0; color: var(--text-primary);">
            📊 Comparativa entre Ejercicios ({{ periodo }} días)
        </h3>
        
        {% for ejercicio, metricas in comparativas_data.items %}
        <div class="exercise-item">
            <div class="exercise-name">{{ ejercicio }}</div>
            <div class="exercise-stats">
                <div class="exercise-stat">
                    <div class="exercise-stat-label">Sesiones</div>
                    <div class="exercise-stat-value">{{ metricas.total_sesiones }}</div>
                </div>
                <div class="exercise-stat">
                    <div class="exercise-stat-label">Volumen Total</div>
                    <div class="exercise-stat-value">{{ metricas.volumen_total|floatformat:0 }} kg</div>
                </div>
                <div class="exercise-stat">
                    <div class="exercise-stat-label">Peso Máximo</div>
                    <div class="exercise-stat-value">{{ metricas.peso_maximo|floatformat:0 }} kg</div>
                </div>
                <div class="exercise-stat">
                    <div class="exercise-stat-label">Peso Promedio</div>
                    <div class="exercise-stat-value">{{ metricas.peso_promedio|floatformat:1 }} kg</div>
                </div>
            </div>
        </div>
        {% empty %}
        <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
            No hay datos de ejercicios para comparar en este período.
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <!-- Navegación -->
    <div style="text-align: center; margin-top: 2rem;">
        <a href="{% url 'analytics:dashboard' cliente.id %}" 
           style="background: var(--primary-color); color: white; padding: 1rem 2rem; border-radius: 0.5rem; text-decoration: none; font-weight: 600;">
            ← Volver al Dashboard
        </a>
    </div>
</div>
{% endblock %}
'''

# ============================================================================
# 3. TEMPLATE DE RECOMENDACIONES
# ============================================================================

TEMPLATE_RECOMENDACIONES = '''
<!-- 💡 SISTEMA DE RECOMENDACIONES -->
<!-- Archivo: templates/analytics/recomendaciones.html -->

{% extends 'base.html' %}
{% load static %}

{% block title %}Recomendaciones - {{ cliente.nombre }}{% endblock %}

{% block extra_css %}
<style>
    :root {
        --primary-color: #3b82f6;
        --secondary-color: #1e40af;
        --accent-color: #06b6d4;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --dark-bg: #0f172a;
        --card-bg: #1e293b;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --border-color: #334155;
    }

    body {
        background: linear-gradient(135deg, var(--dark-bg) 0%, #1e293b 100%);
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        min-height: 100vh;
    }

    .analytics-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 2rem;
    }

    .analytics-header {
        background: linear-gradient(135deg, var(--warning-color), var(--primary-color));
        border-radius: 1rem;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
    }

    .generate-section {
        background: var(--card-bg);
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid var(--border-color);
        text-align: center;
    }

    .generate-btn {
        background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 0.5rem;
        font-weight: 600;
        font-size: 1rem;
        cursor: pointer;
        transition: transform 0.2s ease;
    }

    .generate-btn:hover {
        transform: translateY(-2px);
    }

    .recommendations-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 2rem;
        margin-bottom: 2rem;
    }

    .recommendations-section {
        background: var(--card-bg);
        border-radius: 1rem;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        color: var(--text-primary);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .recommendation-item {
        background: rgba(59, 130, 246, 0.05);
        border-radius: 0.75rem;
        padding: 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
        position: relative;
    }

    .recommendation-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    }

    .recommendation-item:last-child {
        margin-bottom: 0;
    }

    .recommendation-priority {
        position: absolute;
        top: 1rem;
        right: 1rem;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .priority-alta {
        background: rgba(239, 68, 68, 0.2);
        color: var(--danger-color);
    }

    .priority-media {
        background: rgba(245, 158, 11, 0.2);
        color: var(--warning-color);
    }

    .priority-baja {
        background: rgba(16, 185, 129, 0.2);
        color: var(--success-color);
    }

    .recommendation-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
        color: var(--text-primary);
        padding-right: 4rem;
    }

    .recommendation-description {
        color: var(--text-secondary);
        line-height: 1.5;
        margin-bottom: 1rem;
    }

    .recommendation-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.8rem;
        color: var(--text-secondary);
    }

    .recommendation-actions {
        display: flex;
        gap: 0.5rem;
        margin-top: 1rem;
    }

    .action-btn {
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .btn-apply {
        background: var(--success-color);
        color: white;
    }

    .btn-dismiss {
        background: var(--danger-color);
        color: white;
    }

    .btn-apply:hover,
    .btn-dismiss:hover {
        transform: translateY(-1px);
    }

    .automatic-recommendations {
        background: var(--card-bg);
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid var(--border-color);
    }

    .auto-rec-item {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(6, 182, 212, 0.1));
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid var(--success-color);
    }

    .auto-rec-item:last-child {
        margin-bottom: 0;
    }

    .message-success {
        background: rgba(16, 185, 129, 0.2);
        color: var(--success-color);
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        text-align: center;
        font-weight: 600;
    }

    @media (max-width: 768px) {
        .recommendations-grid {
            grid-template-columns: 1fr;
        }
    }
</style>
{% endblock %}

{% block content %}
<div class="analytics-container">
    <!-- Header -->
    <div class="analytics-header">
        <h1>💡 Sistema de Recomendaciones</h1>
        <p>Recomendaciones personalizadas para optimizar tu entrenamiento</p>
    </div>

    <!-- Mensaje de éxito -->
    {% if mensaje %}
    <div class="message-success">
        {{ mensaje }}
    </div>
    {% endif %}

    <!-- Generar Nuevas Recomendaciones -->
    <div class="generate-section">
        <h3 style="margin: 0 0 1rem 0;">🤖 Generar Nuevas Recomendaciones</h3>
        <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
            Analiza tus datos actuales y genera recomendaciones personalizadas
        </p>
        <form method="post">
            {% csrf_token %}
            <button type="submit" name="generar" class="generate-btn">
                🚀 Generar Recomendaciones
            </button>
        </form>
    </div>

    <!-- Recomendaciones Automáticas -->
    {% if recomendaciones_automaticas %}
    <div class="automatic-recommendations">
        <div class="section-title">
            🎯 Recomendaciones Automáticas
        </div>
        {% for rec in recomendaciones_automaticas %}
        <div class="auto-rec-item">
            <div style="font-weight: 600; margin-bottom: 0.5rem;">{{ rec.titulo }}</div>
            <div style="color: var(--text-secondary);">{{ rec.descripcion }}</div>
            <div style="margin-top: 0.5rem; font-size: 0.8rem; color: var(--text-secondary);">
                Tipo: {{ rec.tipo|title }} | Prioridad: {{ rec.prioridad|title }}
            </div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <!-- Recomendaciones Activas y Aplicadas -->
    <div class="recommendations-grid">
        <!-- Recomendaciones Activas -->
        <div class="recommendations-section">
            <div class="section-title">
                ⚡ Recomendaciones Activas
            </div>
            {% for recomendacion in recomendaciones_activas %}
            <div class="recommendation-item">
                <div class="recommendation-priority priority-{{ recomendacion.get_prioridad_display|lower }}">
                    {{ recomendacion.get_prioridad_display }}
                </div>
                
                <div class="recommendation-title">
                    {{ recomendacion.titulo }}
                </div>
                
                <div class="recommendation-description">
                    {{ recomendacion.descripcion }}
                </div>
                
                <div class="recommendation-meta">
                    <span>{{ recomendacion.get_tipo_display }}</span>
                    <span>Expira: {{ recomendacion.expires_at|date:"d/m/Y" }}</span>
                </div>
                
                <div class="recommendation-actions">
                    <button class="action-btn btn-apply" onclick="aplicarRecomendacion({{ recomendacion.id }})">
                        ✅ Aplicar
                    </button>
                    <button class="action-btn btn-dismiss" onclick="descartarRecomendacion({{ recomendacion.id }})">
                        ❌ Descartar
                    </button>
                </div>
            </div>
            {% empty %}
            <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                🎉 ¡Excelente! No hay recomendaciones pendientes.
                <br><br>
                <small>Genera nuevas recomendaciones para obtener insights actualizados.</small>
            </div>
            {% endfor %}
        </div>

        <!-- Recomendaciones Aplicadas -->
        <div class="recommendations-section">
            <div class="section-title">
                ✅ Recomendaciones Aplicadas
            </div>
            {% for recomendacion in recomendaciones_aplicadas %}
            <div class="recommendation-item" style="opacity: 0.7;">
                <div class="recommendation-title">
                    {{ recomendacion.titulo }}
                </div>
                
                <div class="recommendation-description">
                    {{ recomendacion.descripcion|truncatewords:15 }}
                </div>
                
                <div class="recommendation-meta">
                    <span>{{ recomendacion.get_tipo_display }}</span>
                    <span>Aplicada: {{ recomendacion.fecha_aplicacion|date:"d/m/Y" }}</span>
                </div>
            </div>
            {% empty %}
            <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                📝 No hay recomendaciones aplicadas recientemente.
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Navegación -->
    <div style="text-align: center; margin-top: 2rem;">
        <a href="{% url 'analytics:dashboard' cliente.id %}" 
           style="background: var(--primary-color); color: white; padding: 1rem 2rem; border-radius: 0.5rem; text-decoration: none; font-weight: 600;">
            ← Volver al Dashboard
        </a>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
function aplicarRecomendacion(id) {
    if (confirm('¿Estás seguro de que quieres marcar esta recomendación como aplicada?')) {
        fetch(`/analytics/recomendacion/${id}/aplicar/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error al aplicar la recomendación');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al aplicar la recomendación');
        });
    }
}

function descartarRecomendacion(id) {
    if (confirm('¿Estás seguro de que quieres descartar esta recomendación?')) {
        // Implementar lógica para descartar recomendación
        alert('Funcionalidad de descartar en desarrollo');
    }
}
</script>
{% endblock %}
'''

# ============================================================================
# 4. TEMPLATE DE PREDICCIONES
# ============================================================================

TEMPLATE_PREDICCIONES = '''
<!-- 🔮 SISTEMA DE PREDICCIONES -->
<!-- Archivo: templates/analytics/predicciones.html -->

{% extends 'base.html' %}
{% load static %}

{% block title %}Predicciones - {{ cliente.nombre }}{% endblock %}

{% block extra_css %}
<link href="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.min.css" rel="stylesheet">
<style>
    :root {
        --primary-color: #3b82f6;
        --secondary-color: #1e40af;
        --accent-color: #06b6d4;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --dark-bg: #0f172a;
        --card-bg: #1e293b;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --border-color: #334155;
    }

    body {
        background: linear-gradient(135deg, var(--dark-bg) 0%, #1e293b 100%);
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        min-height: 100vh;
    }

    .analytics-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 2rem;
    }

    .analytics-header {
        background: linear-gradient(135deg, #8b5cf6, var(--accent-color));
        border-radius: 1rem;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
    }

    .exercise-selector {
        background: var(--card-bg);
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid var(--border-color);
    }

    .exercise-selector select {
        width: 100%;
        padding: 1rem;
        background: var(--dark-bg);
        border: 1px solid var(--border-color);
        border-radius: 0.5rem;
        color: var(--text-primary);
        font-size: 1rem;
    }

    .predictions-grid {
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 2rem;
        margin-bottom: 2rem;
    }

    .chart-card {
        background: var(--card-bg);
        border-radius: 1rem;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
    }

    .chart-title {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .predictions-list {
        background: var(--card-bg);
        border-radius: 1rem;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
    }

    .prediction-item {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(6, 182, 212, 0.1));
        border-radius: 0.75rem;
        padding: 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(139, 92, 246, 0.3);
        position: relative;
    }

    .prediction-item:last-child {
        margin-bottom: 0;
    }

    .prediction-timeframe {
        position: absolute;
        top: 1rem;
        right: 1rem;
        background: rgba(139, 92, 246, 0.2);
        color: #8b5cf6;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .prediction-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }

    .prediction-details {
        color: var(--text-secondary);
        font-size: 0.9rem;
        margin-bottom: 0.75rem;
    }

    .prediction-confidence {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.8rem;
    }

    .confidence-bar {
        flex: 1;
        height: 6px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 3px;
        overflow: hidden;
    }

    .confidence-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--danger-color), var(--warning-color), var(--success-color));
        border-radius: 3px;
        transition: width 0.3s ease;
    }

    .historical-predictions {
        background: var(--card-bg);
        border-radius: 1rem;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
        margin-bottom: 2rem;
    }

    .historical-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 1px solid var(--border-color);
    }

    .historical-item:last-child {
        border-bottom: none;
    }

    .historical-info {
        flex: 1;
    }

    .historical-exercise {
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
    }

    .historical-date {
        font-size: 0.8rem;
        color: var(--text-secondary);
    }

    .historical-prediction {
        text-align: center;
        margin: 0 1rem;
    }

    .historical-prediction-value {
        font-weight: 600;
        color: #8b5cf6;
    }

    .historical-prediction-label {
        font-size: 0.7rem;
        color: var(--text-secondary);
    }

    .historical-status {
        text-align: center;
    }

    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .status-active {
        background: rgba(16, 185, 129, 0.2);
        color: var(--success-color);
    }

    .status-expired {
        background: rgba(107, 114, 128, 0.2);
        color: var(--text-secondary);
    }

    @media (max-width: 768px) {
        .predictions-grid {
            grid-template-columns: 1fr;
        }
        
        .historical-item {
            flex-direction: column;
            gap: 1rem;
            text-align: center;
        }
    }
</style>
{% endblock %}

{% block content %}
<div class="analytics-container">
    <!-- Header -->
    <div class="analytics-header">
        <h1>🔮 Predicciones de Rendimiento</h1>
        <p>Proyecciones inteligentes basadas en tu progreso actual</p>
    </div>

    <!-- Selector de Ejercicio -->
    <div class="exercise-selector">
        <label for="ejercicio-select" style="display: block; margin-bottom: 0.5rem; font-weight: 600;">
            Seleccionar Ejercicio para Predicción:
        </label>
        <select id="ejercicio-select" onchange="cambiarEjercicio()">
            {% for ejercicio in ejercicios %}
            <option value="{{ ejercicio }}" {% if ejercicio == ejercicio_seleccionado %}selected{% endif %}>
                {{ ejercicio }}
            </option>
            {% endfor %}
        </select>
    </div>

    {% if ejercicio_seleccionado and predicciones_data %}
    <!-- Predicciones Actuales -->
    <div class="predictions-grid">
        <div class="chart-card">
            <div class="chart-title">
                📊 Proyección de Progreso - {{ ejercicio_seleccionado }}
            </div>
            <canvas id="predictionsChart" width="400" height="200"></canvas>
        </div>

        <div class="predictions-list">
            <div class="chart-title">
                🎯 Predicciones Calculadas
            </div>
            {% for pred in predicciones_data %}
            <div class="prediction-item">
                <div class="prediction-timeframe">{{ pred.meses }} mes{{ pred.meses|pluralize:"es" }}</div>
                
                <div class="prediction-value">{{ pred.peso_predicho|floatformat:1 }} kg</div>
                
                <div class="prediction-details">
                    Incremento esperado: +{{ pred.incremento_esperado|floatformat:1 }} kg
                    <br>
                    Fecha objetivo: {{ pred.fecha_prediccion|date:"d/m/Y" }}
                </div>
                
                <div class="prediction-confidence">
                    <span>Confianza:</span>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: {{ pred.confianza }}%"></div>
                    </div>
                    <span>{{ pred.confianza }}%</span>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    {% elif ejercicio_seleccionado %}
    <div style="text-align: center; padding: 4rem; color: var(--text-secondary);">
        <h3>📊 Datos Insuficientes</h3>
        <p>Se necesitan al menos 3 registros del ejercicio "{{ ejercicio_seleccionado }}" para generar predicciones precisas.</p>
        <p><small>Continúa entrenando para obtener predicciones personalizadas.</small></p>
    </div>

    {% else %}
    <div style="text-align: center; padding: 4rem; color: var(--text-secondary);">
        <h3>🏋️‍♂️ No hay ejercicios disponibles</h3>
        <p>Realiza algunos entrenamientos para ver predicciones de rendimiento.</p>
    </div>
    {% endif %}

    <!-- Predicciones Históricas -->
    {% if predicciones_bd %}
    <div class="historical-predictions">
        <div class="chart-title">
            📈 Historial de Predicciones
        </div>
        {% for pred in predicciones_bd %}
        <div class="historical-item">
            <div class="historical-info">
                <div class="historical-exercise">{{ pred.nombre_ejercicio }}</div>
                <div class="historical-date">Creada: {{ pred.fecha_prediccion|date:"d/m/Y" }}</div>
            </div>
            
            <div class="historical-prediction">
                <div class="historical-prediction-value">{{ pred.peso_estimado }} kg</div>
                <div class="historical-prediction-label">Predicción</div>
            </div>
            
            <div class="historical-status">
                <div class="status-badge {% if pred.activa %}status-active{% else %}status-expired{% endif %}">
                    {% if pred.activa %}Activa{% else %}Expirada{% endif %}
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <!-- Navegación -->
    <div style="text-align: center; margin-top: 2rem;">
        <a href="{% url 'analytics:dashboard' cliente.id %}" 
           style="background: var(--primary-color); color: white; padding: 1rem 2rem; border-radius: 0.5rem; text-decoration: none; font-weight: 600;">
            ← Volver al Dashboard
        </a>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.min.js"></script>
<script>
function cambiarEjercicio() {
    const select = document.getElementById('ejercicio-select');
    const ejercicio = select.value;
    if (ejercicio) {
        window.location.href = `?ejercicio=${encodeURIComponent(ejercicio)}`;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    {% if predicciones_data %}
    const prediccionesData = {{ predicciones_data|safe }};
    
    if (prediccionesData && prediccionesData.length > 0) {
        const ctx = document.getElementById('predictionsChart');
        
        // Preparar datos para el gráfico
        const labels = ['Actual'].concat(prediccionesData.map(p => `${p.meses} mes${p.meses > 1 ? 'es' : ''}`));
        const valores = [prediccionesData[0].peso_actual].concat(prediccionesData.map(p => p.peso_predicho));
        const colores = ['#10b981'].concat(prediccionesData.map(() => '#8b5cf6'));
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Peso (kg)',
                    data: valores,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: colores,
                    pointBorderColor: colores,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f8fafc'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                if (context.dataIndex === 0) {
                                    return 'Peso actual';
                                } else {
                                    const pred = prediccionesData[context.dataIndex - 1];
                                    return `Confianza: ${pred.confianza}%`;
                                }
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        ticks: {
                            color: '#cbd5e1'
                        },
                        grid: {
                            color: '#334155'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#cbd5e1'
                        },
                        grid: {
                            color: '#334155'
                        }
                    }
                }
            }
        });
    }
    {% endif %}
});
</script>
{% endblock %}
'''

print("📊 TEMPLATES COMPLETOS CREADOS:")
print("1. templates/analytics/progresion.html")
print("2. templates/analytics/comparativas.html") 
print("3. templates/analytics/recomendaciones.html")
print("4. templates/analytics/predicciones.html")

