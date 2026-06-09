import streamlit as st
import pandas as pd
import datetime
import requests

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Lundin Gold — Manos Seguras",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos visuales del Tótem Industrial para el Concurso
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
        border-top: 4px solid #1A365D;
        margin-bottom: 10px;
    }
    .metric-card h4 { margin: 0; font-size: 28px; }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 20px;
        border-radius: 8px;
        border-left: 6px solid #28a745;
        margin-top: 15px;
    }
    .danger-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 20px;
        border-radius: 8px;
        border-left: 6px solid #dc3545;
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN MAESTRA A TU GOOGLE SHEETS
# ==========================================
ID_DOCUMENTO = "1et_T6dZZWpCc2Q4BMrASdo76mGtIvBLeaBdBR358RS0"

URL_INVENTARIO = f"https://docs.google.com/spreadsheets/d/{ID_DOCUMENTO}/gviz/tq?tqx=out:csv&sheet=Inventario"
URL_PERSONAL = f"https://docs.google.com/spreadsheets/d/{ID_DOCUMENTO}/gviz/tq?tqx=out:csv&sheet=Personal"
URL_RESPUESTAS = f"https://docs.google.com/spreadsheets/d/{ID_DOCUMENTO}/gviz/tq?tqx=out:csv&sheet=Form_Responses"

# ==========================================
# 3. CARGA DE DATOS DINÁMICOS (HASTA 10 PUNTOS)
# ==========================================
@st.cache_data(ttl="3s")
def cargar_inventario_dinamico():
    try:
        df_inv = pd.read_csv(URL_INVENTARIO)
        df_inv.columns = df_inv.columns.str.strip()
        db_dinamica = {}
        
        for _, fila in df_inv.iterrows():
            tag_activo = str(fila['TAG']).strip().upper()
            lista_puntos = []
            
            # Barrido elástico del Punto 1 al 10 detectando celdas con texto válido
            for i in range(1, 11):
                col_name = f"Punto{i}"
                if col_name in df_inv.columns:
                    valor_punto = str(fila[col_name]).strip()
                    if valor_punto and valor_punto.lower() != 'nan' and valor_punto != '':
                        lista_puntos.append(f"⚠️ **Punto {i}:** {valor_punto}")
            
            db_dinamica[tag_activo] = {
                "nombre": fila['Nombre'],
                "categoria": fila['Categoria'],
                "marca": fila['Marca'],
                "serial": fila['Serial'],
                "imagen": fila['Imagen'],
                "puntos": lista_puntos
            }
        return db_dinamica
    except Exception as e:
        st.error(f"⚠️ Error al leer la pestaña 'Inventario': {e}")
        return {}

@st.cache_data(ttl="3s")
def cargar_personal_dinamico():
    try:
        df_per = pd.read_csv(URL_PERSONAL)
        lista_nombres = df_per['Nombre'].dropna().astype(str).tolist()
        return sorted(lista_nombres)
    except Exception:
        return ["CESAR SARABIA", "SEBASTIAN YANEZ", "MIGUEL CUJILEMA"]

LISTA_OPERADORES = cargar_personal_dinamico()
INVENTARIO_HERRAMIENTAS = cargar_inventario_dinamico()

try:
    df_historico_real = pd.read_csv(URL_RESPUESTAS)
    df_historico_real.columns = df_historico_real.columns.str.strip()
except Exception:
    df_historico_real = pd.DataFrame()

# ==========================================
# 4. BARRA LATERAL (CONFIGURACIÓN Y MÉTRICAS)
# ==========================================
with st.sidebar:
    st.image("https://www.lundingold.com/assets/img/logo.png", width=180)
    st.markdown("### ⚙️ Configuración del Tótem")
    
    operador = st.selectbox(
        "👤 Nombre del Operador / Técnico:",
        options=["-- Seleccione un Técnico --"] + LISTA_OPERADORES
    )
    
    area_trabajo = st.selectbox(
        "🏢 Área de Destino:", 
        ["Mantenimiento Mina", "Planta de Beneficio", "Talleres Mecánicos", "Subestación Eléctrica"]
    )
    
    st.write("---")
    st.markdown("### 📊 Métricas de Turno Real")
    
    aprobados, rechazados = 0, 0
    if not df_historico_real.empty:
        col_estado = [c for c in df_historico_real.columns if c.upper() == "ESTADO"]
        if col_estado:
            col_activa = col_estado[0]
            aprobados = len(df_historico_real[df_historico_real[col_activa].astype(str).str.upper() == "APROBADO"])
            rechazados = len(df_historico_real[df_historico_real[col_activa].astype(str).str.upper() == "RECHAZADO"])
            
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(f'<div class="metric-card"><h4 style="color:green;">{aprobados}</h4><small>Seguras</small></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown(f'<div class="metric-card"><h4 style=")