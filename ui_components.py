"""
Módulo de componentes de interfaz de usuario
Contiene funciones para crear elementos de la UI
"""
import streamlit as st
import calendar
from datetime import datetime

def _safe_session_state_update(key, value):
    """
    Actualiza el session_state de forma segura para evitar conflictos del DOM
    """
    if key not in st.session_state or st.session_state[key] != value:
        st.session_state[key] = value

def mostrar_input_valor_hora():
    """
    Muestra el input para el valor por hora con estilo mejorado
    
    Returns:
        float: Valor por hora ingresado
    """
    st.markdown("### 💲 Valor por Hora")
    return st.number_input(
        "Ingrese el valor por hora:", 
        min_value=0.0, 
        value=13937.0,
        step=100.0,
        format="%.0f",
        help="Este valor se aplicará a todas las horas trabajadas por los empleados"
    )

def mostrar_descarga_plantilla():
    """
    Muestra el botón de descarga de la plantilla Excel con estilo personalizado
    """
    st.markdown("""
    <div class="custom-alert alert-info">
        <strong> Descarga la plantilla de Excel</strong><br>
        Completa la plantilla con los datos de tus empleados y súbela para calcular automáticamente los sueldos.
    </div>
    """, unsafe_allow_html=True)
    
    # Obtener la ruta del archivo de plantilla
    import os
    plantilla_path = os.path.join(os.path.dirname(__file__), "plantilla_sueldos_feriados_dias.xlsx")
    
    # Verificar si el archivo existe
    if os.path.exists(plantilla_path):
        with open(plantilla_path, "rb") as f:
            st.download_button(
                "Descargar Plantilla Excel", 
                f, 
                file_name="plantilla_sueldo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Descarga la plantilla oficial para cargar datos de empleados"
            )
    else:
        st.warning("⚠️ Archivo de plantilla no encontrado. Usa el formato estándar de Excel con las columnas: Empleado, Fecha, Entrada, Salida, Descuento Inventario, Descuento Caja, Retiro")

def configurar_feriados():
    """
    Muestra la configuración de feriados de forma simple
    
    Returns:
        tuple: (opcion_feriados, fechas_feriados, cantidad_feriados)
    """
    st.markdown("""
    <div class="custom-alert alert-info">
        <strong>📅 Selecciona hasta 3 fechas de feriados</strong><br>
        Los días feriados reciben doble pago automáticamente.
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar session state para feriados si no existe
    if 'feriados_list' not in st.session_state:
        st.session_state.feriados_list = []
    
    # Mostrar selector de fecha simple
    st.markdown("### Agregar Fecha de Feriado")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        fecha_seleccionada = st.date_input(
            "Selecciona una fecha:",
            value=datetime.now(),
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2030, 12, 31),
            help="Haz clic para abrir el calendario y seleccionar una fecha",
            key="date_picker_feriado"
        )
    
    with col2:
        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
        if st.button("➕ Agregar", use_container_width=True):
            if len(st.session_state.feriados_list) >= 3:
                st.error("Máximo 3 fechas de feriados permitidas")
            elif fecha_seleccionada in st.session_state.feriados_list:
                st.warning(" Esta fecha ya está agregada")
            else:
                st.session_state.feriados_list.append(fecha_seleccionada)
                st.success(f" Feriado agregado: {fecha_seleccionada.strftime('%d/%m/%Y')}")
    
    # Mostrar feriados seleccionados con opción de eliminar
    if st.session_state.feriados_list:
        st.markdown("###  Feriados Seleccionados:")
        
        for idx, fecha in enumerate(sorted(st.session_state.feriados_list)):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""
                <div class="custom-alert alert-success" style="margin: 0.2rem 0; padding: 0.8rem;">
                    <strong> {fecha.strftime('%d/%m/%Y - %A')}</strong>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("🗑️", key=f"delete_{idx}", help="Eliminar este feriado"):
                    st.session_state.feriados_list.remove(fecha)
                    st.rerun()
        
        # Botón para limpiar todos
        if st.button(" Limpiar Todos", help="Eliminar todas las fechas de feriados"):
            st.session_state.feriados_list = []
            st.rerun()
    
    # Convertir lista a set para compatibilidad con el resto del código
    fechas_feriados = set(st.session_state.feriados_list)
    opcion_feriados = " Seleccionar fechas específicas"
    cantidad_feriados = len(fechas_feriados)
    
    return opcion_feriados, fechas_feriados, cantidad_feriados

def mostrar_subida_archivo():
    """
    Muestra el widget de subida de archivo Excel o PDF con estilo mejorado
    
    Returns:
        tuple: (archivo_subido, tipo_archivo) o (lista_archivos, tipo_archivo) para PDFs
    """
    st.markdown("###  Selecciona el tipo de archivo")
    
    # Selector de tipo de archivo con botones mejorados
    col1, col2 = st.columns(2)
    
    with col1:
        excel_selected = st.button("Archivo Excel", use_container_width=True, help="Datos estructurados tradicionales")
    
    with col2:
        pdf_selected = st.button(" Archivos PDF (Hasta 2)", use_container_width=True, help="Procesamiento inteligente automático - Períodos quincenales")
    
    # Mantener selección en session state
    if excel_selected:
        st.session_state.file_type = "excel"
    elif pdf_selected:
        st.session_state.file_type = "pdf"
    
    # Valor por defecto
    if "file_type" not in st.session_state:
        st.session_state.file_type = "excel"
    
    tipo_archivo = st.session_state.file_type
    
    if tipo_archivo == "excel":
        st.markdown("""
        <div class="custom-alert alert-info">
            <strong>Modo Excel Tradicional</strong><br>
            Sube tu archivo Excel completado con todos los datos de empleados.
        </div>
        """, unsafe_allow_html=True)
        
        archivo = st.file_uploader(
            "Sube tu archivo Excel completado:",
            type=["xlsx"],
            help="Archivo Excel con columnas: Empleado, Fecha, Entrada, Salida, Descuento Inventario, Descuento Caja, Retiro",
            key="excel_uploader"
        )
        return archivo, "excel"
    
    else:  # PDF
        st.markdown("""
        <div class="custom-alert alert-warning">
            <strong> Modo Inteligente PDF Activado - Períodos Quincenales</strong><br>
            Sube hasta 2 PDFs (uno por cada quincena). El sistema los ordenará automáticamente por fecha.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="custom-alert alert-info">
            <strong>💡</strong> Añade por orden los PDFs (primera a segunda quincena). 
        </div>
        """, unsafe_allow_html=True)
        
        # Subida de archivos múltiples
        archivos = st.file_uploader(
            "Sube tus archivos PDF (máximo 2 quincenas):",
            type=["pdf"],
            accept_multiple_files=True,
            help="PDFs con información de empleados y horarios. Ejemplo: 1-15 octubre y 16-31 octubre",
            key="pdf_uploader"
        )
        
        # Validar que no se suban más de 2 archivos
        if archivos and len(archivos) > 2:
            st.error(" Máximo 2 archivos PDF permitidos (uno por cada quincena)")
            return None, "pdf"
        
        # Mostrar información de archivos subidos de forma compacta
        if archivos:
            # Crear lista compacta de archivos
            nombres_archivos = [f"PDF {idx}: {archivo.name}" for idx, archivo in enumerate(archivos, 1)]
            archivos_texto = " | ".join(nombres_archivos)
            
            st.markdown(f"""
            <div style="
                background-color: #d4edda; 
                border: 1px solid #c3e6cb; 
                border-radius: 6px; 
                padding: 8px 12px; 
                margin: 8px 0;
                font-size: 14px;
                color: #155724;
                display: flex;
                align-items: center;
                flex-wrap: wrap;
                gap: 8px;
            ">
                <span style="font-weight: 600;">📁 Cargados:</span>
                <span style="word-break: break-all;">{archivos_texto}</span>
            </div>
            """, unsafe_allow_html=True)
        
        return archivos, "pdf"


def mostrar_editor_registros_incompletos(df_incompletos):
    """
    Muestra una interfaz simplificada y estable para completar registros incompletos.
    Evita conflictos del DOM usando una estructura más simple.
    
    Args:
        df_incompletos: DataFrame con registros incompletos
        
    Returns:
        bool: True si se aplicaron correcciones, False si aún están pendientes
    """
    import pandas as pd
    from datetime import datetime, timedelta
    
    # Forzar limpieza de caché para evitar problemas de duplicación
    st.cache_data.clear()
    
    if df_incompletos.empty:
        return True
    
    st.markdown("""
    <div class="custom-alert alert-warning">
        <strong>🔍 Registros Incompletos Detectados</strong><br>
        Empleados que marcaron solo <strong>UNA VEZ</strong> en el día. Usa los controles desplegables para completar.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 👨‍💼 Panel de Corrección Administrativa")
    
    # Inicializar session_state de forma más limpia
    if 'correcciones_horarios' not in st.session_state:
        st.session_state.correcciones_horarios = {}
    
    # Inicializar contador de cambios para evitar problemas DOM
    if 'cambios_contador' not in st.session_state:
        st.session_state.cambios_contador = {}
    
    registros_completos = 0
    
    # Procesar cada registro de forma más simple
    for idx, row in df_incompletos.iterrows():
        horario_registrado = row.get('Horario_Registrado', 'No disponible')
        tipo_problema = row.get('Tipo_Problema', 'Problema no identificado')
        
        with st.expander(
            f"👤 {row['Empleado']} - 📅 {row['Fecha']} - ⏰ {horario_registrado}", 
            expanded=True
        ):
            # Información del problema (sin sugerencias automáticas)
            st.markdown(f"""
            <div class="custom-alert alert-info">
                <strong>📊 Situación:</strong> {tipo_problema}<br>
                <strong>⏰ Horario registrado:</strong> {horario_registrado}<br>
                <strong>👨‍� Decisión:</strong> El administrador decide si fue entrada o salida
            </div>
            """, unsafe_allow_html=True)
            
            # Evitar recreación excesiva de elementos del DOM
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**1️⃣ ¿Qué tipo de marca fue?**")
                
                # Clave única para evitar conflictos
                select_key = f"tipo_select_{idx}_{row['Empleado'].replace(' ', '_')}"
                
                tipo_decision = st.selectbox(
                    f"El horario {horario_registrado} fue:",
                    options=['Entrada', 'Salida'],
                    key=select_key,
                    help="Decide si el empleado estaba llegando (Entrada) o saliendo (Salida)"
                )
            
            with col2:
                st.markdown("**2️⃣ Completar horario faltante**")
                
                # Usar un contenedor estático para mostrar el estado
                estado_placeholder = st.empty()
                
                # Determinar qué mostrar basado en la selección actual
                if tipo_decision == 'Entrada':
                    estado_content = f"""
                    <div style='margin-bottom: 10px;'>
                        <div style='background-color: #d1ecf1; padding: 8px; border-radius: 4px; margin-bottom: 5px;'>
                            ✅ <strong>Entrada:</strong> {horario_registrado}
                        </div>
                        <div style='background-color: #f8d7da; padding: 8px; border-radius: 4px;'>
                            ❌ <strong>Salida:</strong> Faltante
                        </div>
                    </div>
                    """
                else:  # tipo_decision == 'Salida'
                    estado_content = f"""
                    <div style='margin-bottom: 10px;'>
                        <div style='background-color: #f8d7da; padding: 8px; border-radius: 4px; margin-bottom: 5px;'>
                            ❌ <strong>Entrada:</strong> Faltante
                        </div>
                        <div style='background-color: #d1ecf1; padding: 8px; border-radius: 4px;'>
                            ✅ <strong>Salida:</strong> {horario_registrado}
                        </div>
                    </div>
                    """
                
                # Mostrar el estado usando HTML estático
                estado_placeholder.markdown(estado_content, unsafe_allow_html=True)
            
            # Formulario para la entrada de datos y confirmación (sin sugerencias automáticas)
            with st.form(key=f"form_registro_{idx}"):
                if tipo_decision == 'Entrada':
                    # Necesita completar la salida - administrador decide completamente
                    salida_corregida = st.time_input(
                        "Ingresa la hora de salida:",
                        value=datetime.strptime("17:00", "%H:%M").time(),
                        key=f"time_salida_{idx}",
                        help="Hora en que el empleado salió"
                    )
                    entrada_final = horario_registrado
                    salida_final = salida_corregida.strftime("%H:%M")
                    
                else:  # tipo_decision == 'Salida'
                    # Necesita completar la entrada - administrador decide completamente
                    entrada_corregida = st.time_input(
                        "Ingresa la hora de entrada:",
                        value=datetime.strptime("08:00", "%H:%M").time(),
                        key=f"time_entrada_{idx}",
                        help="Hora en que el empleado ingresó"
                    )
                    entrada_final = entrada_corregida.strftime("%H:%M")
                    salida_final = horario_registrado
                
                # Botón para confirmar este registro
                if st.form_submit_button(f"✅ Confirmar Registro {idx+1}", use_container_width=True):
                    # Guardar las correcciones
                    st.session_state.correcciones_horarios[f"{idx}_entrada"] = entrada_final
                    st.session_state.correcciones_horarios[f"{idx}_salida"] = salida_final
                    st.session_state.correcciones_horarios[f"{idx}_confirmado"] = True
                    
                    # Mostrar confirmación
                    horas_estimadas = _calcular_horas_trabajadas(entrada_final, salida_final)
                    st.success(f"✅ Registro confirmado: {entrada_final} → {salida_final} ({horas_estimadas})")
                    st.rerun()
            
            # Mostrar estado actual si ya está confirmado
            if st.session_state.correcciones_horarios.get(f"{idx}_confirmado", False):
                entrada_conf = st.session_state.correcciones_horarios.get(f"{idx}_entrada")
                salida_conf = st.session_state.correcciones_horarios.get(f"{idx}_salida")
                
                if entrada_conf and salida_conf:
                    horas_estimadas = _calcular_horas_trabajadas(entrada_conf, salida_conf)
                    st.markdown(f"""
                    <div class="custom-alert alert-success">
                        <strong>✅ Registro Confirmado:</strong><br>
                        📥 Entrada: {entrada_conf} | 📤 Salida: {salida_conf}<br>
                        ⏱️ <strong>Horas: {horas_estimadas}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                    registros_completos += 1
    
    # Verificar progreso
    st.markdown("---")
    st.markdown(f"### 📊 Progreso: {registros_completos}/{len(df_incompletos)} registros completados")
    
    # Botón final para continuar
    if registros_completos == len(df_incompletos):
        if st.button("🚀 Continuar con el Cálculo", type="primary", use_container_width=True):
            return True
    else:
        st.warning(f"⚠️ Confirma {len(df_incompletos) - registros_completos} registro(s) restante(s)")
    
    return False


# Funciones de sugerencias automáticas eliminadas - administrador tiene control total


def _calcular_horas_trabajadas(entrada_str: str, salida_str: str) -> str:
    """Calcula las horas trabajadas entre entrada y salida"""
    try:
        from datetime import datetime, timedelta
        entrada = datetime.strptime(entrada_str.strip(), "%H:%M")
        salida = datetime.strptime(salida_str.strip(), "%H:%M")
        
        # Si la salida es menor que la entrada, asumimos que cruzó medianoche
        if salida < entrada:
            salida += timedelta(days=1)
        
        diferencia = salida - entrada
        horas = diferencia.total_seconds() / 3600
        
        horas_enteras = int(horas)
        minutos = int((horas - horas_enteras) * 60)
        
        return f"{horas_enteras}h {minutos}m"
    except:
        return "Error en cálculo"


def mostrar_editor_horarios_ambiguos(df_ambiguos):
    """
    Muestra una interfaz para revisar horarios que podrían estar mal asignados
    (por ejemplo, entrada muy tarde o salida muy temprano)
    
    Args:
        df_ambiguos: DataFrame con registros ambiguos
        
    Returns:
        tuple: (correcciones_aplicadas, df_corregido)
    """
    import pandas as pd
    from datetime import datetime
    
    if df_ambiguos.empty:
        return False, df_ambiguos
    
    st.markdown("""
    <div class="custom-alert alert-info">
        <strong>🤔 Horarios Sospechosos Detectados</strong><br>
        Se detectaron horarios que podrían estar <strong>mal asignados</strong>. 
        Revisa si la entrada y salida están correctamente asignadas.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔍 Revisión de Horarios Ambiguos")
    
    # Inicializar session_state para correcciones de ambiguos
    if 'correcciones_ambiguos' not in st.session_state:
        st.session_state.correcciones_ambiguos = {}
    
    correcciones_realizadas = False
    
    for idx, row in df_ambiguos.iterrows():
        with st.expander(
            f"⚠️ {row['Empleado']} - 📅 {row['Fecha']} - {row['Razon_Sospecha'][:50]}...", 
            expanded=True
        ):
            st.markdown(f"""
            <div class="custom-alert alert-warning">
                <strong>🚨 Problema detectado:</strong><br>
                {row['Razon_Sospecha']}
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                st.markdown("**📊 Horarios Actuales:**")
                st.info(f"🔘 Entrada: {row['Entrada_Original']}")
                st.info(f"🔘 Salida: {row['Salida_Original']}")
            
            with col2:
                st.markdown("**🔄 ¿Intercambiar horarios?**")
                
                intercambiar_key = f"intercambiar_{idx}"
                intercambiar = st.checkbox(
                    "Sí, intercambiar entrada ↔ salida",
                    key=intercambiar_key,
                    help="Marca esto si crees que los horarios están invertidos"
                )
                
                if intercambiar:
                    st.success(f"✅ Nuevo orden:")
                    st.success(f"📥 Entrada: {row['Salida_Original']}")
                    st.success(f"📤 Salida: {row['Entrada_Original']}")
                    
                    # Guardar la corrección
                    st.session_state.correcciones_ambiguos[idx] = {
                        'nueva_entrada': row['Salida_Original'],
                        'nueva_salida': row['Entrada_Original']
                    }
                    correcciones_realizadas = True
                else:
                    # Mantener original
                    if idx in st.session_state.correcciones_ambiguos:
                        del st.session_state.correcciones_ambiguos[idx]
            
            with col3:
                st.markdown("**⏱️ Horas resultantes:**")
                if intercambiar:
                    horas_nuevas = _calcular_horas_trabajadas(row['Salida_Original'], row['Entrada_Original'])
                    st.metric("Nuevas horas", horas_nuevas)
                else:
                    horas_actuales = _calcular_horas_trabajadas(row['Entrada_Original'], row['Salida_Original'])
                    st.metric("Horas actuales", horas_actuales)
    
    # Botón para aplicar correcciones de ambiguos
    if correcciones_realizadas:
        st.markdown("---")
        if st.button("🔄 Aplicar Intercambios de Horarios", type="secondary", use_container_width=True):
            return True, df_ambiguos
    
    return False, df_ambiguos


def aplicar_correcciones_ambiguos_a_dataframe(df_original, df_ambiguos):
    """
    Aplica las correcciones de horarios ambiguos al DataFrame original
    
    Args:
        df_original: DataFrame original
        df_ambiguos: DataFrame con registros ambiguos
        
    Returns:
        DataFrame: DataFrame con intercambios aplicados
    """
    import pandas as pd
    
    df_corregido = df_original.copy()
    
    if 'correcciones_ambiguos' not in st.session_state:
        return df_corregido
    
    intercambios_aplicados = 0
    
    for idx, correcciones in st.session_state.correcciones_ambiguos.items():
        df_corregido.at[idx, 'Entrada'] = correcciones['nueva_entrada']
        df_corregido.at[idx, 'Salida'] = correcciones['nueva_salida']
        intercambios_aplicados += 1
    
    if intercambios_aplicados > 0:
        st.markdown(f"""
        <div class="custom-alert alert-success">
            <strong>🔄 Intercambios Aplicados</strong><br>
            Se intercambiaron los horarios en {intercambios_aplicados} registro(s).
        </div>
        """, unsafe_allow_html=True)
        
        # Limpiar session state
        if 'correcciones_ambiguos' in st.session_state:
            del st.session_state.correcciones_ambiguos
    
    return df_corregido


def aplicar_correcciones_a_dataframe(df_original, df_incompletos):
    """
    Aplica las correcciones manuales al DataFrame original, incluyendo decisiones administrativas
    
    Args:
        df_original: DataFrame original con todos los datos
        df_incompletos: DataFrame con registros incompletos
        
    Returns:
        DataFrame: DataFrame corregido con horarios completos
    """
    import pandas as pd
    
    df_corregido = df_original.copy()
    
    if 'correcciones_horarios' not in st.session_state:
        return df_corregido
    
    # Aplicar correcciones basadas en decisiones administrativas
    correcciones_aplicadas = 0
    
    for idx in df_incompletos.index:
        entrada_corregida = False
        salida_corregida = False
        
        # Aplicar entrada corregida
        if f"{idx}_entrada" in st.session_state.correcciones_horarios:
            df_corregido.at[idx, 'Entrada'] = st.session_state.correcciones_horarios[f"{idx}_entrada"]
            entrada_corregida = True
        
        # Aplicar salida corregida
        if f"{idx}_salida" in st.session_state.correcciones_horarios:
            df_corregido.at[idx, 'Salida'] = st.session_state.correcciones_horarios[f"{idx}_salida"]
            salida_corregida = True
        
        if entrada_corregida or salida_corregida:
            correcciones_aplicadas += 1
    
    # Mostrar resumen de correcciones aplicadas
    if correcciones_aplicadas > 0:
        st.markdown(f"""
        <div class="custom-alert alert-success">
            <strong>✅ Correcciones Aplicadas Exitosamente</strong><br>
            Se corrigieron {correcciones_aplicadas} registro(s) con decisiones administrativas.<br>
            Los horarios faltantes han sido completados según tus especificaciones.
        </div>
        """, unsafe_allow_html=True)
    
    return df_corregido
