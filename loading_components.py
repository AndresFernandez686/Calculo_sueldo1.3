"""
Módulo de componentes de Loading
Proporciona componentes visuales de carga para mejorar la experiencia del usuario
"""
import streamlit as st
import time
from contextlib import contextmanager

def mostrar_loading_simple(texto="Procesando..."):
    """
    Muestra un indicador de carga simple con texto
    
    Args:
        texto: Texto a mostrar durante la carga
    """
    st.markdown(f"""
    <div class="loading-container">
        <div class="loading-spinner"></div>
        <div class="loading-text">{texto}</div>
        <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def mostrar_loading_procesamiento(texto="Procesando datos", subtexto="Por favor espera..."):
    """
    Muestra un indicador de carga para procesamiento de datos
    
    Args:
        texto: Texto principal
        subtexto: Texto secundario explicativo
    """
    st.markdown(f"""
    <div class="processing-loader">
        <div class="icon">🔄</div>
        <div class="loading-text">{texto}</div>
        <div class="loading-subtext">{subtexto}</div>
        <div class="progress-bar-container">
            <div class="progress-bar"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def mostrar_loading_validacion(texto="Validando datos..."):
    """
    Muestra un indicador de carga para validación
    
    Args:
        texto: Texto a mostrar durante la validación
    """
    st.markdown(f"""
    <div class="validation-loader">
        <div class="loading-text">⚠️ {texto}</div>
        <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def mostrar_loading_pdf(cantidad_archivos=1):
    """
    Muestra un indicador de carga específico para procesamiento de PDFs
    
    Args:
        cantidad_archivos: Número de PDFs siendo procesados
    """
    texto = f"Procesando {cantidad_archivos} PDF{'s' if cantidad_archivos > 1 else ''}"
    subtexto = "Extrayendo datos de asistencia automáticamente..."
    
    st.markdown(f"""
    <div class="processing-loader">
        <div class="loading-text">{texto}</div>
        <div class="loading-subtext">{subtexto}</div>
        <div class="progress-bar-container">
            <div class="progress-bar"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def mostrar_loading_excel():
    """
    Muestra un indicador de carga específico para procesamiento de Excel
    """
    st.markdown("""
    <div class="processing-loader">
        <div class="loading-text">Procesando archivo Excel</div>
        <div class="loading-subtext">Leyendo y validando datos...</div>
        <div class="progress-bar-container">
            <div class="progress-bar"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def mostrar_loading_calculos():
    """
    Muestra un indicador de carga para el cálculo de sueldos
    """
    st.markdown("""
    <div class="loading-container">
        <div class="loading-spinner"></div>
        <div class="loading-text"> Calculando sueldos</div>
        <div class="loading-subtext">Procesando horas, feriados y descuentos...</div>
        <div class="progress-bar-container">
            <div class="progress-bar"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

@contextmanager
def loading_context(tipo="simple", texto="Procesando..."):
    """
    Context manager para mostrar loading durante operaciones
    
    Uso:
        with loading_context("procesamiento", "Calculando datos"):
            # Tu código aquí
            resultado = procesar_datos()
    
    Args:
        tipo: Tipo de loading ("simple", "procesamiento", "validacion", "calculos")
        texto: Texto a mostrar
    """
    # Crear un placeholder para el loading
    placeholder = st.empty()
    
    with placeholder.container():
        if tipo == "simple":
            mostrar_loading_simple(texto)
        elif tipo == "procesamiento":
            mostrar_loading_procesamiento(texto)
        elif tipo == "validacion":
            mostrar_loading_validacion(texto)
        elif tipo == "calculos":
            mostrar_loading_calculos()
        elif tipo == "pdf":
            mostrar_loading_pdf()
        elif tipo == "excel":
            mostrar_loading_excel()
    
    try:
        yield placeholder
    finally:
        # Limpiar el loading cuando termine la operación
        placeholder.empty()

def mostrar_skeleton_tabla(num_filas=5):
    """
    Muestra un skeleton loader para una tabla mientras se carga
    
    Args:
        num_filas: Número de filas del skeleton
    """
    html_skeleton = "<div style='padding: 1rem;'>"
    for _ in range(num_filas):
        html_skeleton += """
        <div class="skeleton-loader" style="height: 30px; margin: 0.5rem 0;"></div>
        """
    html_skeleton += "</div>"
    
    st.markdown(html_skeleton, unsafe_allow_html=True)

def mostrar_progreso_con_porcentaje(porcentaje, texto="Procesando"):
    """
    Muestra una barra de progreso con porcentaje
    
    Args:
        porcentaje: Valor de 0 a 100
        texto: Texto a mostrar
    """
    st.markdown(get_progress_html(porcentaje, texto), unsafe_allow_html=True)

def get_progress_html(porcentaje, texto="Procesando"):
    """
    Genera el HTML de la barra de progreso para poder renderizarlo desde placeholders.

    Args:
        porcentaje: Valor de 0 a 100
        texto: Texto a mostrar

    Returns:
        str: HTML como cadena
    """
    # Asegurar rango válido
    try:
        porcentaje_int = max(0, min(100, int(porcentaje)))
    except Exception:
        porcentaje_int = 0

    return f"""
    <div class="loading-container">
        <div class="loading-text">{texto}</div>
        <div style="width: 100%; background: #E3F2FD; border-radius: 10px; height: 30px; position: relative; margin-top: 1rem;">
            <div style="width: {porcentaje_int}%; background: linear-gradient(90deg, #4FC3F7, #81D4FA); height: 100%; border-radius: 10px; transition: width 0.3s ease;"></div>
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-weight: 600; color: #000;">
                {porcentaje_int}%
            </div>
        </div>
    </div>
    """
