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
    .warning-lock { padding: 30px; background-color: #FFF2CC; border-left: 8px solid #FFC72C; border-radius: 8px; color: #7F6000; text-align: center; margin-top: 15px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# 2. URL MAESTRA DE TU WEB APP SCRIPT
URL_WEB_APP_MAESTRA = "https://script.google.com/macros/s/AKfycbx3ApkYqq0X_6JKi5Vz8ZcdnjTpddQKj-XAiis-Klu2EKFY7ONIQurwMe-qWWSURSMG9w/exec"

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

# ==========================================
# BARRA LATERAL (MÉTRICAS DEL TURNO SOLAMENTE)
# ==========================================
with st.sidebar:
    st.image("https://www.lundingold.com/assets/img/logo.png", width=180)
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
# ⚙️ MÓDULO: GESTIÓN DE INVENTARIO ÉLITE (BARRA LATERAL)
# ==========================================
with st.sidebar:
    st.write("---")
    with st.expander("🛠️ Panel de Control y Gestión de Inventario"):
        st.markdown("##### 📦 Consulta de Equipos en Pañol")
        
        buscar_admin = st.text_input(
            "🔍 Buscar por Serial o TAG:", 
            placeholder="Ej. SN-987654 o HERR-...", 
            key="search_admin_inv"
        ).strip().upper()
        
        try:
            if HERRAMIENTAS_DB:
                df_mini_inv = pd.DataFrame.from_dict(HERRAMIENTAS_DB, orient='index').reset_index()
                df_mini_inv.rename(columns={'index': 'TAG', 'nombre': 'Nombre', 'serial': 'Serial'}, inplace=True)
                
                if buscar_admin:
                    df_mini_inv = df_mini_inv[
                        df_mini_inv['Serial'].astype(str).str.upper().str.contains(buscar_admin) | 
                        df_mini_inv['TAG'].astype(str).str.upper().str.contains(buscar_admin)
                    ]
                
                st.dataframe(df_mini_inv[["TAG", "Nombre", "Serial"]], hide_index=True, use_container_width=True)
            else:
                st.info("📌 No se registran equipos en el pañol local.")
        except Exception:
            st.error("🔄 Error al cargar la vista previa del inventario.")
            
        st.write("---")
        st.markdown("##### ➕ Alta de Nuevas Herramientas")
        
        CLAVE_ACCESO_CORRECTA = "Lundin2026"
        clave_ingresada = st.text_input("🔑 Contraseña para Añadir Equipos:", type="password", placeholder="Clave de Supervisor SSO", key="admin_password_lock")
        
        if clave_ingresada == CLAVE_ACCESO_CORRECTA:
            st.success("🔓 Modo Editor Habilitado")
            nuevo_tag = st.text_input("Etiqueta (TAG):", placeholder="Ej. HERR-AMO-046", key="inv_tag").strip().upper()
            nuevo_nombre = st.text_input("Nombre del Equipo:", placeholder="Ej. Amoladora Angular 7\"", key="inv_nombre")
            nueva_marca = st.text_input("Marca:", placeholder="Ej. Bosch", key="inv_marca")
            nuevo_serial = st.text_input("Número de Serial:", placeholder="Ej. SN-987654", key="inv_serial")
            nueva_img = st.text_input("Enlace de Imagen (URL):", placeholder="https://...", key="inv_img")
            nueva_cat = st.selectbox("Categoría SSO:", ["CONSTRUCCION", "MECANICA", "ELECTRICA", "MINERIA"], key="inv_cat")
            
            st.markdown("**Puntos Críticos de Control:**")
            np1 = st.text_input("Punto 1:", placeholder="Ej. Estado del cable", key="inv_p1")
            np2 = st.text_input("Punto 2:", placeholder="Ej. Guarda colocada", key="inv_p2")
            np3 = st.text_input("Punto 3:", placeholder="Ej. Ajuste de disco", key="inv_p3")
            np4 = st.text_input("Punto 4:", placeholder="Ej. Interruptor operativo", key="inv_p4")
            np5 = st.text_input("Punto 5:", placeholder="Ej. Uso de Careta", key="inv_p5")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                btn_guardar = st.button("➕ Guardar Equipo", key="btn_guardar_nuevo_item", use_container_width=True)
            with col_btn2:
                btn_limpiar = st.button("🔄 Limpiar", key="btn_limpiar_formulario", use_container_width=True)
                
            if btn_limpiar:
                st.rerun()

            if btn_guardar:
                if not nuevo_tag or not nuevo_nombre:
                    st.error("❌ El TAG y el Nombre son campos obligatorios.")
                elif nuevo_tag in HERRAMIENTAS_DB:
                    st.error(f"❌ El TAG {nuevo_tag} ya existe en la base de datos.")
                else:
                    datos_inventario = {
                        "tipo_registro": "inventario",  
                        "tag": str(nuevo_tag), "nombre": str(nuevo_nombre), "marca": str(nueva_marca),
                        "serial": str(nuevo_serial), "imagen": str(nueva_img), "categoria": str(nueva_cat),
                        "p1": str(np1), "p2": str(np2), "p3": str(np3), "p4": str(np4), "p5": str(np5),
                        "p6": "", "p7": ""
                    }
                    try:
                        respuesta = requests.post(URL_WEB_APP_MAESTRA, data=datos_inventario, params=datos_inventario, timeout=10)
                        if respuesta.status_code == 200:
                            st.success(f"✅ ¡{nuevo_tag} guardado con éxito!")
                            st.cache_data.clear()
                            st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Error al conectar: {e}")
        elif clave_ingresada != "":
            st.error("❌ Contraseña Incorrecta.")
        else:
            st.info("💡 Ingrese la contraseña de Supervisor si necesita añadir una herramienta.")

# ==========================================
# 5. PANEL PRINCIPAL (ÁREA CENTRAL)
# ==========================================
st.markdown("""
    <div class="title-banner">
        <h2>Programa Concurso "Manos Seguras" — Lundin Gold</h2>
        <p>Estación Digital de Validación Visual de Herramientas de Potencia antes del Trabajo en Campo</p>
    </div>
""", unsafe_allow_html=True)

# 👤 UBICACIÓN CENTRAL DEL SELECTOR DE TÉCNICOS Y ÁREA DE TRABAJO
st.markdown("### 📋 Registro de Turno Obligatorio")
col_c1, col_c2 = st.columns(2)

with col_c1:
    operador = st.selectbox(
        "👤 Nombre del Operador / Técnico Firmante:",
        options=["-- Seleccione un Técnico --"] + LISTA_OPERADORES,
        key="main_operador_selector"
    )

with col_c2:
    area_trabajo = st.selectbox(
        "🏢 Área de Destino de la Herramienta:", 
        ["Electrico", "Mecanico", "Contratista", "Pasta"],
        key="main_area_selector"
    )

# 🔐 CANDADO DE SEGURIDAD INDUSTRIAL CENTRALIZADO
if operador == "-- Seleccione un Técnico --":
    st.markdown("""
        <div class="warning-lock">
            <h2>⚠️ CONTROL DE ACCESO RESTRINGIDO</h2>
            <p style="font-size: 18px;">Por políticas de SSO y control de guardia de Lundin Gold, 
            <b>seleccione su Nombre y Apellido en el menú de arriba</b> para desbloquear la estación de validación.</p>
        </div>
    """, unsafe_allow_html=True)
else:
    # 🔓 CONTENIDO DESBLOQUEADO INSTANTÁNEAMENTE AL SELECCIONAR TÉCNICO:
    st.write("---")

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

    # 6. PASO 2 Y PASO 3: DETALLE DE VALIDACIÓN E INFORME
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
                    fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    if chk1 and chk2 and chk3 and chk4 and chk5 and chk6 and chk7:
                        estado_final = "APROBADO"
                        detalle_final = comentarios if comentarios else "Todo operativo"
                        status_html = f"""<div class="success-box"><h4>✅ ¡CHECK-IN EXITOSO! HERRAMIENTA AUTORIZADA PARA TRABAJO</h4><p>El equipo <b>{tool_info['nombre']}</b> cumple las condiciones. ¡Operación segura habilitada!</p></div>"""
                        st.balloons()
                    else:
                        estado_final = "RECHAZADO"
                        fallas = []
                        if not chk1: fallas.append("Punto 1")
                        if not chk2: fallas.append("Punto 2")
                        if not chk3: fallas.append("Punto 3")
                        if not chk4: fallas.append("Punto 4")
                        if not chk5: fallas.append("Punto 5")
                        if not chk6: fallas.append("Punto 6")
                        if not chk7: fallas.append("Punto 7")
                        detalle_final = f"FALLA CRÍTICA EN: {', '.join(fallas)}. Obs: {comentarios}"
                        status_html = f"""<div class="danger-box"><h4>❌ ALERTA: HERRAMIENTA RETENIDA / BLOQUEADA</h4><p><b>¡No use este equipo!</b> Registro despachado automáticamente al supervisor de SSO.</p></div>"""

                    st.markdown(status_html, unsafe_allow_html=True)
                    
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
# ==========================================
    # 7. DASHBOARD REACTIVO + HISTORIAL COMPLETO DE DATOS
    # ==========================================
    st.write("---")
    
    # Control de estado interno para abrir/cerrar el panel analítico
    if 'ver_historial' not in st.session_state:
        st.session_state.ver_historial = False

    # Botón principal compacto
    if st.button("📊 Historial", key="btn_historial_principal"):
        st.session_state.ver_historial = not st.session_state.ver_historial
        st.rerun()

    # 🔓 Si el botón está activo, se despliega la analítica reactiva sobre la tabla completa
    if st.session_state.ver_historial:
        st.markdown("## 📈 Centro de Analítica Operacional — 'Manos Seguras'")
        
        try:
            # 📥 1. DETECCIÓN DINÁMICA DE COLUMNAS EN LA BASE MAESTRA
            col_estado = [c for c in df_historico_real.columns if 'ESTADO' in str(c).upper()][0]
            col_tag = [c for c in df_historico_real.columns if 'TAG' in str(c).upper() or 'CÓDIGO' in str(c).upper()][0]
            col_ope = [c for c in df_historico_real.columns if 'OPERADOR' in str(c).upper() or 'TÉCNICO' in str(c).upper()][0]

            # CONTROLES DE FILTRADO (Operan sobre la base completa de datos)
            st.markdown("#### 🔍 Filtros de Búsqueda Dinámica")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                f_tag = st.text_input("Filtrar por TAG de Equipo:", placeholder="Ej. HERR-AMO-046", key="f_tag").strip().upper()
            with col_f2:
                f_ope = st.text_input("Filtrar por Técnico / Persona:", placeholder="Ej. VÍCTOR", key="f_ope").strip().upper()

            # --- APLICACIÓN DEL FILTRADO EN CALIENTE EN LA TABLA COMPLETA ---
            df_filtrado = df_historico_real.copy()
            if f_tag:
                df_filtrado = df_filtrado[df_filtrado[col_tag].astype(str).str.upper().str.contains(f_tag)]
            if f_ope:
                df_filtrado = df_filtrado[df_filtrado[col_ope].astype(str).str.upper().str.contains(f_ope)]
            # ----------------------------------------------------------------

            total_f = len(df_filtrado)
            if total_f > 0:
                # 📊 2. CÁLCULO DE MÉTRICAS KPI (Basadas en la tabla filtrada)
                aprob_f = len(df_filtrado[df_filtrado[col_estado].astype(str).str.upper() == "APROBADO"])
                rechaz_f = len(df_filtrado[df_filtrado[col_estado].astype(str).str.upper() == "RECHAZADO"])
                porcentaje_seguro = (aprob_f / total_f) * 100

                st.write("---")
                col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
                with col_kpi1:
                    st.markdown(f'<div class="metric-card" style="border-top: 5px solid #002F6C;"><h3>{total_f}</h3><p>Muestras Filtradas</p></div>', unsafe_allow_html=True)
                with col_kpi2:
                    st.markdown(f'<div class="metric-card" style="border-top: 5px solid #27AE60;"><h3 style="color:#27AE60;">{aprob_f}</h3><p>Aprobadas ✔️</p></div>', unsafe_allow_html=True)
                with col_kpi3:
                    st.markdown(f'<div class="metric-card" style="border-top: 5px solid #CB6155;"><h3 style="color:#CB6155;">{rechaz_f}</h3><p>Rechazadas ❌</p></div>', unsafe_allow_html=True)
                with col_kpi4:
                    st.markdown(f'<div class="metric-card" style="border-top: 5px solid #F39C12;"><h3 style="color:#F39C12;">{porcentaje_seguro:.1f}%</h3><p>Índice Seguridad</p></div>', unsafe_allow_html=True)

                st.write("---")

                # 📈 3. GRÁFICOS INTERACTIVOS (Se alimentan solo de las 3 variables de la tabla filtrada)
                st.markdown("### 📈 Gráficos de Comportamiento Filtrado")
                c1, c2 = st.columns(2)
                
                with c1:
                    st.markdown("##### 👤 Estado de Inspección por Persona")
                    chart_data_ope = df_filtrado.groupby([col_ope, col_estado]).size().unstack(fill_value=0)
                    for col in ["APROBADO", "RECHAZADO"]:
                        if col not in chart_data_ope.columns: chart_data_ope[col] = 0
                    st.bar_chart(chart_data_ope[["APROBADO", "RECHAZADO"]], color=["#27AE60", "#CB6155"])

                with c2:
                    st.markdown("##### 🛠️ Estado de Inspección por TAG")
                    chart_data_tag = df_filtrado.groupby([col_tag, col_estado]).size().unstack(fill_value=0)
                    for col in ["APROBADO", "RECHAZADO"]:
                        if col not in chart_data_tag.columns: chart_data_tag[col] = 0
                    st.bar_chart(chart_data_tag[["APROBADO", "RECHAZADO"]], color=["#27AE60", "#CB6155"])

                # 📋 4. DATA FRAME VISUAL COMPLETÍSIMO (Muestra absolutamente todas las columnas)
                st.write("---")
                st.markdown("#### 📄 Registro Completo de Datos Filtrados (Últimos movimientos primero)")
                st.dataframe(
                    df_filtrado.iloc[::-1], 
                    use_container_width=True, 
                    hide_index=True
                )
                st.caption(f"💡 Visualizando {total_f} registros completos sincronizados con la base de datos.")
                
            else:
                st.warning("🔎 No se encontraron registros que coincidan con los filtros aplicados.")

        except Exception as e:
            st.info("📡 Sincronizando datos maestros... Realice una inspección para inicializar los gráficos.")