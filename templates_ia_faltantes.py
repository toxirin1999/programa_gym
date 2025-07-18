#!/usr/bin/env python3
# 🎨 GENERADOR DE TEMPLATES HTML FALTANTES PARA IA

import os

def crear_templates_faltantes():
    """Crea todos los templates HTML que faltan para el sistema de IA"""
    
    # Crear directorio si no existe
    os.makedirs('templates/analytics', exist_ok=True)
    
    # Template: recomendaciones_inteligentes.html
    template_recomendaciones = '''{% extends "base.html" %}
{% load static %}

{% block title %}Recomendaciones Inteligentes - Centro de IA{% endblock %}

{% block extra_css %}
<style>
    .ia-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        padding: 20px;
    }
    
    .recomendacion-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border-left: 5px solid #667eea;
    }
    
    .categoria-header {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
    }
    
    .categoria-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 15px;
        font-size: 18px;
    }
    
    .ejercicios-nuevos { background: #e3f2fd; color: #1976d2; }
    .progresion { background: #f3e5f5; color: #7b1fa2; }
    .equilibrio { background: #e8f5e8; color: #388e3c; }
    .periodizacion { background: #fff3e0; color: #f57c00; }
    .recuperacion { background: #fce4ec; color: #c2185b; }
    .nutricion { background: #e0f2f1; color: #00695c; }
    
    .recomendacion-item {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 3px solid #667eea;
    }
    
    .prioridad-alta { border-left-color: #f44336; }
    .prioridad-media { border-left-color: #ff9800; }
    .prioridad-baja { border-left-color: #4caf50; }
    
    .confianza-badge {
        background: linear-gradient(45deg, #4caf50, #8bc34a);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .perfil-usuario {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .stat-item {
        text-align: center;
        padding: 10px;
    }
    
    .stat-value {
        font-size: 24px;
        font-weight: bold;
        color: #667eea;
    }
    
    .stat-label {
        font-size: 12px;
        color: #666;
        text-transform: uppercase;
    }
</style>
{% endblock %}

{% block content %}
<div class="ia-container">
    <div class="container-fluid">
        <!-- Header -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h1 class="text-white mb-0">🧠 Recomendaciones Inteligentes</h1>
                        <p class="text-white-50">Sistema de IA personalizado para {{ cliente.nombre }}</p>
                    </div>
                    <div class="confianza-badge">
                        Confianza: {{ recomendaciones.confianza_sistema }}%
                    </div>
                </div>
            </div>
        </div>

        <!-- Perfil del Usuario -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="perfil-usuario">
                    <h5 class="mb-3">📊 Perfil Analizado</h5>
                    <div class="row">
                        <div class="col-md-2">
                            <div class="stat-item">
                                <div class="stat-value">{{ recomendaciones.perfil_usuario.nivel_experiencia|title }}</div>
                                <div class="stat-label">Nivel</div>
                            </div>
                        </div>
                        <div class="col-md-2">
                            <div class="stat-item">
                                <div class="stat-value">{{ recomendaciones.perfil_usuario.frecuencia_entrenamiento|floatformat:1 }}</div>
                                <div class="stat-label">Días/Semana</div>
                            </div>
                        </div>
                        <div class="col-md-2">
                            <div class="stat-item">
                                <div class="stat-value">{{ recomendaciones.perfil_usuario.consistencia|floatformat:0 }}%</div>
                                <div class="stat-label">Consistencia</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="stat-item">
                                <div class="stat-value">{{ recomendaciones.perfil_usuario.intensidad_promedio|floatformat:0 }} min</div>
                                <div class="stat-label">Duración Promedio</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="stat-item">
                                <div class="stat-value">{{ recomendaciones.perfil_usuario.progreso_reciente.porcentaje_mejora|floatformat:1 }}%</div>
                                <div class="stat-label">Progreso Reciente</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recomendaciones por Categoría -->
        <div class="row">
            <!-- Ejercicios Nuevos -->
            <div class="col-lg-6 mb-4">
                <div class="recomendacion-card">
                    <div class="categoria-header">
                        <div class="categoria-icon ejercicios-nuevos">💪</div>
                        <h5 class="mb-0">Ejercicios Nuevos</h5>
                    </div>
                    {% for recomendacion in recomendaciones.recomendaciones.ejercicios_nuevos %}
                    <div class="recomendacion-item prioridad-{{ recomendacion.prioridad }}">
                        <strong>{{ recomendacion.grupo_muscular|title }}</strong>
                        <p class="mb-1">{{ recomendacion.razon }}</p>
                        <small class="text-muted">
                            Ejercicios sugeridos: {{ recomendacion.ejercicios_sugeridos|join:", " }}
                        </small>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Progresión Inteligente -->
            <div class="col-lg-6 mb-4">
                <div class="recomendacion-card">
                    <div class="categoria-header">
                        <div class="categoria-icon progresion">📈</div>
                        <h5 class="mb-0">Progresión Inteligente</h5>
                    </div>
                    {% for recomendacion in recomendaciones.recomendaciones.progresion_inteligente %}
                    <div class="recomendacion-item">
                        <strong>{{ recomendacion.ejercicio }}</strong>
                        <p class="mb-1">{{ recomendacion.sugerencia }}</p>
                        <small class="text-muted">{{ recomendacion.razon }}</small>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Equilibrio Muscular -->
            <div class="col-lg-6 mb-4">
                <div class="recomendacion-card">
                    <div class="categoria-header">
                        <div class="categoria-icon equilibrio">⚖️</div>
                        <h5 class="mb-0">Equilibrio Muscular</h5>
                    </div>
                    {% for recomendacion in recomendaciones.recomendaciones.equilibrio_muscular %}
                    <div class="recomendacion-item">
                        <strong>{{ recomendacion.ratio|title }}</strong>
                        <p class="mb-1">{{ recomendacion.recomendacion }}</p>
                        <small class="text-muted">
                            Actual: {{ recomendacion.valor_actual|floatformat:2 }} | 
                            Ideal: {{ recomendacion.valor_ideal|floatformat:2 }}
                        </small>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Periodización -->
            <div class="col-lg-6 mb-4">
                <div class="recomendacion-card">
                    <div class="categoria-header">
                        <div class="categoria-icon periodizacion">📅</div>
                        <h5 class="mb-0">Periodización Personalizada</h5>
                    </div>
                    <div class="recomendacion-item">
                        <strong>{{ recomendaciones.recomendaciones.periodizacion.tipo|title }}</strong>
                        <p class="mb-1">Duración de fase: {{ recomendaciones.recomendaciones.periodizacion.duracion_fase }}</p>
                        <p class="mb-1">Incrementos: {{ recomendaciones.recomendaciones.periodizacion.incrementos }}</p>
                        <small class="text-muted">
                            Deload: {{ recomendaciones.recomendaciones.periodizacion.deload_frecuencia }}
                        </small>
                    </div>
                </div>
            </div>

            <!-- Recuperación -->
            <div class="col-lg-6 mb-4">
                <div class="recomendacion-card">
                    <div class="categoria-header">
                        <div class="categoria-icon recuperacion">😴</div>
                        <h5 class="mb-0">Recuperación Optimizada</h5>
                    </div>
                    <div class="recomendacion-item">
                        <strong>Nivel de Fatiga: {{ recomendaciones.recomendaciones.recuperacion.nivel_fatiga|title }}</strong>
                        {% for estrategia in recomendaciones.recomendaciones.recuperacion.estrategias_recomendadas %}
                        <p class="mb-1">• {{ estrategia }}</p>
                        {% endfor %}
                        <small class="text-muted">
                            Masajes: {{ recomendaciones.recomendaciones.recuperacion.frecuencia_masajes }}
                        </small>
                    </div>
                </div>
            </div>

            <!-- Nutrición y Timing -->
            <div class="col-lg-6 mb-4">
                <div class="recomendacion-card">
                    <div class="categoria-header">
                        <div class="categoria-icon nutricion">🥗</div>
                        <h5 class="mb-0">Nutrición y Timing</h5>
                    </div>
                    <div class="recomendacion-item">
                        <strong>Pre-Entreno</strong>
                        <p class="mb-1">{{ recomendaciones.recomendaciones.nutricion_timing.pre_entreno.timing }}</p>
                        <small class="text-muted">{{ recomendaciones.recomendaciones.nutricion_timing.pre_entreno.ejemplo }}</small>
                    </div>
                    <div class="recomendacion-item">
                        <strong>Post-Entreno</strong>
                        <p class="mb-1">{{ recomendaciones.recomendaciones.nutricion_timing.post_entreno.timing }}</p>
                        <small class="text-muted">{{ recomendaciones.recomendaciones.nutricion_timing.post_entreno.ejemplo }}</small>
                    </div>
                </div>
            </div>
        </div>

        <!-- Objetivos SMART -->
        <div class="row">
            <div class="col-12">
                <div class="recomendacion-card">
                    <h5 class="mb-3">🎯 Objetivos SMART Generados</h5>
                    <div class="row">
                        {% for objetivo in recomendaciones.recomendaciones.objetivos_smart %}
                        <div class="col-md-6 mb-3">
                            <div class="recomendacion-item">
                                <strong>{{ objetivo.objetivo }}</strong>
                                <p class="mb-1"><strong>Específico:</strong> {{ objetivo.especifico }}</p>
                                <p class="mb-1"><strong>Medible:</strong> {{ objetivo.medible }}</p>
                                <p class="mb-1"><strong>Tiempo:</strong> {{ objetivo.tiempo }}</p>
                                <small class="text-muted">{{ objetivo.relevante }}</small>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>

        <!-- Navegación -->
        <div class="row mt-4">
            <div class="col-12 text-center">
                <a href="{% url 'analytics:dashboard_ia' cliente.id %}" class="btn btn-light btn-lg me-3">
                    ← Volver al Dashboard IA
                </a>
                <a href="{% url 'analytics:patrones' cliente.id %}" class="btn btn-outline-light btn-lg">
                    Análisis de Patrones →
                </a>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

    # Template: deteccion_patrones.html
    template_patrones = '''{% extends "base.html" %}
{% load static %}

{% block title %}Detección de Patrones - Centro de IA{% endblock %}

{% block extra_css %}
<style>
    .ia-container {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        min-height: 100vh;
        padding: 20px;
    }
    
    .patron-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border-left: 5px solid #11998e;
    }
    
    .patron-header {
        display: flex;
        align-items: center;
        justify-content: between;
        margin-bottom: 15px;
    }
    
    .patron-icon {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 15px;
        font-size: 20px;
        background: linear-gradient(45deg, #11998e, #38ef7d);
        color: white;
    }
    
    .confianza-badge {
        background: linear-gradient(45deg, #4caf50, #8bc34a);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        margin-left: auto;
    }
    
    .patron-item {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 3px solid #11998e;
    }
    
    .patron-temporal { border-left-color: #2196f3; }
    .patron-rendimiento { border-left-color: #ff9800; }
    .patron-comportamiento { border-left-color: #9c27b0; }
    .patron-correlacion { border-left-color: #f44336; }
    
    .estancamiento-card {
        border-left-color: #f44336;
    }
    
    .severidad-alta { background: #ffebee; }
    .severidad-media { background: #fff3e0; }
    .severidad-baja { background: #e8f5e8; }
    
    .anomalia-card {
        border-left-color: #ff5722;
    }
    
    .pico-valle-card {
        border-left-color: #673ab7;
    }
    
    .chart-container {
        height: 300px;
        margin: 20px 0;
    }
    
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 15px;
        margin-bottom: 20px;
    }
    
    .stat-item {
        text-align: center;
        padding: 15px;
        background: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
    }
    
    .stat-value {
        font-size: 24px;
        font-weight: bold;
        color: #11998e;
    }
    
    .stat-label {
        font-size: 12px;
        color: #666;
        text-transform: uppercase;
    }
</style>
{% endblock %}

{% block content %}
<div class="ia-container">
    <div class="container-fluid">
        <!-- Header -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h1 class="text-white mb-0">🔍 Detección de Patrones</h1>
                        <p class="text-white-50">Análisis automático de patrones para {{ cliente.nombre }}</p>
                    </div>
                    <div class="confianza-badge">
                        Confianza: {{ patrones.confianza_deteccion|floatformat:0 }}%
                    </div>
                </div>
            </div>
        </div>

        <!-- Estadísticas Generales -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="stat-grid">
                    <div class="stat-item">
                        <div class="stat-value">{{ patrones.total_patrones }}</div>
                        <div class="stat-label">Patrones Detectados</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{ estancamientos.total_estancamientos }}</div>
                        <div class="stat-label">Estancamientos</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{ anomalias.total_anomalias }}</div>
                        <div class="stat-label">Anomalías</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{ picos_valles.total_eventos }}</div>
                        <div class="stat-label">Picos y Valles</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{ recuperacion.tiempo_recuperacion_ideal|floatformat:1 }}</div>
                        <div class="stat-label">Días Recuperación</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Patrones Detectados -->
        <div class="row">
            <div class="col-lg-6 mb-4">
                <div class="patron-card">
                    <div class="patron-header">
                        <div class="patron-icon">🔄</div>
                        <h5 class="mb-0">Patrones Generales</h5>
                    </div>
                    {% for patron in patrones.patrones_detectados %}
                    <div class="patron-item patron-{{ patron.tipo|slice:"7:" }}">
                        <strong>{{ patron.categoria|title }}</strong>
                        <p class="mb-1">{{ patron.descripcion }}</p>
                        <small class="text-muted">Confianza: {{ patron.confianza|floatformat:0 }}%</small>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Estancamientos -->
            <div class="col-lg-6 mb-4">
                <div class="patron-card estancamiento-card">
                    <div class="patron-header">
                        <div class="patron-icon">⏸️</div>
                        <h5 class="mb-0">Estancamientos Detectados</h5>
                    </div>
                    {% for estancamiento in estancamientos.estancamientos_detectados %}
                    <div class="patron-item severidad-{{ estancamiento.severidad|floatformat:0|add:0|divisibleby:3|yesno:"baja,media,alta" }}">
                        <strong>{{ estancamiento.ejercicio }}</strong>
                        <p class="mb-1">Duración: {{ estancamiento.duracion_semanas }} semanas</p>
                        <p class="mb-1">Severidad: {{ estancamiento.severidad|floatformat:1 }}/1.0</p>
                        <small class="text-muted">
                            Último progreso: {{ estancamiento.ultimo_progreso }}
                        </small>
                        <div class="mt-2">
                            <strong>Recomendaciones:</strong>
                            {% for rec in estancamiento.recomendaciones %}
                            <br><small>• {{ rec }}</small>
                            {% endfor %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Picos y Valles -->
            <div class="col-lg-6 mb-4">
                <div class="patron-card pico-valle-card">
                    <div class="patron-header">
                        <div class="patron-icon">📊</div>
                        <h5 class="mb-0">Picos y Valles de Rendimiento</h5>
                    </div>
                    
                    <h6 class="text-success">🔺 Picos de Rendimiento</h6>
                    {% for pico in picos_valles.picos_detectados %}
                    <div class="patron-item">
                        <strong>{{ pico.fecha }}</strong>
                        <p class="mb-1">Rendimiento: {{ pico.valor_rendimiento|floatformat:2 }}</p>
                        <small class="text-muted">{{ pico.contexto.posible_causa }}</small>
                    </div>
                    {% endfor %}
                    
                    <h6 class="text-danger mt-3">🔻 Valles de Rendimiento</h6>
                    {% for valle in picos_valles.valles_detectados %}
                    <div class="patron-item">
                        <strong>{{ valle.fecha }}</strong>
                        <p class="mb-1">Rendimiento: {{ valle.valor_rendimiento|floatformat:2 }}</p>
                        <small class="text-muted">{{ valle.contexto.posible_causa }}</small>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Anomalías -->
            <div class="col-lg-6 mb-4">
                <div class="patron-card anomalia-card">
                    <div class="patron-header">
                        <div class="patron-icon">⚠️</div>
                        <h5 class="mb-0">Anomalías de Comportamiento</h5>
                    </div>
                    <p class="text-muted">{{ anomalias.porcentaje_anomalias|floatformat:1 }}% de sesiones anómalas</p>
                    
                    {% for anomalia in anomalias.anomalias_detectadas %}
                    <div class="patron-item">
                        <strong>{{ anomalia.fecha }}</strong>
                        <p class="mb-1">Tipo: {{ anomalia.tipo_anomalia|title }}</p>
                        <p class="mb-1">Desviación: {{ anomalia.desviacion_estandar|floatformat:1 }}σ</p>
                        <small class="text-muted">{{ anomalia.posible_causa }}</small>
                    </div>
                    {% endfor %}
                    
                    <div class="mt-3">
                        <strong>Recomendaciones de Corrección:</strong>
                        {% for rec in anomalias.recomendaciones_correccion %}
                        <br><small>• {{ rec }}</small>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <!-- Patrones de Recuperación -->
            <div class="col-12 mb-4">
                <div class="patron-card">
                    <div class="patron-header">
                        <div class="patron-icon">💤</div>
                        <h5 class="mb-0">Patrones de Recuperación</h5>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-4">
                            <h6>Patrón Óptimo</h6>
                            <div class="patron-item">
                                <strong>{{ recuperacion.patron_optimo.descripcion }}</strong>
                                <p class="mb-1">Tiempo: {{ recuperacion.patron_optimo.tiempo_descanso_promedio|floatformat:1 }} días</p>
                                <p class="mb-1">Calidad: {{ recuperacion.patron_optimo.calidad_sesion_promedio|floatformat:2 }}</p>
                                <small class="text-muted">
                                    Eficiencia: {{ recuperacion.patron_optimo.eficiencia_recuperacion|floatformat:2 }}
                                </small>
                            </div>
                        </div>
                        
                        <div class="col-md-8">
                            <h6>Recomendaciones</h6>
                            {% for rec in recuperacion.recomendaciones_recuperacion %}
                            <div class="patron-item">
                                <p class="mb-0">• {{ rec }}</p>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Navegación -->
        <div class="row mt-4">
            <div class="col-12 text-center">
                <a href="{% url 'analytics:dashboard_ia' cliente.id %}" class="btn btn-light btn-lg me-3">
                    ← Volver al Dashboard IA
                </a>
                <a href="{% url 'analytics:optimizacion' cliente.id %}" class="btn btn-outline-light btn-lg">
                    Optimización →
                </a>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
// Aquí se pueden agregar gráficos interactivos para visualizar patrones
</script>
{% endblock %}'''

    # Template: optimizacion_entrenamientos.html
    template_optimizacion = '''{% extends "base.html" %}
{% load static %}

{% block title %}Optimización de Entrenamientos - Centro de IA{% endblock %}

{% block extra_css %}
<style>
    .ia-container {
        background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%);
        min-height: 100vh;
        padding: 20px;
    }
    
    .optimizacion-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border-left: 5px solid #ff6b6b;
    }
    
    .optimizacion-header {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
    }
    
    .optimizacion-icon {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 15px;
        font-size: 20px;
        background: linear-gradient(45deg, #ff6b6b, #feca57);
        color: white;
    }
    
    .mejora-badge {
        background: linear-gradient(45deg, #4caf50, #8bc34a);
        color: white;
        padding: 8px 20px;
        border-radius: 25px;
        font-size: 14px;
        font-weight: bold;
        margin-left: auto;
    }
    
    .algoritmo-badge {
        background: #2196f3;
        color: white;
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 11px;
        font-weight: bold;
    }
    
    .rutina-item {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 3px solid #ff6b6b;
    }
    
    .sesion-item {
        background: #fff3cd;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 3px solid #feca57;
    }
    
    .periodizacion-item {
        background: #d1ecf1;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 3px solid #17a2b8;
    }
    
    .recuperacion-item {
        background: #d4edda;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 3px solid #28a745;
    }
    
    .carga-item {
        background: #f8d7da;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 3px solid #dc3545;
    }
    
    .progress-custom {
        height: 25px;
        border-radius: 15px;
        background: rgba(255, 255, 255, 0.3);
    }
    
    .progress-bar-custom {
        background: linear-gradient(45deg, #4caf50, #8bc34a);
        border-radius: 15px;
    }
    
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 15px;
        margin-bottom: 20px;
    }
    
    .stat-item {
        text-align: center;
        padding: 15px;
        background: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
    }
    
    .stat-value {
        font-size: 24px;
        font-weight: bold;
        color: #ff6b6b;
    }
    
    .stat-label {
        font-size: 12px;
        color: #666;
        text-transform: uppercase;
    }
    
    .comparacion-algoritmos {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        padding: 15px;
        margin-top: 15px;
    }
</style>
{% endblock %}

{% block content %}
<div class="ia-container">
    <div class="container-fluid">
        <!-- Header -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h1 class="text-white mb-0">⚡ Optimización de Entrenamientos</h1>
                        <p class="text-white-50">Sistema de optimización avanzada para {{ cliente.nombre }}</p>
                    </div>
                    <div class="mejora-badge">
                        Mejora Estimada: {{ rutina_completa.mejora_estimada|floatformat:1 }}%
                    </div>
                </div>
            </div>
        </div>

        <!-- Estadísticas de Optimización -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="stat-grid">
                    <div class="stat-item">
                        <div class="stat-value">{{ rutina_completa.confianza_optimizacion|floatformat:0 }}%</div>
                        <div class="stat-label">Confianza</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{ rutina_completa.duracion_semanas }}</div>
                        <div class="stat-label">Semanas</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{ rutina_completa.algoritmo_usado }}</div>
                        <div class="stat-label">Algoritmo</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{ sesion_individual.tiempo_estimado }}</div>
                        <div class="stat-label">Duración Sesión</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{ carga_adaptativa.ajuste_recomendado|floatformat:1 }}%</div>
                        <div class="stat-label">Ajuste Carga</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Rutina Optimizada -->
        <div class="row">
            <div class="col-lg-6 mb-4">
                <div class="optimizacion-card">
                    <div class="optimizacion-header">
                        <div class="optimizacion-icon">🏋️</div>
                        <h5 class="mb-0">Rutina Completa Optimizada</h5>
                        <span class="algoritmo-badge">{{ rutina_completa.algoritmo_usado }}</span>
                    </div>
                    
                    <div class="rutina-item">
                        <strong>Frecuencia Semanal</strong>
                        <p class="mb-1">{{ rutina_completa.rutina_optimizada.dias_semana }} días por semana</p>
                        <small class="text-muted">Ejercicios por día: {{ rutina_completa.rutina_optimizada.ejercicios_por_dia }}</small>
                    </div>
                    
                    <div class="rutina-item">
                        <strong>Estructura de Series</strong>
                        <p class="mb-1">{{ rutina_completa.rutina_optimizada.series_por_ejercicio }} series por ejercicio</p>
                        <small class="text-muted">
                            Repeticiones: {{ rutina_completa.rutina_optimizada.repeticiones_objetivo.0 }}-{{ rutina_completa.rutina_optimizada.repeticiones_objetivo.1 }}
                        </small>
                    </div>
                    
                    <div class="rutina-item">
                        <strong>Intensidad y Descanso</strong>
                        <p class="mb-1">Intensidad: {{ rutina_completa.rutina_optimizada.intensidad_promedio|floatformat:0 }}% 1RM</p>
                        <small class="text-muted">Descanso: {{ rutina_completa.rutina_optimizada.descanso_series }}s entre series</small>
                    </div>
                    
                    <div class="rutina-item">
                        <strong>Distribución Muscular</strong>
                        {% for grupo, porcentaje in rutina_completa.rutina_optimizada.distribucion_muscular.items %}
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span>{{ grupo|title }}</span>
                            <span>{{ porcentaje|floatformat:0 }}%</span>
                        </div>
                        <div class="progress progress-custom mb-2" style="height: 8px;">
                            <div class="progress-bar progress-bar-custom" style="width: {{ porcentaje }}%"></div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <!-- Sesión Individual -->
            <div class="col-lg-6 mb-4">
                <div class="optimizacion-card">
                    <div class="optimizacion-header">
                        <div class="optimizacion-icon">📅</div>
                        <h5 class="mb-0">Sesión Individual Optimizada</h5>
                        <span class="algoritmo-badge">{{ sesion_individual.nivel_dificultad|title }}</span>
                    </div>
                    
                    <div class="sesion-item">
                        <strong>Ejercicios Recomendados</strong>
                        {% for ejercicio in sesion_individual.sesion_optimizada.ejercicios_recomendados %}
                        <p class="mb-1">• {{ ejercicio }}</p>
                        {% endfor %}
                    </div>
                    
                    <div class="sesion-item">
                        <strong>Series por Ejercicio</strong>
                        {% for series in sesion_individual.sesion_optimizada.series_por_ejercicio %}
                        <span class="badge bg-secondary me-1">{{ series }}</span>
                        {% endfor %}
                    </div>
                    
                    <div class="sesion-item">
                        <strong>Adaptaciones Realizadas</strong>
                        {% for adaptacion in sesion_individual.adaptaciones_realizadas %}
                        <p class="mb-1">• {{ adaptacion }}</p>
                        {% endfor %}
                    </div>
                    
                    <div class="sesion-item">
                        <strong>Tiempo Estimado</strong>
                        <p class="mb-0">{{ sesion_individual.tiempo_estimado }}</p>
                    </div>
                </div>
            </div>

            <!-- Periodización Automática -->
            <div class="col-lg-6 mb-4">
                <div class="optimizacion-card">
                    <div class="optimizacion-header">
                        <div class="optimizacion-icon">📊</div>
                        <h5 class="mb-0">Periodización Automática</h5>
                    </div>
                    
                    <div class="periodizacion-item">
                        <strong>Modelo Óptimo: {{ periodizacion.modelo_optimo|title }}</strong>
                        <p class="mb-1">Puntuación: {{ periodizacion.puntuacion_optimizacion|floatformat:1 }}/10</p>
                    </div>
                    
                    <div class="periodizacion-item">
                        <strong>Fases de Periodización</strong>
                        {% for fase in periodizacion.fases_periodizacion %}
                        <p class="mb-1">• {{ fase|title }}</p>
                        {% endfor %}
                    </div>
                    
                    <div class="periodizacion-item">
                        <strong>Adaptaciones Personalizadas</strong>
                        {% for adaptacion in periodizacion.adaptaciones_personalizadas %}
                        <p class="mb-1">• {{ adaptacion }}</p>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <!-- Recuperación Inteligente -->
            <div class="col-lg-6 mb-4">
                <div class="optimizacion-card">
                    <div class="optimizacion-header">
                        <div class="optimizacion-icon">💤</div>
                        <h5 class="mb-0">Recuperación Inteligente</h5>
                    </div>
                    
                    <div class="recuperacion-item">
                        <strong>Descanso Entre Series</strong>
                        <p class="mb-1">{{ recuperacion.optimizaciones_recuperacion.descanso_entre_series.descanso_optimo }}</p>
                    </div>
                    
                    <div class="recuperacion-item">
                        <strong>Descanso Entre Sesiones</strong>
                        <p class="mb-1">Óptimo: {{ recuperacion.optimizaciones_recuperacion.descanso_entre_sesiones.descanso_optimo }}h</p>
                        <small class="text-muted">Mínimo: {{ recuperacion.optimizaciones_recuperacion.descanso_entre_sesiones.descanso_minimo }}h</small>
                    </div>
                    
                    <div class="recuperacion-item">
                        <strong>Recuperación Activa</strong>
                        <p class="mb-1">{{ recuperacion.optimizaciones_recuperacion.estrategias_recuperacion_activa.duracion_optima }}</p>
                        <small class="text-muted">
                            Actividades: {{ recuperacion.optimizaciones_recuperacion.estrategias_recuperacion_activa.actividades_recomendadas|join:", " }}
                        </small>
                    </div>
                    
                    <div class="recuperacion-item">
                        <strong>Deload Automático</strong>
                        <p class="mb-1">{{ recuperacion.optimizaciones_recuperacion.periodizacion_deload.frecuencia_deload|title }}</p>
                        <small class="text-muted">Reducción: {{ recuperacion.optimizaciones_recuperacion.periodizacion_deload.reduccion_volumen }}</small>
                    </div>
                </div>
            </div>

            <!-- Carga Adaptativa -->
            <div class="col-12 mb-4">
                <div class="optimizacion-card">
                    <div class="optimizacion-header">
                        <div class="optimizacion-icon">⚖️</div>
                        <h5 class="mb-0">Optimización de Carga Adaptativa</h5>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-4">
                            <div class="carga-item">
                                <strong>Carga Actual</strong>
                                <p class="mb-1">{{ carga_adaptativa.carga_actual }}% de capacidad</p>
                                <div class="progress progress-custom">
                                    <div class="progress-bar progress-bar-custom" style="width: {{ carga_adaptativa.carga_actual }}%"></div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-4">
                            <div class="carga-item">
                                <strong>Carga Optimizada</strong>
                                <p class="mb-1">{{ carga_adaptativa.carga_optimizada }}% de capacidad</p>
                                <div class="progress progress-custom">
                                    <div class="progress-bar progress-bar-custom" style="width: {{ carga_adaptativa.carga_optimizada }}%"></div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-4">
                            <div class="carga-item">
                                <strong>Ajuste Recomendado</strong>
                                <p class="mb-1">{{ carga_adaptativa.ajuste_recomendado|floatformat:1 }}%</p>
                                <small class="text-muted">{{ carga_adaptativa.justificacion }}</small>
                            </div>
                        </div>
                    </div>
                    
                    <div class="carga-item mt-3">
                        <strong>Implementación Gradual</strong>
                        {% for semana, descripcion in carga_adaptativa.implementacion_gradual.items %}
                        <p class="mb-1"><strong>{{ semana|title }}:</strong> {{ descripcion }}</p>
                        {% endfor %}
                    </div>
                    
                    <div class="carga-item">
                        <strong>Monitoreo Recomendado</strong>
                        <p class="mb-1">Frecuencia: {{ carga_adaptativa.monitoreo_recomendado.frecuencia_evaluacion }}</p>
                        <p class="mb-1">Indicadores: {{ carga_adaptativa.monitoreo_recomendado.indicadores_clave|join:", " }}</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Comparación de Algoritmos -->
        <div class="row">
            <div class="col-12 mb-4">
                <div class="optimizacion-card">
                    <div class="optimizacion-header">
                        <div class="optimizacion-icon">🔬</div>
                        <h5 class="mb-0">Comparación de Algoritmos</h5>
                    </div>
                    
                    <div class="comparacion-algoritmos">
                        <div class="row">
                            {% for algoritmo, metricas in rutina_completa.comparacion_algoritmos.items %}
                            <div class="col-md-3 mb-3">
                                <div class="text-center">
                                    <h6>{{ algoritmo|title }}</h6>
                                    <div class="stat-value" style="font-size: 18px;">{{ metricas.mejora_estimada|floatformat:1 }}%</div>
                                    <div class="stat-label">Mejora Estimada</div>
                                    <small class="text-muted">
                                        Confianza: {{ metricas.confianza|floatformat:0 }}% | 
                                        Iteraciones: {{ metricas.iteraciones }}
                                    </small>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Navegación -->
        <div class="row mt-4">
            <div class="col-12 text-center">
                <a href="{% url 'analytics:dashboard_ia' cliente.id %}" class="btn btn-light btn-lg me-3">
                    ← Volver al Dashboard IA
                </a>
                <a href="{% url 'analytics:predicciones' cliente.id %}" class="btn btn-outline-light btn-lg">
                    Predicciones →
                </a>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

    # Escribir los archivos
    with open('templates/analytics/recomendaciones_inteligentes.html', 'w', encoding='utf-8') as f:
        f.write(template_recomendaciones)
    
    with open('templates/analytics/deteccion_patrones.html', 'w', encoding='utf-8') as f:
        f.write(template_patrones)
    
    with open('templates/analytics/optimizacion_entrenamientos.html', 'w', encoding='utf-8') as f:
        f.write(template_optimizacion)
    
    print("✅ Templates HTML creados exitosamente:")
    print("   - templates/analytics/recomendaciones_inteligentes.html")
    print("   - templates/analytics/deteccion_patrones.html") 
    print("   - templates/analytics/optimizacion_entrenamientos.html")

if __name__ == "__main__":
    crear_templates_faltantes()

