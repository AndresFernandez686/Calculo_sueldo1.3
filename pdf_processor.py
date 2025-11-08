"""
Módulo para procesamiento inteligente de PDFs
Convierte PDFs con formatos diversos a estructura estándar para cálculo de sueldos
"""
import pandas as pd
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import streamlit as st

def procesar_pdf_a_dataframe(archivo_pdf) -> pd.DataFrame:
    """
    Procesa un archivo PDF y extrae datos de empleados y horarios
    
    Args:
        archivo_pdf: Archivo PDF subido
        
    Returns:
        DataFrame: Datos procesados en formato estándar
    """
    try:
        # Aquí necesitaremos una librería como PyPDF2 o pdfplumber
        # Por ahora simulo la extracción
        texto_pdf = extraer_texto_pdf(archivo_pdf)
        lineas = texto_pdf.split('\n')
        
        # Identificar estructura del PDF
        estructura = analizar_estructura_pdf(lineas)
        
        # Extraer datos según la estructura identificada
        datos_brutos = extraer_datos_segun_estructura(lineas, estructura)
        
        # Procesar datos inteligentemente
        datos_procesados = procesar_datos_inteligente(datos_brutos)
        
        # Convertir a DataFrame estándar
        df_final = convertir_a_dataframe_estandar(datos_procesados)
        
        return df_final
        
    except Exception as e:
        st.error(f" Error procesando PDF: {str(e)}")
        return pd.DataFrame()

def extraer_texto_pdf(archivo_pdf) -> str:
    """
    Extrae texto del PDF usando pdfplumber
    """
    try:
        # Importar pdfplumber dinámicamente
        import pdfplumber
        
        texto_completo = ""
        
        with pdfplumber.open(archivo_pdf) as pdf:
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto_completo += texto_pagina + "\n"
        
        return texto_completo
        
    except ImportError:
        st.warning(" pdfplumber no está instalado. Usando datos de ejemplo.")
        # Fallback con datos de ejemplo
        return """
        REPORTE DE ASISTENCIA - OCTUBRE 2024
        
        Empleado: Juan Pérez
        01/10/2024 08:00 - Entrada
        01/10/2024 17:00 - Salida
        02/10/2024 08:30 - Entrada
        02/10/2024 17:30 - Salida
        
        Empleado: María González  
        01/10/2024 09:00 - Entrada
        01/10/2024 18:00 - Salida
        02/10/2024 08:45 - Entrada
        02/10/2024 17:45 - Salida
        
        Empleado: Carlos López
        01/10/2024 08:15 - Entrada
        01/10/2024 17:15 - Salida
        """
        
    except Exception as e:
        st.error(f" Error extrayendo texto del PDF: {str(e)}")
        return ""

def analizar_estructura_pdf(lineas: List[str]) -> Dict:
    """
    Analiza la estructura del PDF para identificar patrones
    
    Args:
        lineas: Lista de líneas del texto extraído
        
    Returns:
        Dict: Información sobre la estructura identificada
    """
    estructura = {
        "tipo": "desconocido",
        "patron_empleado": None,
        "patron_fecha_hora": None,
        "columnas_detectadas": [],
        "separador": None
    }
    
    # Detectar patrones comunes
    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue
            
        # Patrón: Empleado: Nombre
        if re.match(r'Empleado:', linea, re.IGNORECASE):
            estructura["patron_empleado"] = "empleado_prefijo"
            
        # Patrón: Fecha y hora juntas (YYYY-MM-DD HH:MM:SS)
        if re.search(r'\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}:\d{2}', linea):
            estructura["patron_fecha_hora"] = "fecha_hora_completa"
            
        # Patrón: Fecha y hora juntas (YYYY-MM-DD HH:MM)
        if re.search(r'\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}', linea):
            estructura["patron_fecha_hora"] = "fecha_hora_separada"
            
        # Patrón: Fecha y hora juntas (DD/MM/YYYY HH:MM)
        if re.search(r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}', linea):
            estructura["patron_fecha_hora"] = "fecha_hora_barras"
            
        # Detectar si hay columnas tabulares
        if '\t' in linea or '|' in linea or '  ' in linea:
            estructura["tipo"] = "tabular"
            
    return estructura

def extraer_datos_segun_estructura(lineas: List[str], estructura: Dict) -> List[Dict]:
    """
    Extrae datos según la estructura identificada usando el parser inteligente
    """
    from smart_parser import SmartTimeParser, EntradaSalidaDetector
    
    parser = SmartTimeParser()
    detector = EntradaSalidaDetector()
    
    datos = []
    empleado_actual = None
    
    # Buscar nombres en todo el documento primero
    posibles_nombres = _buscar_nombres_en_documento(lineas)
    
    for i, linea in enumerate(lineas):
        linea = linea.strip()
        if not linea:
            continue
            
        # Detectar nombre de empleado (varios patrones)
        if re.match(r'Empleado:', linea, re.IGNORECASE):
            empleado_actual = linea.split(':', 1)[1].strip()
            continue
        elif re.match(r'Nombre:', linea, re.IGNORECASE):
            empleado_actual = linea.split(':', 1)[1].strip()
            continue
        elif re.match(r'^[A-ZÁÉÍÓÚ][a-záéíóú]+ [A-ZÁÉÍÓÚ][a-záéíóú]+.*$', linea):
            # Patrón de nombre completo (Nombre Apellido)
            if not any(char.isdigit() for char in linea) and len(linea.split()) >= 2:
                empleado_actual = linea.strip()
                continue
        elif re.match(r'^[A-ZÁÉÍÓÚ][a-záéíóúñ]+$', linea):
            # Patrón de nombre simple (solo una palabra, como "Paz")
            if len(linea.strip()) >= 2 and linea.strip().isalpha():
                empleado_actual = linea.strip()
                continue
        elif re.match(r'^[A-ZÁÉÍÓÚ][a-záéíóúñ]+\s*$', linea.strip()):
            # Patrón de nombre con posibles espacios al final
            nombre_limpio = linea.strip()
            if len(nombre_limpio) >= 2 and nombre_limpio.isalpha():
                empleado_actual = nombre_limpio
                continue
        
        # Extraer fechas y horas de la línea
        fechas_horas = parser.extraer_fecha_hora(linea)
        
        for fh in fechas_horas:
            # Si no hay empleado actual, usar el primer nombre encontrado o "Empleado 1"
            if not empleado_actual and posibles_nombres:
                nombre_empleado = posibles_nombres[0]
            else:
                nombre_empleado = empleado_actual if empleado_actual else "Empleado 1"
            
            # Detectar tipo (entrada/salida)
            contexto = lineas[max(0, i-2):i+3] if i > 0 else [linea]
            tipo = detector.detectar_tipo(linea, fh['hora'], contexto)
            
            datos.append({
                "empleado": nombre_empleado,
                "fecha": fh['fecha'],
                "hora": fh['hora'],
                "tipo": tipo,
                "linea_original": linea,
                "confianza": _calcular_confianza(linea, fh)
            })
    
    return datos

def _buscar_nombres_en_documento(lineas: List[str]) -> List[str]:
    """
    Busca posibles nombres de empleados en todo el documento
    """
    nombres_encontrados = []
    
    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue
            
        # Buscar patrones de nombres
        # Nombre con "Nombre:" o "Empleado:"
        if re.match(r'(Nombre|Empleado):', linea, re.IGNORECASE):
            nombre = linea.split(':', 1)[1].strip()
            if nombre and nombre not in nombres_encontrados:
                nombres_encontrados.append(nombre)
        
        # Nombre simple (una palabra alfabética, primera letra mayúscula)
        elif re.match(r'^[A-ZÁÉÍÓÚ][a-záéíóúñ]+$', linea):
            if len(linea) >= 2 and linea not in nombres_encontrados:
                # Evitar palabras que claramente no son nombres
                palabras_excluir = ['Hora', 'Fecha', 'Entrada', 'Salida', 'Total', 'Reporte', 'Asistencia']
                if linea not in palabras_excluir:
                    nombres_encontrados.append(linea)
        
        # Nombre completo (dos o más palabras)
        elif re.match(r'^[A-ZÁÉÍÓÚ][a-záéíóú]+ [A-ZÁÉÍÓÚ][a-záéíóú]+.*$', linea):
            if not any(char.isdigit() for char in linea) and linea not in nombres_encontrados:
                nombres_encontrados.append(linea)
    
    return nombres_encontrados

def validar_datos_pdf(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Valida que el DataFrame extraído del PDF tenga los datos necesarios
    
    Args:
        df: DataFrame extraído del PDF
        
    Returns:
        Tuple[bool, List[str]]: (es_valido, lista_errores)
    """
    errores = []
    
    # Verificar que tenga filas
    if len(df) == 0:
        errores.append("No se encontraron registros de asistencia")
        return False, errores
    
    # Verificar columnas necesarias
    columnas_requeridas = ['Empleado', 'Fecha', 'Entrada', 'Salida']
    columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
    
    if columnas_faltantes:
        errores.append(f"Faltan columnas: {', '.join(columnas_faltantes)}")
    
    # Verificar que hay datos válidos
    if 'Fecha' in df.columns and df['Fecha'].isna().all():
        errores.append("No se encontraron fechas válidas")
    
    if 'Empleado' in df.columns and df['Empleado'].isna().all():
        errores.append("No se encontraron nombres de empleados")
    
    return len(errores) == 0, errores

def _calcular_confianza(linea: str, fecha_hora: Dict) -> float:
    """Calcula la confianza de la extracción"""
    confianza = 0.5  # Base
    
    # Mayor confianza si hay palabras clave
    if any(palabra in linea.lower() for palabra in ['entrada', 'salida', 'entry', 'exit']):
        confianza += 0.3
    
    # Mayor confianza si el formato de fecha es estándar
    if re.match(r'\d{4}-\d{2}-\d{2}', fecha_hora['fecha']):
        confianza += 0.2
    
    return min(confianza, 1.0)

def procesar_datos_inteligente(datos_brutos: List[Dict]) -> List[Dict]:
    """
    Procesa los datos de manera inteligente usando el DataGrouper
    """
    from smart_parser import DataGrouper
    
    if not datos_brutos:
        return []
    
    # Filtrar datos por confianza
    datos_confiables = [d for d in datos_brutos if d.get('confianza', 0) > 0.6]
    
    if not datos_confiables:
        st.warning(" Datos extraídos tienen baja confianza. Usando todos los datos disponibles.")
        datos_confiables = datos_brutos
    
    # Usar DataGrouper para agrupar inteligentemente
    grouper = DataGrouper()
    datos_agrupados = grouper.agrupar_por_empleado_fecha(datos_confiables)
    
    return datos_agrupados

def convertir_a_dataframe_estandar(datos_procesados: List[Dict]) -> pd.DataFrame:
    """
    Convierte los datos procesados al formato estándar del sistema
    
    Args:
        datos_procesados: Datos procesados
        
    Returns:
        DataFrame: DataFrame en formato estándar
    """
    if not datos_procesados:
        return pd.DataFrame()
    
    # Crear DataFrame con las columnas que espera el sistema
    df = pd.DataFrame(datos_procesados)
    
    # Renombrar columnas para que coincidan con el sistema existente
    df = df.rename(columns={
        'empleado': 'Empleado',
        'fecha': 'Fecha',
        'entrada': 'Entrada',
        'salida': 'Salida'
    })
    
    # Agregar columnas faltantes con valores por defecto
    df['Descuento Inventario'] = 0
    df['Descuento Caja'] = 0
    df['Retiro'] = 0
    
    # Convertir tipos de datos
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    
    return df

def validar_datos_pdf(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Valida que los datos extraídos del PDF sean correctos
    Ahora permite registros con entrada o salida faltante (incluyendo 0:00) para corrección manual
    
    Args:
        df: DataFrame a validar
        
    Returns:
        Tuple: (es_valido, lista_errores)
    """
    errores = []
    
    if df.empty:
        errores.append("No se pudieron extraer datos del PDF")
        return False, errores
    
    # Validar columnas requeridas
    columnas_requeridas = ['Empleado', 'Fecha', 'Entrada', 'Salida']
    for col in columnas_requeridas:
        if col not in df.columns:
            errores.append(f"Falta la columna: {col}")
    
    # Validar formatos de hora (permitir valores vacíos/NaN/0:00)
    for idx, row in df.iterrows():
        # Validar entrada solo si no está vacía ni es 0:00
        entrada_str = str(row['Entrada']).strip()
        if pd.notna(row['Entrada']) and entrada_str != '' and entrada_str not in ['0:00', '00:00']:
            try:
                datetime.strptime(entrada_str, '%H:%M')
            except:
                errores.append(f"Formato de hora de entrada inválido en fila {idx + 1}: {row['Entrada']}")
        
        # Validar salida solo si no está vacía ni es 0:00
        salida_str = str(row['Salida']).strip()
        if pd.notna(row['Salida']) and salida_str != '' and salida_str not in ['0:00', '00:00']:
            try:
                datetime.strptime(salida_str, '%H:%M')
            except:
                errores.append(f"Formato de hora de salida inválido en fila {idx + 1}: {row['Salida']}")
    
    return len(errores) == 0, errores


def detectar_registros_incompletos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detecta registros con entrada o salida faltante (pero no ambos).
    Si faltan AMBOS, se considera que el empleado no trabajó ese día y se excluye.
    Considera como "faltante": NaN, vacío, 'nan', '0:00', '00:00'
    
    Analiza también casos especiales donde el empleado marcó solo una vez 
    y el sistema no puede determinar si fue entrada o salida.
    
    Args:
        df: DataFrame con datos de empleados
        
    Returns:
        DataFrame: Registros con UNO de los datos faltante (necesitan corrección manual)
    """
    # Identificar registros incompletos (incluyendo 0:00 y 00:00)
    entrada_faltante = (
        df['Entrada'].isna() | 
        (df['Entrada'] == '') | 
        (df['Entrada'] == 'nan') |
        (df['Entrada'].astype(str).str.strip() == '0:00') |
        (df['Entrada'].astype(str).str.strip() == '00:00')
    )
    
    salida_faltante = (
        df['Salida'].isna() | 
        (df['Salida'] == '') | 
        (df['Salida'] == 'nan') |
        (df['Salida'].astype(str).str.strip() == '0:00') |
        (df['Salida'].astype(str).str.strip() == '00:00')
    )
    
    # SOLO incluir registros donde falta UNO (no ambos)
    # Si faltan ambos = no trabajó = excluir automáticamente
    necesita_correccion = (entrada_faltante & ~salida_faltante) | (~entrada_faltante & salida_faltante)
    
    # Filtrar registros que necesitan corrección
    df_incompletos = df[necesita_correccion].copy()
    
    # Agregar columna indicadora sin sugerencias automáticas
    df_incompletos['Dato_Faltante'] = ''
    df_incompletos['Horario_Registrado'] = ''
    df_incompletos['Tipo_Problema'] = ''
    
    for idx in df_incompletos.index:
        row = df_incompletos.loc[idx]
        
        if entrada_faltante.loc[idx]:
            df_incompletos.loc[idx, 'Dato_Faltante'] = 'Entrada'
            df_incompletos.loc[idx, 'Horario_Registrado'] = str(row['Salida'])
            df_incompletos.loc[idx, 'Tipo_Problema'] = 'Solo marcó salida'
            
        elif salida_faltante.loc[idx]:
            df_incompletos.loc[idx, 'Dato_Faltante'] = 'Salida'
            df_incompletos.loc[idx, 'Horario_Registrado'] = str(row['Entrada'])
            df_incompletos.loc[idx, 'Tipo_Problema'] = 'Solo marcó entrada'
    
    return df_incompletos


# Función de análisis automático eliminada - administrador tiene control total


def detectar_horarios_ambiguos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detecta registros con horarios que podrían ser ambiguos
    (por ejemplo, marcar a las 22:00 - ¿es entrada o salida?)
    
    Esta función complementa detectar_registros_incompletos para casos especiales
    donde hay entrada Y salida, pero parecen estar mal asignadas.
    
    Args:
        df: DataFrame con datos completos
        
    Returns:
        DataFrame: Registros con posibles asignaciones incorrectas
    """
    import pandas as pd
    from datetime import datetime
    
    horarios_ambiguos = []
    
    for idx, row in df.iterrows():
        try:
            # Verificar que ambos horarios existan
            if pd.isna(row['Entrada']) or pd.isna(row['Salida']):
                continue
                
            entrada_str = str(row['Entrada']).strip()
            salida_str = str(row['Salida']).strip()
            
            # Verificar que no sean valores inválidos
            if entrada_str in ['', 'nan', '0:00', '00:00'] or salida_str in ['', 'nan', '0:00', '00:00']:
                continue
            
            # Convertir a horas
            entrada = datetime.strptime(entrada_str, "%H:%M").time()
            salida = datetime.strptime(salida_str, "%H:%M").time()
            
            # Detectar patrones anómalos
            entrada_decimal = entrada.hour + entrada.minute/60
            salida_decimal = salida.hour + salida.minute/60
            
            # Casos sospechosos:
            sospechoso = False
            razon = ""
            
            # 1. Entrada muy tarde (después de las 20:00)
            if entrada_decimal >= 20:
                sospechoso = True
                razon = f"Entrada registrada a las {entrada_str} (muy tarde - ¿podría ser salida?)"
            
            # 2. Salida muy temprano (antes de las 10:00)
            elif salida_decimal <= 10:
                sospechoso = True
                razon = f"Salida registrada a las {salida_str} (muy temprano - ¿podría ser entrada?)"
            
            # 3. Entrada después de salida (mismo día)
            elif entrada_decimal > salida_decimal:
                sospechoso = True
                razon = f"Entrada ({entrada_str}) después de salida ({salida_str}) - posible error de asignación"
            
            if sospechoso:
                row_dict = row.to_dict()
                row_dict['Razon_Sospecha'] = razon
                row_dict['Entrada_Original'] = entrada_str
                row_dict['Salida_Original'] = salida_str
                horarios_ambiguos.append(row_dict)
                
        except Exception as e:
            continue
    
    return pd.DataFrame(horarios_ambiguos) if horarios_ambiguos else pd.DataFrame()


def filtrar_registros_sin_asistencia(df: pd.DataFrame) -> tuple:
    """
    Filtra y separa registros donde el empleado no trabajó (sin entrada ni salida).
    Considera como "faltante": NaN, vacío, 'nan', '0:00', '00:00'
    
    Args:
        df: DataFrame con datos de empleados
        
    Returns:
        tuple: (df_con_asistencia, df_sin_asistencia)
    """
    # Identificar registros sin entrada ni salida (incluyendo 0:00 y 00:00)
    entrada_faltante = (
        df['Entrada'].isna() | 
        (df['Entrada'] == '') | 
        (df['Entrada'] == 'nan') |
        (df['Entrada'].astype(str).str.strip() == '0:00') |
        (df['Entrada'].astype(str).str.strip() == '00:00')
    )
    
    salida_faltante = (
        df['Salida'].isna() | 
        (df['Salida'] == '') | 
        (df['Salida'] == 'nan') |
        (df['Salida'].astype(str).str.strip() == '0:00') |
        (df['Salida'].astype(str).str.strip() == '00:00')
    )
    
    # Registros sin asistencia (faltan ambos)
    sin_asistencia = entrada_faltante & salida_faltante
    
    df_sin_asistencia = df[sin_asistencia].copy()
    df_con_asistencia = df[~sin_asistencia].copy()
    
    return df_con_asistencia, df_sin_asistencia
