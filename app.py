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
        st.markdown(f'<div class="metric-card"><h4 style="color:red;">{rechazados}</h4><small>Inseguras</small></div>', unsafe_allow_html=True)

# ==========================================
# 5. CUERPO PRINCIPAL (INTERFAZ DE CONTROL)
# ==========================================
st.markdown('# Programa Concurso "Manos Seguras" — Lundin Gold')
st.markdown('#### Estación Digital de Validación Visual de Herramientas de Potencia antes del Trabajo en Campo')
st.write("---")

st.markdown("### 🔍 PASO 1: Ingreso de la Herramienta")
codigo_input = st.text_input("Digite o escanee el TAG de la herramienta (Ej: ELE-TL-001):", placeholder="Ej: ELE-TL-001").strip().upper()

if codigo_input:
    if codigo_input in INVENTARIO_HERRAMIENTAS:
        tool_info = INVENTARIO_HERRAMIENTAS[codigo_input]
        
        st.success(f"✨ ¡Herramienta {codigo_input} identificada con éxito!")
        st.write("---")
        st.markdown("### 📋 PASO 2: Matriz de Control Visual Obligatoria")
        
        col_img, col_chk = st.columns([1, 2])
        
        with col_img:
            st.image(tool_info["imagen"], caption=f"{tool_info['nombre']} - {tool_info['marca']}", use_container_width=True)
            st.info(f"**Especificaciones Técnicas:**\n* **TAG:** {codigo_input}\n* **Categoría:** {tool_info['categoria']}\n* **Serial:** {tool_info['serial']}")
            
        with col_chk:
            st.markdown("#### Verifique el estado físico y marque las casillas correspondientes:")
            
            checks_estados = []
            for idx, texto_punto in enumerate(tool_info["puntos"]):
                chk = st.checkbox(texto_punto, key=f"chk_{codigo_input}_{idx}")
                checks_estados.append((f"Punto {idx+1}", chk))
                
            st.write("---")
            comentarios = st.text_input("📝 Notas u observaciones adicionales:", placeholder="Ej. Todo conforme", key=f"obs_{codigo_input}")
            
            st.markdown("### 💾 PASO 3: Conclusión del Registro")
            
          if st.button("🚀 Enviar Diagnóstico de Seguridad", key="btn_enviar_diagnose"):
                if operador == "-- Seleccione un Técnico --":
                    st.error("❌ Error: Debe seleccionar su nombre de la lista en la barra lateral para firmar el registro.")
                else:
                    fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    todos_aprobados = all(estado for _, estado in checks_estados)
                    
                    if todos_aprobados:
                        estado_final = "APROBADO"
                        detalle_final = comentarios if comentarios else "Todo operativo"
                        status_html = """<div class="success-box"><h4>✅ ¡CHECK-IN EXITOSO! HERRAMIENTA AUTORIZADA</h4><p>El equipo cumple las condiciones de seguridad en campo.</p></div>"""
                        st.balloons()
                    else:
                        estado_final = "RECHAZADO"
                        fallas = [f"Punto {i+1}" for i, (_, estado) in enumerate(checks_estados) if not estado]
                        detalle_final = f"FALLA CRÍTICA EN: {', '.join(fallas)}. Obs: {comentarios}"
                        status_html = """<div class="danger-box"><h4>❌ ALERTA: HERRAMIENTA RETENIDA / BLOQUEADA</h4><p>Equipo fuera de estándar. Reportado a SSO.</p></div>"""
                    
                    # 🚨 1. REEMPLAZA ESTA URL CON EL ID REAL DE TU FORMULARIO MORADO DE GOOGLE
                    URL_FORM = "https://docs.google.com/forms/d/e/1FAIpQLSfD_Xxxxxxxxxx_Coloca_Aqui_El_ID_Real_De_Tu_Formulario/formResponse"
                    
                    # 🚨 2. MAQUETA DEFINITIVA CON TUS CODES ENTRY REALES
                    datos_envio = {
                        "entry.2064132338": fecha_hora,             # Columna FECHA
                        "entry.1706240243": operador,               # Columna OPERADOR
                        "entry.1741634260": codigo_input,           # Columna TAG
                        "entry.444265005": tool_info['nombre'],     # Columna HERRAMIENTA
                        "entry.1843195861": tool_info['marca'],     # Columna MARCA
                        "entry.254146747": tool_info['serial'],     # Columna SERIAL
                        "entry.2120021665": estado_final,           # Columna ESTADO
                        "entry.2001552097": detalle_final           # Columna DETALLE
                    }
                    
                    try:
                        respuesta = requests.post(URL_FORM, data=datos_envio)
                        if respuesta.status_code in [200, 302]:
                            st.markdown(status_html, unsafe_allow_html=True)
                            st.success("💾 ¡Sincronizado con la base de datos de Google Sheets!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ Error al enviar. Google Forms respondió con código: {respuesta.status_code}")
                    except Exception as e:
                        st.error(f"⚠️ Error de conexión: {e}")
    else:
        st.error(f"❌ Código '{codigo_input}' no encontrado en el Inventario.")

# ==========================================
# 6. LOG BOOK DIGITAL — BITÁCORA EN TIEMPO REAL
# ==========================================
st.write("---")
st.markdown("### 📖 Log Book Digital: Control de Guardia y Turnos")

if not df_historico_real.empty:
    columnas_reales = {c.upper(): c for c in df_historico_real.columns}
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filtro_estado = st.selectbox("📋 Filtrar por Condición:", ["TODOS", "APROBADO", "RECHAZADO"])
    with col_f2:
        filtro_area = st.text_input("🔍 Buscar por Operador o TAG:", placeholder="Ej. CESAR o ELE-TL-001").strip().upper()
    with col_f3:
        st.markdown("<p style='margin-bottom:25px;'></p>", unsafe_allow_html=True)
        csv_data = df_historico_real.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar Log Book (.CSV)",
            data=csv_data,
            file_name=f"LogBook_ManosSeguras_{datetime.date.today()}.csv",
            mime="text/csv"
        )

    df_filtrado = df_historico_real.copy()
    
    if filtro_estado != "TODOS" and "ESTADO" in columnas_reales:
        c_est = columnas_reales["ESTADO"]
        df_filtrado = df_filtrado[df_filtrado[c_est].astype(str).str.upper() == filtro_estado]
        
    if filtro_area:
        c_op = columnas_reales.get("OPERADOR", df_historico_real.columns[2])
        c_tag = columnas_reales.get("TAG", df_historico_real.columns[3])
        df_filtrado = df_filtrado[
            df_filtrado[c_op].astype(str).str.upper().str.contains(filtro_area) | 
            df_filtrado[c_tag].astype(str).str.upper().str.contains(filtro_area)
        ]

    df_log_book = df_filtrado.iloc[::-1]

    if not df_log_book.empty:
        st.dataframe(df_log_book, use_container_width=True, hide_index=True)
else:
    st.info("📌 El Log Book se encuentra vacío.")