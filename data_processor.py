"""
Módulo de procesamiento de datos
Contiene funciones para procesar archivos Excel y calcular sueldos
"""
import pandas as pd
import streamlit as st
import io
from datetime import datetime, timedelta
from calculations import calcular_horas_especiales, horas_a_horasminutos
from loading_components import get_progress_html

def detectar_y_resolver_marcaciones_duplicadas(df):
    """
    Detecta cuando un empleado marcó 3 veces en un mismo día y selecciona automáticamente 
    solo 2 marcas, eliminando duplicados que estén en el mismo rango de tiempo (10-20 minutos).
    
    Args:
        df (DataFrame): DataFrame con los datos originales
        
    Returns:
        DataFrame: DataFrame procesado con marcaciones duplicadas resueltas
    """
    df_procesado = df.copy()
    registros_procesados = []
    empleados_con_duplicados = []
    
    # Agrupar por empleado y fecha
    for (empleado, fecha), grupo in df_procesado.groupby(['Empleado', 'Fecha']):
        if len(grupo) == 3:
            # Empleado marcó 3 veces el mismo día
            empleados_con_duplicados.append(f"{empleado} - {fecha}")
            
            # Convertir las marcaciones a datetime para comparar
            marcaciones = []
            for idx, row in grupo.iterrows():
                try:
                    entrada = pd.to_datetime(str(row["Entrada"])).time()
                    salida = pd.to_datetime(str(row["Salida"])).time()
                    fecha_dt = pd.to_datetime(row["Fecha"])
                    
                    entrada_dt = datetime.combine(fecha_dt, entrada)
                    salida_dt = datetime.combine(fecha_dt, salida)
                    
                    marcaciones.append({
                        'index': idx,
                        'entrada': entrada_dt,
                        'salida': salida_dt,
                        'row': row
                    })
                except:
                    # Si hay error en conversión, mantener el registro
                    marcaciones.append({
                        'index': idx,
                        'entrada': None,
                        'salida': None,
                        'row': row
                    })
            
            # Encontrar duplicados basados en rangos de tiempo (10-20 minutos)
            duplicados_encontrados = []
            for i in range(len(marcaciones)):
                for j in range(i + 1, len(marcaciones)):
                    marc1 = marcaciones[i]
                    marc2 = marcaciones[j]
                    
                    if marc1['entrada'] and marc2['entrada']:
                        # Calcular diferencia en minutos para entrada
                        diff_entrada = abs((marc1['entrada'] - marc2['entrada']).total_seconds() / 60)
                        # Calcular diferencia en minutos para salida
                        diff_salida = abs((marc1['salida'] - marc2['salida']).total_seconds() / 60)
                        
                        # Si ambas diferencias están entre 10 y 20 minutos, son duplicados
                        if (10 <= diff_entrada <= 20) and (10 <= diff_salida <= 20):
                            duplicados_encontrados.append((i, j))
            
            # NUEVA LÓGICA SIMPLIFICADA: Crear marcación óptima combinando lo mejor de todas
            # Encontrar la entrada más temprana y la salida más tardía entre todas las marcaciones
            entrada_mas_temprana = min(marcaciones, key=lambda x: x['entrada'])
            salida_mas_tardia = max(marcaciones, key=lambda x: x['salida'])
            
            # Crear primera marcación con entrada más temprana y salida más tardía
            marcacion_principal = entrada_mas_temprana['row'].copy()
            marcacion_principal['Entrada'] = entrada_mas_temprana['entrada'].strftime("%H:%M")
            marcacion_principal['Salida'] = salida_mas_tardia['salida'].strftime("%H:%M")
            
            registros_procesados.append(marcacion_principal)
            
            # Buscar una segunda marcación que no sea duplicado de la principal
            segunda_marcacion = None
            for marc in marcaciones:
                # Verificar que no sea duplicado de la marcación principal
                diff_entrada = abs((marc['entrada'] - entrada_mas_temprana['entrada']).total_seconds() / 60)
                diff_salida = abs((marc['salida'] - salida_mas_tardia['salida']).total_seconds() / 60)
                
                # Si no es duplicado (diferencia > 20 minutos), usar como segunda marcación
                if diff_entrada > 20 or diff_salida > 20:
                    segunda_marcacion = marc['row']
                    break
            
            # Si encontramos una segunda marcación válida, agregarla
            if segunda_marcacion is not None:
                registros_procesados.append(segunda_marcacion)
            else:
                # Si no hay segunda marcación válida, usar la marcación del medio
                if len(marcaciones) >= 2:
                    # Ordenar por entrada y tomar la del medio
                    marcaciones_ordenadas = sorted(marcaciones, key=lambda x: x['entrada'])
                    registros_procesados.append(marcaciones_ordenadas[1]['row'])
                    
        else:
            # Empleado marcó 1 o 2 veces - mantener todos los registros
            for idx, row in grupo.iterrows():
                registros_procesados.append(row)
    
    # Mostrar información sobre empleados con duplicados procesados
    if empleados_con_duplicados:
        st.info(f"🔍 **Marcaciones duplicadas detectadas y resueltas automáticamente:**\n\n" + 
                "\n".join([f"• {emp}" for emp in empleados_con_duplicados]))
    
    # Crear nuevo DataFrame con los registros procesados
    df_resultado = pd.DataFrame(registros_procesados)
    
    return df_resultado

def validar_archivo_excel(df):
    """
    Valida que el archivo Excel contenga las columnas necesarias
    
    Args:
        df (DataFrame): DataFrame del archivo Excel
        
    Returns:
        tuple: (es_valido, columnas_faltantes)
    """
    required_cols = ["Empleado", "Fecha", "Entrada", "Salida", "Descuento Inventario", "Descuento Caja", "Retiro"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    return len(missing_cols) == 0, missing_cols

def procesar_datos_excel(df, valor_por_hora, opcion_feriados, fechas_feriados, cantidad_feriados):
    """
    Procesa los datos del Excel y calcula los sueldos
    
    Args:
        df (DataFrame): DataFrame con los datos
        valor_por_hora (float): Valor por hora de trabajo
        opcion_feriados (str): Tipo de configuración de feriados (no usado, solo fechas específicas)
        fechas_feriados (set): Fechas completas específicas de feriados
        cantidad_feriados (int): No usado, mantener por compatibilidad
        
    Returns:
        tuple: (resultados, total_horas, total_sueldos, total_horas_normales, total_horas_especiales)
    """
    # NUEVO: Primero resolver marcaciones duplicadas
    df_procesado = detectar_y_resolver_marcaciones_duplicadas(df)
    
    resultados = []
    total_horas = 0
    total_sueldos = 0
    total_horas_normales = 0  # NUEVO: Total de horas normales
    total_horas_especiales = 0  # NUEVO: Total de horas especiales

    for idx, row in df_procesado.iterrows():
        try:
            resultado_fila = _procesar_fila(row, idx, valor_por_hora, fechas_feriados)
            
            if resultado_fila:
                resultados.append(resultado_fila["datos"])
                total_horas += resultado_fila["horas"]
                total_sueldos += resultado_fila["sueldo"]
                
                # NUEVO: Acumular horas normales y especiales
                total_horas_normales += resultado_fila.get("horas_normales", 0)
                total_horas_especiales += resultado_fila.get("horas_especiales", 0)

        except Exception as e:
            st.error(f"Error en la fila {idx+2}: {e}")

    return resultados, total_horas, total_sueldos, total_horas_normales, total_horas_especiales

def _procesar_fila(row, idx, valor_por_hora, fechas_feriados):
    """
    Procesa una fila individual del Excel con lógica completa:
    - Validación de horario laboral (10:30 AM - 22:00 PM)
    - Horas normales × tarifa
    - Horas especiales (20:00-22:00) × tarifa × 1.3
    - Factor de feriado ×2 si aplica
    
    Args:
        row: Fila del DataFrame
        idx: Índice de la fila
        valor_por_hora: Valor por hora
        fechas_feriados: Fechas completas específicas de feriados
        
    Returns:
        dict: Resultado del procesamiento de la fila
    """
    fecha = pd.to_datetime(row["Fecha"])
    entrada = pd.to_datetime(str(row["Entrada"])).time()
    salida = pd.to_datetime(str(row["Salida"])).time()

    entrada_dt = datetime.combine(fecha, entrada)
    salida_dt = datetime.combine(fecha, salida)
    if salida_dt < entrada_dt:
        salida_dt += timedelta(days=1)

    # NUEVA VALIDACIÓN: Verificar horario laboral (10:30 AM - 22:00 PM)
    hora_inicio_laboral = datetime.combine(fecha, datetime.strptime("10:30", "%H:%M").time())
    hora_fin_laboral = datetime.combine(fecha, datetime.strptime("22:00", "%H:%M").time())
    
    # Validar que la entrada esté dentro del horario laboral
    if entrada_dt < hora_inicio_laboral or entrada_dt > hora_fin_laboral:
        # Si está fuera del horario, no se calcula - retornar registro con 0 horas
        return {
            "datos": {
                "Empleado": row["Empleado"],
                "Fecha": fecha.strftime("%Y-%m-%d"),
                "Entrada": entrada.strftime("%H:%M"),
                "Salida": salida.strftime("%H:%M"),
                "Feriado": "No",
                "Horas Trabajadas (h:mm)": "0:00",
                "Horas Normales": "0:00",
                "Horas Especiales": "0:00",
                "Descuento Inventario": 0,
                "Descuento Caja": 0,
                "Retiro": 0,
                "Sueldo Final": 0,
                "Observaciones": f"Fuera de horario laboral (10:30-22:00)"
            },
            "horas": 0,
            "sueldo": 0
        }
    
    # Validar que la salida también esté dentro del rango permitido
    if salida_dt > hora_fin_laboral + timedelta(days=1 if salida_dt.date() > entrada_dt.date() else 0):
        # Ajustar salida al máximo permitido
        salida_dt = hora_fin_laboral

    # Calcular horas trabajadas en decimal
    horas_trabajadas_decimal = (salida_dt - entrada_dt).total_seconds() / 3600

    # Calcular horas especiales (20:00-22:00 con 30% extra)
    horas_normales, horas_especiales = calcular_horas_especiales(entrada_dt, salida_dt)
    
    # Comparar la fecha completa (año-mes-día) con las fechas de feriados seleccionadas
    es_feriado = fecha.date() in fechas_feriados
    
    # Factor de feriado: 2x si es feriado, 1x si no lo es
    factor_feriado = 2 if es_feriado else 1

    # Cálculo con horas normales y especiales
    sueldo_normal = horas_normales * valor_por_hora
    sueldo_especial = horas_especiales * valor_por_hora * 1.3  # 30% extra para horas especiales
    sueldo_bruto = (sueldo_normal + sueldo_especial) * factor_feriado

    # Aplicar descuentos
    descuento_inventario = row["Descuento Inventario"] if not pd.isnull(row["Descuento Inventario"]) else 0
    descuento_caja = row["Descuento Caja"] if not pd.isnull(row["Descuento Caja"]) else 0
    retiro = row["Retiro"] if not pd.isnull(row["Retiro"]) else 0

    sueldo_final = sueldo_bruto - descuento_inventario - descuento_caja - retiro

    datos_fila = {
        "Empleado": row["Empleado"],
        "Fecha": fecha.strftime("%Y-%m-%d"),
        "Entrada": entrada.strftime("%H:%M"),
        "Salida": salida.strftime("%H:%M"),
        "Feriado": "Sí" if es_feriado else "No",
        "Horas Trabajadas (h:mm)": horas_a_horasminutos(horas_trabajadas_decimal),
        "Horas Normales": horas_a_horasminutos(horas_normales),
        "Horas Especiales": horas_a_horasminutos(horas_especiales),
        "Descuento Inventario": descuento_inventario,
        "Descuento Caja": descuento_caja,
        "Retiro": retiro,
        "Sueldo Final": round(sueldo_final, 2)
    }

    return {
        "datos": datos_fila,
        "horas": horas_trabajadas_decimal,
        "sueldo": sueldo_final,
        "horas_normales": horas_normales,  # NUEVO: Para los totales
        "horas_especiales": horas_especiales  # NUEVO: Para los totales
    }

def mostrar_resultados(resultados, total_horas, total_sueldos, total_horas_normales=0, total_horas_especiales=0, valor_por_hora=None, fechas_feriados=None, nombre_archivo=None):
    """
    Muestra los resultados en la interfaz y proporciona descarga
    
    Args:
        resultados (list): Lista de resultados procesados
        total_horas (float): Total de horas trabajadas
        total_sueldos (float): Total de sueldos calculados
        total_horas_normales (float): Total de horas normales trabajadas
        total_horas_especiales (float): Total de horas especiales trabajadas
        valor_por_hora (float): Valor por hora utilizado en cálculos
        fechas_feriados (set): Fechas marcadas como feriados
        nombre_archivo (str): Nombre base para el archivo Excel (opcional)
    """
    df_result = pd.DataFrame(resultados)
    
    # Mensaje de éxito con estilo
    st.markdown("""
    <div class="custom-alert alert-success">
        <h3> Cálculo completado exitosamente</h3>
        <p>Los sueldos han sido procesados correctamente. Revisa los resultados a continuación.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Mostrar tabla con estilo
    st.markdown("### Resultados del Cálculo")
    st.dataframe(df_result, use_container_width=True)

    # Resumen visual final con métricas mejoradas
    st.markdown("### 📈 Resumen General")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Registros</div>
            <div class="metric-value">{len(df_result)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Horas Normales</div>
            <div class="metric-value">{horas_a_horasminutos(total_horas_normales)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Horas Especiales</div>
            <div class="metric-value">{horas_a_horasminutos(total_horas_especiales)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Horas</div>
            <div class="metric-value">{horas_a_horasminutos(total_horas)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Sueldos</div>
            <div class="metric-value">${round(total_sueldos, 2):,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    # Descargar Excel final
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_result.to_excel(writer, index=False)
    
    # Generar nombre del archivo dinámico
    if nombre_archivo:
        # Limpiar nombre del archivo (remover extensión .pdf si existe)
        nombre_base = nombre_archivo.replace('.pdf', '').replace('.PDF', '')
        nombre_excel = f"{nombre_base}_calculado.xlsx"
    else:
        nombre_excel = "sueldos_calculados.xlsx"
    
    st.download_button(
        " Descargar Reporte Final en Excel",
        data=output.getvalue(),
        file_name=nombre_excel,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    # Botón de consulta para calculadora de horas
    st.markdown("---")
    st.markdown("### 🧮 Verificación de Cálculos")
    st.markdown("""
    <div style="text-align: center; margin: 1rem 0;">
        <p>¿Necesitas verificar los cálculos de horas? Usa nuestra calculadora externa:</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div style="text-align: center;">
                <a href="https://calculadorasonline.com/calculadora-de-horas-minutos-y-segundos-sumar-horas-restar-horas/" target="_blank">
                    <button style="
                        background: linear-gradient(90deg, #4FC3F7, #81D4FA);
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 12px 24px;
                        font-size: 16px;
                        font-weight: 600;
                        cursor: pointer;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                        transition: all 0.3s ease;
                        text-decoration: none;
                        display: inline-block;
                        width: 100%;
                    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 12px rgba(0,0,0,0.15)'" 
                       onmouseout="this.style.transform='translateY(0px)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.1)'">
                        🧮 CONSULTA - Calculadora de Horas
                    </button>
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
