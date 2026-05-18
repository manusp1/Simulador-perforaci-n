import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Configuración inicial de la página web
st.set_page_config(page_title="AI Geosteering Simulator", layout="wide")

st.title("🎯 Simulador Inteligente de Geonavegación (Geosteering)")
st.markdown("### Proyecto Final - Perforación Direccional")
st.write("Monitorea los Rayos Gamma (LWD) en tiempo real y sigue los consejos del Asistente de IA para mantener el pozo dentro del yacimiento.")

# --- INICIALIZACIÓN DE VARIABLES (ESTADO DE LA SESIÓN) ---
if 'md' not in st.session_state:
    st.session_state.md = [6000]          # Profundidad Medida inicial (ft)
    st.session_state.tvd = [5015]         # Profundidad Verdadera Vertical inicial (ft)
    st.session_state.gr = [45]            # Rayos Gamma iniciales (API)
    st.session_state.angulo = 0.0         # Ángulo respecto a la horizontal (0 = plano)
    st.session_state.score = 100          # Puntaje de eficiencia
    st.session_state.historial_gr = [45]
    st.session_state.logs = ["Pozo iniciado en el centro de la formación productiva."]

# --- GEOLOGÍA DEL YACIMIENTO (El target tiene un buzamiento/caída de 1.5 grados) ---
def obtener_limites_yacimiento(md_actual):
    # El yacimiento cae gradualmente a medida que avanzamos en MD
    buzamiento = np.tan(np.radians(1.5))
    distancia = md_actual - 6000
    techo = 5000 + (distancia * buzamiento)
    base = techo + 30  # El yacimiento tiene 30 pies de espesor
    return techo, base

# --- INTERFAZ DE USUARIO (PANEL LATERAL DE CONTROL) ---
st.sidebar.header("🕹️ Controles del Taladro")

# Control para cambiar la dirección de la broca
ajuste_angulo = st.sidebar.slider("Ajustar ángulo de navegación (°)", -5.0, 5.0, float(st.session_state.angulo), 0.5)
st.session_state.angulo = ajuste_angulo

# Botón para perforar el siguiente tramo
if st.sidebar.button("🚀 Perforar Siguiente Intervalo (+50 ft)"):
    # 1. Calcular nueva trayectoria
    nuevo_md = st.session_state.md[-1] + 50
    
    # Física simple: cambio en TVD basado en el ángulo respecto a la horizontal
    # (Si el ángulo es positivo va hacia arriba, disminuye TVD)
    cambio_tvd = -50 * np.sin(np.radians(st.session_state.angulo))
    nuevo_tvd = st.session_state.tvd[-1] + cambio_tvd
    
    # 2. Calcular límites geológicos en este nuevo punto
    techo, base = obtener_limites_yacimiento(nuevo_md)
    
    # 3. Simular lectura de Rayos Gamma (LWD)
    # Arena (Yacimiento) = Bajos Rayos Gamma (30-60 API)
    # Lutita (Fuera) = Altos Rayos Gamma (110-150 API)
    if techo <= nuevo_tvd <= base:
        nuevo_gr = int(np.random.normal(45, 5)) # Dentro de la arena
        status = "✅ Dentro del yacimiento (Arena limpia)"
    else:
        nuevo_gr = int(np.random.normal(130, 8)) # Fuera, en la lutita
        status = "🚨 ¡FUERA DEL TARGET! Perforando Lutita"
        st.session_state.score -= 15 # Penalización
        
    # Actualizar estados
    st.session_state.md.append(nuevo_md)
    st.session_state.tvd.append(nuevo_tvd)
    st.session_state.gr.append(nuevo_gr)
    st.session_state.logs.append(f"MD: {nuevo_md}ft | {status} | GR: {nuevo_gr} API")

# Botón de reinicio
if st.sidebar.button("🔄 Reiniciar Simulación"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- CÁLCULOS DEL ASISTENTE DE IA ---
md_actual = st.session_state.md[-1]
tvd_actual = st.session_state.tvd[-1]
techo_actual, base_actual = obtener_limites_yacimiento(md_actual)

# Predictor de IA: Calcula qué pasará en los próximos 100 pies si no cambia el rumbo
tvd_predicho = tvd_actual + (-100 * np.sin(np.radians(st.session_state.angulo)))
techo_futuro, base_futuro = obtener_limites_yacimiento(md_actual + 100)

ai_consejo = "🟢 Trayectoria estable. Continúa con el rumbo actual."
ai_alerta = "Normal"

if tvd_predicho < techo_futuro + 5:
    ai_consejo = "⚠️ ALERTA DE IA: Riesgo de salir por el TECHO de la formación en los próximos 100ft. Se sugiere aplicar DROP (bajar ángulo a -2.0°)."
    ai_alerta = "Advertencia"
elif tvd_predicho > base_futuro - 5:
    ai_consejo = "⚠️ ALERTA DE IA: Riesgo de salir por la BASE de la formación en los próximos 100ft. Se sugiere aplicar BUILD (subir ángulo a +2.0°)."
    ai_alerta = "Advertencia"

if tvd_actual < techo_actual or tvd_actual > base_actual:
    ai_consejo = "🚨 CRÍTICO: ¡Estás fuera de la zona de pago! Corrige el rumbo inmediatamente hacia el centro del canal."
    ai_alerta = "Crítico"

# --- VISUALIZACIÓN DE LOS GRÁFICOS ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Visualización del Perfil del Pozo (Sección Estructural)")
    
    # Generar datos para dibujar las capas geológicas
    md_grafico = np.linspace(6000, max(8000, md_actual + 500), 100)
    techos_grafico = 5000 + ((md_grafico - 6000) * np.tan(np.radians(1.5)))
    bases_grafico = techos_grafico + 30
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Dibujar Capas
    ax.fill_between(md_grafico, 4950, techos_grafico, color='#b0c4de', label='Lutita Superior (Techo)')
    ax.fill_between(md_grafico, techos_grafico, bases_grafico, color='#fff8dc', label='Arena Yacimiento (Target)')
    ax.fill_between(md_grafico, bases_grafico, 5100, color='#d2b48c', label='Lutita Inferior (Base)')
    
    # Dibujar la trayectoria del pozo perforado
    ax.plot(st.session_state.md, st.session_state.tvd, color='black', linewidth=3, marker='o', label='Pozo Real')
    
    # Configuración del gráfico (Invertir eje Y porque la profundidad aumenta hacia abajo)
    ax.set_ylim(5080, 4970)
    ax.set_xlim(6000, max(7000, md_actual + 100))
    ax.set_xlabel("Profundidad Medida - MD (ft)")
    ax.set_ylabel("Profundidad Vertical - TVD (ft)")
    ax.legend(loc='lower left')
    ax.grid(True, linestyle='--', alpha=0.5)
    
    st.pyplot(fig)

with col2:
    st.subheader("Indicadores en Tiempo Real")
    st.metric(label="Profundidad Actual (MD)", value=f"{md_actual} ft")
    
    # Mostrar indicador de Rayos Gamma cromático
    if st.session_state.gr[-1] < 75:
        st.success(f"⚡ Rayos Gamma: {st.session_state.gr[-1]} API (¡Buena Arena!)")
    else:
        st.error(f"⚡ Rayos Gamma: {st.session_state.gr[-1]} API (Lutita/No comercial)")
        
    st.metric(label="Puntaje de Eficiencia Comercial", value=f"{st.session_state.score} pts")

---
# --- PANEL DEL ASISTENTE DE IA ---
st.subheader("🤖 Copiloto de Geonavegación Inteligente (Predictive AI)")
if ai_alerta == "Normal":
    st.info(ai_consejo)
elif ai_alerta == "Advertencia":
    st.warning(ai_consejo)
else:
    st.error(ai_consejo)

# Historial de operaciones
with st.expander("📋 Ver registro detallado de perforación"):
    for log in reversed(st.session_state.logs):
        st.write(log)