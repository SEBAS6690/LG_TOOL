import streamlit as st
import pandas as pd
import datetime
import time
import cv2
import numpy as np

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

# 2. BASE DE DATOS SIMULADA
if 'registro_inspecciones' not in st.session_state:
    st.session_state.registro_inspecciones = [
        {"Fecha": "2026-06-07 07:15", "Operador": "Carlos Mendoza", "ID Herramienta": "HERR-AMO-045", "Equipo": "Amoladora Angular", "Estado": "APROBADO", "Detalle": "Todo operativo"},
        {"Fecha": "2026-06-07 07:30", "Operador": "Juan Pérez", "ID Herramienta": "HERR-NEU-075", "Equipo": "Pistola de Impacto", "Estado": "RECHAZADO", "Detalle": "Mango agrietado"}
    ]

# 3. DICCIONARIO MAESTRO DE HERRAMIENTAS
HERRAMIENTAS_DB = {
    "HERR-AMO-045": {
        "nombre": "Amoladora Angular de 4.5\"",
        "categoria": "Corte y Desbaste",
        "imagen": "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?q=80&w=600&auto=format&fit=crop",
        "puntos": [
            "⚠️ **Punto 1 (Empuñadura):** ¿La empuñadura auxiliar está instalada, limpia y firme?",
            "⚠️ **Punto 2 (Guarda):** ¿La carcasa metálica está fija y orientada entre el disco y su mano?",
            "⚠️ **Punto 3 (Gatillo):** ¿El interruptor 'hombre muerto' se desactiva automáticamente al soltarlo?"
        ]
    },
    "HERR-NEU-075": {
        "nombre": "Pistola de Impacto Neumática 3/4\"",
        "categoria": "Ajuste Mecánico / Torque",
        "imagen": "https://images.unsplash.com/photo-1620917260582-8494b281b376?q=80&w=600&auto=format&fit=crop",
        "puntos": [
            "⚠️ **Punto 1 (Retención):** ¿El dado tiene su O-ring y pasador de seguridad colocados?",
            "⚠️ **Punto 2 (Carcasa/Goma):** ¿El recubrimiento absorbente de vibración en el mango está intacto?",
            "⚠️ **Punto 3 (Gatillo):** ¿El gatillo se mueve libremente sin atascos mecánicos?"
        ]
    },
    "HERR-TAL-102": {
        "nombre": "Taladro Percutor Industrial",
        "categoria": "Perforación",
        "imagen": "https://images.unsplash.com/photo-1504148455328-c376907d081c?q=80&w=600&auto=format&fit=crop",
        "puntos": [
            "⚠️ **Punto 1 (Mandril):** ¿El broquero ajusta de forma simétrica y se retiró la llave de apriete?",
            "⚠️ **Punto 2 (Tope):** ¿La varilla de tope de profundidad está fija para evitar atrapamientos directos?",
            "⚠️ **Punto 3 (Sentido):** ¿El inversor de marcha cambia con firmeza para evitar contragolpes?"
        ]
    }
}

# 4. BARRA LATERAL (SIDEBAR)
with st.sidebar:
    st.image("https://www.lundingold.com/assets/img/logo.png", width=180)
    st.markdown("### ⚙️ Configuración del Tótem")
    operador = st.text_input("👤 Nombre del Operador / Técnico:", placeholder="Ej. Carlos Mendoza")
    area_trabajo = st.selectbox("🏢 Área de Destino:", ["Planta de Beneficio", "Mantenimiento Mina", "Talleres Mecánicos", "Subestación Eléctrica"])
    
    st.write("---")
    st.markdown("### 📊 Métricas")
    df_actual = pd.DataFrame(st.session_state.registro_inspecciones)
    aprobados = len(df_actual[df_actual["Estado"] == "APROBADO"])
    rechazados = len(df_actual[df_actual["Estado"] == "RECHAZADO"])
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(f'<div class="metric-card"><h4 style="color:green;">{aprobados}</h4><small>Seguras</small></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown(f'<div class="metric-card"><h4 style="color:red;">{rechazados}</h4><small>Inseguras</small></div>', unsafe_allow_html=True)

# 5. PANEL PRINCIPAL
st.markdown("""
    <div class="title-banner">
        <h2>Programa Concurso "Manos Seguras" — Lundin Gold</h2>
        <p>Estación Digital de Validación Visual de Herramientas de Potencia antes del Trabajo en Campo</p>
    </div>
""", unsafe_allow_html=True)

# ==================== AQUÍ SE REEMPLAZÓ EL PASO 1 ====================
st.markdown("### 🔍 PASO 1: Escaneo de Código QR con la Cámara")

# Activación del componente de cámara en vivo
img_file_buffer = st.camera_input("Enfoque el código QR de la herramienta con la cámara de su dispositivo")

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
        st.warning("🔄 Buscando código QR... Asegúrese de que haya buena iluminación y enfoque el código de la herramienta.")

# Alternativa de escritura manual por si falla la cámara o estás en PC sin webcam
codigo_manual = st.text_input("O ingrese el ID manualmente si no dispone de cámara activa:", value=codigo_escaneado).strip().upper()
codigo_input = codigo_manual if codigo_manual else codigo_escaneado
# =====================================================================

# 6. PASO 2 Y PASO 3: DETALLE DE VALIDACIÓN
if codigo_input:
    if codigo_input in HERRAMIENTAS_DB:
        tool_info = HERRAMIENTAS_DB[codigo_input]
        
        st.write("---")
        st.markdown(f"### 🛠️ PASO 2: Inspección Visual Obligatoria — {tool_info['nombre']}")
        st.info(f"Categoría de Riesgo: **{tool_info['categoria']}** | Inspección enfocada 100% en la protección de dedos y manos.")
        
        col_img, col_chk = st.columns([1, 1.2])
        
        with col_img:
            st.image(tool_info["imagen"], caption=f"Puntos clave: {tool_info['nombre']}", use_container_width=True)
            
        with col_chk:
            st.markdown("#### Verifique el estado físico y marque las casillas correspondientes:")
            chk1 = st.checkbox(tool_info["puntos"][0])
            chk2 = st.checkbox(tool_info["puntos"][1])
            chk3 = st.checkbox(tool_info["puntos"][2])
            
            st.write("---")
            comentarios = st.text_input("📝 Notas u observaciones adicionales:", placeholder="Ej. Ninguna")
            
            st.markdown("### 💾 PASO 3: Conclusión del Registro")
            if st.button("🚀 Enviar Diagnóstico de Seguridad"):
                if not operador:
                    st.error("❌ Error: Debe ingresar el nombre del operador en la barra lateral.")
                else:
                    fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    if chk1 and chk2 and chk3:
                        st.markdown(f"""
                            <div class="success-box">
                                <h4>✅ ¡CHECK-IN EXITOSO! HERRAMIENTA AUTORIZADA</h4>
                                <p>El equipo <b>{tool_info['nombre']}</b> cumple las condiciones para mitigar atrapamientos.<br>
                                <b>¡Tus manos están en tus manos!</b></p>
                            </div>
                        """, unsafe_allow_html=True)
                        st.balloons()
                        
                        st.session_state.registro_inspecciones.insert(0, {
                            "Fecha": fecha_hora, "Operador": operador, "ID Herramienta": codigo_input,
                            "Equipo": tool_info['nombre'], "Estado": "APROBADO", "Detalle": comentarios if comentarios else "Todo operativo"
                        })
                    else:
                        st.markdown(f"""
                            <div class="danger-box">
                                <h4>❌ ALERTA: HERRAMIENTA BLOQUEADA</h4>
                                <p><b>¡No use este equipo!</b> Falta un control esencial de protección para sus manos.<br>
                                <i>Se despachó una notificación automática al supervisor de SSO del área {area_trabajo}.</i></p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        st.session_state.registro_inspecciones.insert(0, {
                            "Fecha": fecha_hora, "Operador": operador, "ID Herramienta": codigo_input,
                            "Equipo": tool_info['nombre'], "Estado": "RECHAZADO", "Detalle": f"FALLA DE SEGURIDAD: {comentarios}"
                        })
                        
    else:
        st.error("❌ El código ingresado no coincide con ninguna herramienta registrada en el inventario.")

# 7. HISTORIAL
st.write("---")
st.markdown("### 📋 Registro Histórico de Inspecciones (Módulo Centralizado SSO)")
df_log = pd.DataFrame(st.session_state.registro_inspecciones)
st.dataframe(df_log, use_container_width=True)