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

# 🚨 2. URL MAESTRA DE TU WEB APP SCRIPT (La única que necesitas para todo)
# Reemplaza esta dirección con la URL real de Apps Script que termina en /exec
URL_WEB_APP_MAESTRA = "https://script.google.com/macros/s/AQUÍ_PEGA_TU_ID_DE_EXEC_DE_APPS_SCRIPT/exec"

# 3. CONEXIÓN DINÁMICA AL INVENTARIO DE GOOGLE SHEETS
ID_DOCUMENTO = "1et_T6dZZWpCc2Q4BMrASdo76mGtIvBLeaBdBR358RS0"
URL_INVENTARIO = f"https://docs.google.com/spreadsheets/d/{ID_DOCUMENTO}/gviz/tq?tqx=out:csv&sheet=Inventario"

@st.cache_data(ttl="3s")
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
                    f"⚠️ **Punto 4:** {fila['Punto4']}",
                    f"⚠️ **Punto 5:** {fila['Punto5']}",
                    f"⚠️ **Punto 6:** {fila['Punto6']}",
                    f"⚠️ **Punto 7:** {fila['Punto7']}"
                ]
            }
        return db_dinamica
    except Exception as e:
        st.error(f"⚠️ Error al leer la pestaña 'Inventario': {e}")
        return {}

HERRAMIENTAS_DB = cargar_inventario_dinamico()

# 4. CONEXIÓN A LAS BASES DE DATOS DE PERSONAL Y RESPUESTAS
URL_PERSONAL = f"https://docs.google.com/spreadsheets/d/{ID_DOCUMENTO}/gviz/tq?tqx=out:csv&sheet=Personal"
URL_RESPUESTAS = f"https://docs.google.com/spreadsheets/d/{ID_DOCUMENTO}/gviz/tq?tqx=out:csv&sheet=Respuestas%20de%20formulario%201"

@st.cache_data(ttl="3s")
def cargar_personal_dinamico():
    try:
        df_per = pd.read_csv(URL_PERSONAL)
        lista_nombres = df_per['Nombre'].dropna().astype(str).tolist()
        return sorted(lista_nombres)
    except Exception:
        return ["Sebastián Yánez", "Víctor Morillo"]

LISTA_OPERADORES = cargar_personal_dinamico()

try:
    df_historico_real = pd.read_csv(URL_RESPUESTAS)
    df_historico_real.columns = df_historico_real.columns.str.upper().str.strip()
except Exception:
    df_historico_real = pd.DataFrame()

# BARRA LATERAL (Configuración y Métricas en Tiempo Real)
with st.sidebar:
    st.image("https://www.lundingold.com/assets/img/logo.png", width=180)
    st.markdown("### ⚙️ Configuración del Tótem")
    
    operador = st.selectbox(
        "👤 Nombre del Operador / Técnico:",
        options=["-- Seleccione un Técnico --"] + LISTA_OPERADORES
    )
    
    area_trabajo = st.selectbox("🏢 Área de Destino:", ["Mantenimiento Mina", "Planta de Beneficio", "Talleres Mecánicos", "Subestación Eléctrica"])
    
    st.write("---")
    st.markdown("### 📊 Métricas de Turno Real")
    
    if not df_historico_real.empty and "ESTADO" in df_historico_real.columns:
        aprobados = len(df_historico_real[df_historico_real["ESTADO"] == "APROBADO"])
        rechazados = len(df_historico_real[df_historico_real["ESTADO"] == "RECHAZADO"])
    else:
        aprobados, rechazados = 0, 0
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(f'<div class="metric-card"><h4 style="color:green;">{aprobados}</h4><small>Seguras</small></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown(f'<div class="metric-card"><h4 style="color:red;">{rechazados}</h4><small>Inseguras</small></div>', unsafe_allow_html=True)

# ==========================================
# ⚙️ MÓDULO: ADMINISTRACIÓN DE INVENTARIO CORREGIDO (SIN JSON)
# ==========================================
with st.sidebar:
    st.write("---")
    with st.expander("🛠️ Panel de Administración (Añadir Equipos)"):
        st.markdown("##### Registrar Nueva Herramienta o Ítems")
        
        nuevo_tag = st.text_input("Etiqueta (TAG):", placeholder="Ej. HERR-AMO-046").strip().upper()
        nuevo_nombre = st.text_input("Nombre del Equipo:", placeholder="Ej. Amoladora Angular 7\"")
        nueva_marca = st.text_input("Marca:", placeholder="Ej. Bosch")
        nuevo_serial = st.text_input("Número de Serial:", placeholder="Ej. SN-987654")
        nueva_img = st.text_input("Enlace de Imagen (URL):", placeholder="https://...")
        nueva_cat = st.selectbox("Categoría SSO:", ["CONSTRUCCION", "MECANICA", "ELECTRICA", "MINERIA"])
        
        st.markdown("**Puntos Críticos de Control:**")
        np1 = st.text_input("Punto 1:", placeholder="Ej. Estado del cable")
        np2 = st.text_input("Punto 2:", placeholder="Ej. Guarda colocada")
        np3 = st.text_input("Punto 3:", placeholder="Ej. Ajuste de disco")
        np4 = st.text_input("Punto 4:", placeholder="Ej. Interruptor operativo")
        np5 = st.text_input("Punto 5:", placeholder="Ej. Uso de Careta")
        np6 = st.text_input("Punto 6:", placeholder="Ej. Sin ruidos raros")
        np7 = st.text_input("Punto 7:", placeholder="Ej. Mangos ajustados")

        if st.button("➕ Guardar en Inventario Maestro", key="btn_guardar_nuevo_item"):
            if not nuevo_tag or not nuevo_nombre:
                st.error("❌ El TAG y el Nombre son campos obligatorios.")
            else:
                # 🛠️ Datos de formulario en texto plano puro enviando el identificador "inventario"
                datos_inventario = {
                    "tipo_registro": "inventario",  
                    "tag": str(nuevo_tag),
                    "nombre": str(nuevo_nombre),
                    "marca": str(nueva_marca),
                    "serial": str(nuevo_serial),
                    "imagen": str(nueva_img),
                    "categoria": str(nueva_cat),
                    "p1": str(np1), "p2": str(np2), "p3": str(np3), "p4": str(np4), "p5": str(np5), "p6": str(np6), "p7": str(np7)
                }
                
                try:
                    # Envío idéntico a los diagnósticos mediante data= y params= para evitar fallas
                    respuesta = requests.post(URL_WEB_APP_MAESTRA, data=datos_inventario, params=datos_inventario, timeout=10)
                    if respuesta.status_code == 200:
                        st.success(f"✅ ¡{nuevo_tag} registrado en la pestaña INVENTARIO exitosamente!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ Error de comunicación con el servidor: {respuesta.status_code}")
                except Exception as e:
                    st.error(f"⚠️ Error al conectar: {e}")

# 5. PANEL PRINCIPAL (Encabezado)
st.markdown("""
    <div class="title-banner">
        <h2>Programa Concurso "Manos Seguras" — Lundin Gold</h2>
        <p>Estación Digital de Validación Visual de Herramientas de Potencia antes del Trabajo en Campo</p>
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

codigo_manual = st.text_input("O ingrese el TAG manualmente si es necesario:", value=codigo_escaneado).strip().upper()
codigo_input = codigo_manual if codigo_manual else codigo_escaneado

# 6. PASO 2 Y PASO 3: DETALLE DE VALIDACIÓN E INFORME (SIN JSON)
if codigo_input:
    if codigo_input in HERRAMIENTAS_DB:
        tool_info = HERRAMIENTAS_DB[codigo_input]
        
        st.write("---")
        st.markdown(f"### 🛠️ PASO 2: Ficha Técnica del Activo e Inspección")
        
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
            chk1 = st.checkbox(tool_info["puntos"][0], key="c1")
            chk2 = st.checkbox(tool_info["puntos"][1], key="c2")
            chk3 = st.checkbox(tool_info["puntos"][2], key="c3")
            chk4 = st.checkbox(tool_info["puntos"][3], key="c4")
            chk5 = st.checkbox(tool_info["puntos"][4], key="c5")
            chk6 = st.checkbox(tool_info["puntos"][5], key="c6")
            chk7 = st.checkbox(tool_info["puntos"][6], key="c7")
            
            st.write("---")
            comentarios = st.text_input("📝 Notas u observaciones adicionales:", placeholder="Ej. Carcasa en buen estado")
            
            st.markdown("### 💾 PASO 3: Conclusión del Registro")
            
            if st.button("🚀 Enviar Diagnóstico de Seguridad", key="btn_enviar_diagnose"):
                if operador == "-- Seleccione un Técnico --":
                    st.error("❌ Error: Debe seleccionar el nombre del operador en la barra lateral para firmar el registro.")
                else:
                    fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    if chk1 and chk2 and chk3 and chk4 and chk5 and chk6 and chk7:
                        estado_final = "APROBADO"
                        detalle_final = comentarios if comentarios else "Todo operativo"
                        status_html = f"""<div class="success-box"><h4>✅ ¡CHECK-IN EXITOSO! HERRAMIENTA AUTORIZADA PARA TRABAJO</h4><p>El equipo <b>{tool_info['nombre']}</b> cumple las condiciones. ¡Operación segura habilitada!</p></div>"""
                        st.balloons()
                    else:
                        estado_final = "RECHAZADO"
                        detalle_final = f"FALLA CRÍTICA DE SEGURIDAD: {comentarios}"
                        status_html = f"""<div class="danger-box"><h4>❌ ALERTA: HERRAMIENTA RETENIDA / BLOQUEADA</h4><p><b>¡No use este equipo!</b> Registro despachado automáticamente al supervisor de SSO.</p></div>"""

                    st.markdown(status_html, unsafe_allow_html=True)
                    
                    # 🛠️ Datos de formulario en texto plano puro enviando el identificador "diagnostico"
                    datos_envio = {
                        "tipo_registro": "diagnostico",  
                        "fecha": str(fecha_hora),
                        "operador": str(operador),
                        "tag": str(codigo_input),
                        "herramienta": str(tool_info['nombre']),
                        "marca": str(tool_info['marca']),
                        "serial": str(tool_info['serial']),
                        "estado": str(estado_final),
                        "detalle": str(detalle_final)
                    }
                    
                    try:
                        respuesta = requests.post(URL_WEB_APP_MAESTRA, data=datos_envio, params=datos_envio, timeout=10)
                        if respuesta.status_code == 200:
                            st.success("💾 ¡Diagnóstico sincronizado en la base de datos de Google Sheets!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ Error de transmisión del servidor: {respuesta.status_code}")
                    except Exception as e:
                        st.error(f"⚠️ Error al conectar con la base de datos: {e}")
                        
    else:
        st.error("❌ El código escaneado o ingresado no corresponde a ningún activo registrado en el pañol.")

# 7. HISTORIAL VISUAL EN TIEMPO REAL DESDE GOOGLE SHEETS
st.write("---")
st.markdown("### 📋 Registro Histórico de Inspecciones (Tiempo Real)")

try:
    df_historico = pd.read_csv(URL_RESPUESTAS)
    if not df_historico.empty:
        df_historico = df_historico.iloc[::-1]
        st.dataframe(df_historico, use_container_width=True, hide_index=True)
    else:
        st.info("📌 Aún no hay registros guardados en la base de datos central.")
except Exception as e:
    st.warning("🔄 Cargando actualización del historial...")