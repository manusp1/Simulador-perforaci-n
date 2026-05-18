import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Configuración inicial de la página web
st.set_page_config(page_title="AI Geosteering Simulator", layout="wide")

st.title("🎯 Simulador Inteligente de Geonavegación (Geosteering)")
st.markdown("### Proyecto Final - Perforación Direccional")
st.write("Monitorea los Rayos Gamma (LWD) en tiempo real y sigue los consejos de la IA.")

# --- INICIALIZACIÓN DE VARIABLES ---
if 'md' not in st.session_state:
    st.session_state.md = [6000]          
    st.session_state.tvd = [5015]         
    st.session_state.gr = [45]            
    st.session_state.angulo = 0.0         
    st.session_state.score = 100          
    st.session_state.logs = ["Pozo iniciado en el centro de la formación productiva."]

# --- GEOLOGÍA DEL YACIMIENTO ---
def obtener_limites_yacimiento(md_actual):
    buzamiento = np.tan(np.radians(1.5))
    distancia = md_actual - 6000
    techo = 5000 + (distancia * buzamiento)
    base = techo + 30  
    return techo, base

# --- INTERFAZ (PANEL LATERAL) ---
st.sidebar.header("🕹️ Controles del Taladro")
ajuste_angulo = st.sidebar.slider("Ajustar ángulo de navegación (°)", -5.0, 5.0, float(st.session_state.angulo), 0.5)
st.session_state.angulo = ajuste_angulo

if st.sidebar.button("🚀 Perforar Siguiente Intervalo (+50 ft)"):
    nuevo_md = st.session_state.md[-1] + 50
    cambio_tvd = -50 * np.sin(np.radians(st.session_state.angulo))
    nuevo_tvd = st.session_state.tvd[-1] + cambio_tvd
    techo, base = obtener_limites_yacimiento(nuevo_md)
    
    if techo <= nuevo_tvd <= base:
        nuevo_gr = int(np.random.normal(45, 5)) 
        status = "✅ Dentro del yacimiento (Arena limpia)"
    else:
        nuevo_gr = int(np.random.normal(130, 8)) 
        status = "🚨 ¡FUERA DEL TARGET! Perforando Lutita"
        st.session_state.score -= 15 
        
    st.session_state.md.append(nuevo_md)
    st.session_state.tvd.append(nuevo_tvd)
    st.session_state.gr.append(nuevo_gr)
    st.session_state.logs.append(f"MD: {nuevo_md}ft | {status} | GR: {nuevo_gr} API")

if st.sidebar.button("🔄 Reiniciar Simulación"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- CÁLCULOS DE IA ---
md_actual = st.session_state.md[-1]
tvd_actual = st.session_state.tvd[-1]
techo_actual, base_actual = obtener_limites_yacimiento(md_actual)
tvd_predicho = tvd_actual + (-100 * np.sin(np.radians(st.session_state.angulo)))
techo_futuro, base_futuro = obtener_limites_yacimiento(md_actual + 100)

ai_consejo = "🟢 Trayectoria estable. Continúa con el rumbo actual."
ai_alerta = "Normal"

if tvd_predicho < techo_futuro + 5:
    ai_consejo = "⚠️ ALERTA DE IA: Riesgo de salir por el TECHO. Sugerencia: Bajar ángulo (DROP)."
    ai_alerta = "Advertencia"
elif tvd_predicho > base_futuro - 5:
    ai_consejo = "⚠️ ALERTA DE IA: Riesgo de salir por la BASE. Sugerencia: Subir ángulo (BUILD)."
    ai_alerta = "Advertencia"

# --- GRÁFICOS ---
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Perfil Estructural del Pozo")
    md_grafico = np.linspace(6000, max(8000, md_actual + 500), 100)
    techos_grafico = 5000 + ((md_grafico - 6000) * np.tan(np.radians(1.5)))
    bases_grafico = techos_grafico + 30
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(md_grafico, 4950, techos_grafico, color='#b0c4de', label='Lutita Superior')
    ax.fill_between(md_grafico, techos_grafico, bases_grafico, color='#fff8dc', label='Arena (Target)')
    ax.fill_between(md_grafico, bases_grafico, 5100, color='#d2b48c', label='Lutita Inferior')
    ax.plot(st.session_state.md, st.session_state.tvd, color='black', linewidth=3, marker='o', label='Pozo Real')
    ax.set_ylim(5080, 4970)
    ax.set_xlim(6000, max(7000, md_actual + 100))
    ax.legend(loc='lower left')
    st.pyplot(fig)

with col2:
    st.subheader("Datos LWD")
    st.metric(label="MD Actual", value=f"{md_actual} ft")
    if st.session_state.gr[-1] < 75:
        st.success(f"GR: {st.session_state.gr[-1]} API")
    else:
        st.error(f"GR: {st.session_state.gr[-1]} API")
    st.metric(label="Eficiencia", value=f"{st.session_state.score} pts")

st.subheader("🤖 Copiloto de IA")
if ai_alerta == "Normal": st.info(ai_consejo)
elif ai_alerta == "Advertencia": st.warning(ai_consejo)
else: st.error(ai_consejo)
