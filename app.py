import streamlit as st
import pandas as pd
import datetime
import cv2
import numpy as np
import requests

# 1. CONFIGURACIÓN DE LA PÁGINA (Estilo Industrial / Corporativo)
st.set_page_config(
    page_title="Smart Tool Check-In | Lundin Gold",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para la interfaz del Tótem
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; background-color: #002F6C; color: white; font-weight: bold; border-radius: 6px; height: 45px; }
    .stButton>button:hover { background-color: #001F4D; color: white; border: 1px solid #FFC72C; }
    .title-banner { padding: 20px; background-color: #002F6C; color: white; border-radius: 8px; margin-bottom: 25px; border-bottom: 5px solid #FFC72C; }
    .danger-box { padding: 20px; background-color: #FADBD8; border-left: 6px solid #CD6155; border-radius: 5px; margin-bottom: 15px; color: #78281F; }
    .success-box { padding: 20px; background-color: #D4EFDF; border-left: 6px solid #27AE60; border-radius: 5px; margin-bottom: 15px; color: #145A32; }
    .metric-card { background-color: white; padding: 15px; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #E5E7E9; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# 2. HISTORIAL LOCAL TEMPORAL (Métricas rápidas del dispositivo)
if 'registro_inspecciones' not in st.session_state:
    st.session_state.registro_inspecciones = []

# 3. CONEXIÓN DINÁMICA AL INVENTARIO DE GOOGLE SHEETS
# 3. CONEXIÓN DINÁMICA AL INVENTARIO DE GOOGLE SHEETS
ID_DOCUMENTO = "1et_T6dZZWpCc2Q4BMrASdo76mGtIvBLeaBdBR358RS0"
URL_INVENTARIO = f"https://docs.google.com/spreadsheets/d/{ID_DOCUMENTO}/gviz/tq?tqx=out:csv&sheet=Inventario"

@st.cache_data(ttl="5s")  # Cache ultra corto para que detecte rápido los cambios que hagas en el Excel
def cargar_inventario_dinamico():
    try:
        df_inv = pd.read_csv(URL_INVENTARIO)
        db_dinamica = {}
        for _, fila in df_inv.iterrows():
            tag_activo = str(fila['TAG']).strip().upper()
            db_dinamica[tag_activo] = {
                "nombre": fila['Nombre'],
                "categoria": fila['Categoria'],
                "marca": fila['Marca'],
                "serial": fila['Serial'],
                "imagen": fila['Imagen'],
                "puntos": [
                    f"⚠️ **Punto 1:** {fila['Punto1']}",
                    f"⚠️ **Punto 2:** {fila['Punto2']}",
                    f"⚠️ **Punto 3:** {fila['Punto3']}",
                     f"⚠️ **Punto 1:** {fila['Punto4']}",
                    f"⚠️ **Punto 2:** {fila['Punto5']}",
                    f"⚠️ **Punto 3:** {fila['Punto6']}",
                    f"⚠️ **Punto 3:** {fila['Punto6']}"
                ]
            }
        return db_dinamica
    except Exception as e:
        st.error(f"⚠️ Error al leer la pestaña 'Inventario': {e}")
        return {}

# Poblar el diccionario maestro desde la nube
HERRAMIENTAS_DB = cargar_inventario_dinamico()

# 4. CONEXIÓN Y CARGA DE LA LISTA DE PERSONAL
URL_PERSONAL = f"https://docs.google.com/spreadsheets/d/{ID_DOCUMENTO}/gviz/tq?tqx=out:csv&sheet=Personal"

@st.cache_data(ttl="10s")
def cargar_personal_dinamico():
    try:
        df_per = pd.read_csv(URL_PERSONAL)
        # Extrae los nombres de la columna 'Nombre' y elimina filas vacías
        lista_nombres = df_per['Nombre'].dropna().astype(str).tolist()
        return sorted(lista_nombres)
    except Exception:
        # Lista de respaldo por si el Excel está vacío o falla el internet
        return ["Sebastián Yánez", "Víctor Morillo"]

# Cargar el listado de operadores autorizados
LISTA_OPERADORES = cargar_personal_dinamico()

# BARRA LATERAL (SIDEBAR MODIFICADA)
with st.sidebar:
    st.image("https://www.lundingold.com/assets/img/logo.png", width=180)
    st.markdown("### ⚙️ Configuración del Tótem")
    
    # 🔄 CAMBIO CRÍTICO: De campo de texto a lista desplegable inteligente
    operador = st.selectbox(
        "👤 Nombre del Operador / Técnico:",
        options=["-- Seleccione un Técnico --"] + LISTA_OPERADORES
    )
    
    area_trabajo = st.selectbox("🏢 Área de Destino:", ["Mantenimiento Mina", "Planta de Beneficio", "Talleres Mecánicos", "Subestación Eléctrica"])
    
    st.write("---")
    st.markdown("### 📊 Métricas de Turno Local")
    if st.session_state.registro_inspecciones:
        df_actual = pd.DataFrame(st.session_state.registro_inspecciones)
        aprobados = len(df_actual[df_actual["Estado"] == "APROBADO"])
        rechazados = len(df_actual[df_actual["Estado"] == "RECHAZADO"])
    else:
        aprobados, rechazados = 0, 0
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(f'<div class="metric-card"><h4 style="color:green;">{aprobados}</h4><small>Seguras</small></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown(f'<div class="metric-card"><h4 style="color:red;">{rechazados}</h4><small>Inseguras</small></div>', unsafe_allow_html=True)

# 5. PANEL PRINCIPAL (Encabezado)
st.markdown("""
    <div class="title-banner">
        <h2>Programa Concurso "Manos Seguras" — Lundin Gold</h2>
        <p>Estación Digital de Validation Visual de Herramientas de Potencia antes del Trabajo en Campo</p>
    </div>
""", unsafe_allow_html=True)

# PASO 1: ESCANEO DE CÓDIGO QR CON LA CÁMARA
st.markdown("### 🔍 PASO 1: Escaneo de Código QR")
img_file_buffer = st.camera_input("Enfoque el código QR de la placa de aluminio anodizado")

codigo_escaneado = ""

if img_file_buffer is not None:
    bytes_data = img_file_buffer.getvalue()
    cv_image = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    
    detector = cv2.QRCodeDetector()
    data, bbox, straight_qrcode = detector.detectAndDecode(cv_image)
    
    if data:
        codigo_escaneado = data.upper().strip()
        st.success(f"✅ ¡Código QR detectado!: `{codigo_escaneado}`")
    else:
        st.warning("🔄 Analizando imagen... Asegúrese de enfocar el código QR centrado y con buena luz.")

# Entrada manual alternativa
codigo_manual = st.text_input("O ingrese el TAG manualmente si es necesario:", value=codigo_escaneado).strip().upper()
codigo_input = codigo_manual if codigo_manual else codigo_escaneado

# 6. PASO 2 Y PASO 3: DETALLE DE VALIDACIÓN E INFORME
if codigo_input:
    if codigo_input in HERRAMIENTAS_DB:
        tool_info = HERRAMIENTAS_DB[codigo_input]
        
        st.write("---")
        st.markdown(f"### 🛠️ PASO 2: Ficha Técnica del Activo e Inspección")
        
        # Tabla dinámica de especificaciones técnicas
        col_datos, col_espacio = st.columns([2, 1])
        with col_datos:
            datos_tabla = {
                "PARÁMETRO INDUSTRIAL": ["TAG / CÓDIGO QR", "HERRAMIENTA / EQUIPO", "MARCA / FABRICANTE", "NÚMERO DE SERIAL", "CATEGORÍA DE RIESGO SSO"],
                "DETALLES ESPECÍFICOS": [codigo_input, tool_info['nombre'], tool_info['marca'], tool_info['serial'], tool_info['categoria']]
            }
            df_ficha = pd.DataFrame(datos_tabla)
            st.table(df_ficha)
            
        st.info("💡 Complete la validación visual obligatoria enfocada en la protección de extremidades superiores.")
        
        col_img, col_chk = st.columns([1, 1.2])
        
        with col_img:
            if pd.isna(tool_info["imagen"]) or str(tool_info["imagen"]).strip() == "":
                st.warning("📷 No hay imagen configurada para esta herramienta en el Excel.")
            else:
                st.image(tool_info["imagen"], caption=f"Control Crítico: {tool_info['nombre']}", use_container_width=True)
            
        with col_chk:
            st.markdown("#### Verifique el estado físico y marque las casillas correspondientes:")
            chk1 = st.checkbox(tool_info["puntos"][0])
            chk2 = st.checkbox(tool_info["puntos"][1])
            chk3 = st.checkbox(tool_info["puntos"][2])
            chk2 = st.checkbox(tool_info["puntos"][3])
            chk3 = st.checkbox(tool_info["puntos"][4])
            
            st.write("---")
            comentarios = st.text_input("📝 Notas u observaciones adicionales:", placeholder="Ej. Carcasa en buen estado")
            
            st.markdown("### 💾 PASO 3: Conclusión del Registro")
            
            if st.button("🚀 Enviar Diagnóstico de Seguridad", key="btn_enviar_diagnose"):
                if not operador:
                    st.error("❌ Error: Debe ingresar el nombre del operador en la barra lateral para firmar el registro.")
                else:
                    fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    if chk1 and chk2 and chk3:
                        estado_final = "APROBADO"
                        detalle_final = comentarios if comentarios else "Todo operativo"
                        status_html = f"""<div class="success-box"><h4>✅ ¡CHECK-IN EXITOSO! HERRAMIENTA AUTORIZADA PARA TRABAJO</h4><p>El equipo <b>{tool_info['nombre']}</b> cumple las condiciones. ¡Operación segura habilitada!</p></div>"""
                        st.balloons()
                    else:
                        estado_final = "RECHAZADO"
                        detalle_final = f"FALLA CRÍTICA DE SEGURIDAD: {comentarios}"
                        status_html = f"""<div class="danger-box"><h4>❌ ALERTA: HERRAMIENTA RETENIDA / BLOQUEADA</h4><p><b>¡No use este equipo!</b> Registro despachado automáticamente al supervisor de SSO.</p></div>"""

                    st.markdown(status_html, unsafe_allow_html=True)

                    # 🚀 ENVÍO DIRECTO A TU GOOGLE FORMS REAL
                    URL_FORM = "https://docs.google.com/forms/d/e/1FAIpQLSecO_N06RlShHidRPO3JYuveetxHHqqdOpPHisMeMuTdT5Omw/formResponse"
                    
                    datos_envio = {
                        "entry.94170114": fecha_hora,
                        "entry.1584737127": operador,
                        "entry.612752579": codigo_input,
                        "entry.43000870": tool_info['nombre'],
                        "entry.741366664": tool_info['marca'],
                        "entry.1913540372": tool_info['serial'],
                        "entry.2081212052": estado_final,
                        "entry.19695549": detalle_final
                    }
                    
                    try:
                        requests.post(URL_FORM, data=datos_envio)
                        st.success("💾 ¡Sincronizado con la base de datos de Google Sheets!")
                        
                        # Agregar al historial de la pantalla actual
                        st.session_state.registro_inspecciones.insert(0, {
                            "Fecha": fecha_hora, "Operador": operador, "TAG": codigo_input,
                            "Herramienta": tool_info['nombre'], "Marca": tool_info['marca'], 
                            "Serial": tool_info['serial'], "Estado": estado_final, "Detalle": detalle_final
                        })
                    except Exception as e:
                        st.error(f"⚠️ Error al conectar con la base de datos: {e}")
                        
    else:
        st.error("❌ El código escaneado o ingresado no corresponde a ningún activo registrado en el pañol.")

# 7. HISTORIAL VISUAL EN TIEMPO REAL DESDE GOOGLE SHEETS
st.write("---")
st.markdown("### 📋 Registro Histórico de Inspecciones (Tiempo Real)")

# URL automática para leer la pestaña de respuestas
URL_RESPUESTAS = f"https://docs.google.com/spreadsheets/d/{ID_DOCUMENTO}/gviz/tq?tqx=out:csv&sheet=Respuestas%20de%20formulario%201"

try:
    # Descarga las respuestas actuales directamente de la nube
    df_historico = pd.read_csv(URL_RESPUESTAS)
    
    if not df_historico.empty:
        # Ordenar para que la última inspección aparezca primerita en la lista
        df_historico = df_historico.iloc[::-1]
        
        # Mostrar la tabla estilizada en la pantalla del Tótem
        st.dataframe(
            df_historico, 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("📌 Aún no hay registros guardados en la base de datos central.")
except Exception as e:
    st.warning("🔄 Cargando actualización del historial... Si tarda, realice una nueva inspección o recargue la página.")