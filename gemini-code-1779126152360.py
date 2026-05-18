import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Configuración de página
st.set_page_config(page_title="Advanced AI Geosteering - Colombia VMM", layout="wide")

st.title("🚀 Simulador Pro: Perforación Direccional e IA")
st.markdown("### Contexto: Cuenca Valle Medio del Magdalena (Colombia)")

# --- LÓGICA DE GEOLOGÍA (VMM) ---
# Definimos formaciones: [Nombre, Profundidad Tope (TVD), Color, Hatch (Símbolo), Tipo Roca]
# El buzamiento (dip) es de 3 grados hacia el Este
FORMACIONES = [
    ["Formación Real (Lutitas/Limos)", 0, "#8B4513", "///", "Lutita"],
    ["Formación Colorado (Areniscas)", 3500, "#F4D03F", "..", "Areniscas"],
    ["Formación Mugrosa (Intercalaciones)", 5500, "#58D68D", "--", "Lutita/Arena"],
    ["Target: Fm. Esmeraldas (Arena N1)", 7800, "#D35400", "oo", "Arenisca Porosa"]
]
BUZAMIENTO = 3.0  # Grados de inclinación de la capa

# --- INICIALIZACIÓN ---
if 'md' not in st.session_state:
    st.session_state.md = [7500]           # Empezamos cerca del target
    st.session_state.tvd = [7750]          # TVD inicial
    st.session_state.inc = [85.0]          # Inclinación inicial (casi horizontal)
    st.session_state.vs = [0]              # Vertical Section inicial
    st.session_state.dls = [0]             # Dogleg inicial
    st.session_state.logs = []
    st.session_state.sidetrack = False

def calcular_dls(inc1, inc2, dist):
    return abs(inc2 - inc1) * (100 / dist)

# --- SIDEBAR (CONTROLES) ---
st.sidebar.header("⚙️ Parámetros de Perforación")
inc_objetivo = st.sidebar.slider("Ajustar Inclinación (Survey @100ft)", 70.0, 110.0, float(st.session_state.inc[-1]), 0.5)

if st.sidebar.button("🛠️ Perforar Survey (100 ft)"):
    # Cálculos de trayectoria (Método Tangencial Simple para el ejercicio)
    dist = 100
    nueva_inc = inc_objetivo
    inc_promedio = (st.session_state.inc[-1] + nueva_inc) / 2
    
    # MD y TVD
    nuevo_md = st.session_state.md[-1] + dist
    nuevo_tvd = st.session_state.tvd[-1] + (dist * np.cos(np.radians(90 - inc_promedio)))
    nuevo_vs = st.session_state.vs[-1] + (dist * np.sin(np.radians(90 - inc_promedio)))
    
    # Calcular DLS
    dls_actual = calcular_dls(st.session_state.inc[-1], nueva_inc, dist)
    
    # Guardar datos
    st.session_state.md.append(nuevo_md)
    st.session_state.tvd.append(nuevo_tvd)
    st.session_state.inc.append(nueva_inc)
    st.session_state.vs.append(nuevo_vs)
    st.session_state.dls.append(dls_actual)

if st.sidebar.button("🚨 Realizar Sidetrack"):
    st.session_state.sidetrack = True
    st.session_state.logs.append("Sidetrack iniciado por obstáculo/fuera de ventana.")

# --- CÁLCULOS TÉCNICOS ---
tvd_actual = st.session_state.tvd[-1]
inc_actual = st.session_state.inc[-1]
# Ángulo de ataque = Inclinación del pozo respecto al buzamiento de la formación
aoa = abs(inc_actual - (90 + BUZAMIENTO))

# --- ALERTAS DE IA ---
st.subheader("🤖 Diagnóstico de IA en Tiempo Real")
col_a, col_b, col_c = st.columns(3)

with col_a:
    dls_val = st.session_state.dls[-1]
    if dls_val > 4:
        st.error(f"DLS Crítico: {dls_val:.2f}°/100ft. Riesgo alto de Ojo de Llave (Keyseat) y Pega Mecánica.")
    elif dls_val > 2.5:
        st.warning(f"DLS Alto: {dls_val:.2f}°/100ft. Aumento de torque y arrastre.")
    else:
        st.success(f"DLS Seguro: {dls_val:.2f}°/100ft")

with col_b:
    st.metric("Ángulo de Ataque", f"{aoa:.1f}°")
    if aoa < 2: st.info("Geonavegación Paralela: Óptimo para drenaje.")

with col_c:
    distancia_al_techo = abs(tvd_actual - (7800 + (st.session_state.vs[-1] * np.tan(np.radians(BUZAMIENTO)))))
    if distancia_al_techo < 5:
        st.error("¡ALERTA!: Saliendo de la ventana de interés. Riesgo de pérdida de producción.")

# --- GRÁFICA DE SECCIÓN VERTICAL ---
fig, ax = plt.subplots(figsize=(12, 6))

# Dibujar Formaciones con Buzamiento
dist_max = max(2000, st.session_state.vs[-1] + 500)
x_plot = np.array([0, dist_max])

for i in range(len(FORMACIONES)):
    nombre, tope_inicial, color, trama, roca = FORMACIONES[i]
    # El tope varía con el buzamiento
    y_tope = tope_inicial + (x_plot * np.tan(np.radians(BUZAMIENTO)))
    y_base = 10000 if i == len(FORMACIONES)-1 else FORMACIONES[i+1][1] + (x_plot * np.tan(np.radians(BUZAMIENTO)))
    
    ax.fill_between(x_plot, y_tope, y_base, color=color, alpha=0.3, hatch=trama, label=f"{nombre} ({roca})")

# Dibujar Trayectoria del Pozo
ax.plot(st.session_state.vs, st.session_state.tvd, color='black', linewidth=3, marker='|', label="Trayectoria Pozo")

# Configuración Estética
ax.set_ylim(8100, 7500) # Zoom en la zona de interés
ax.set_xlim(0, dist_max)
ax.set_xlabel("Desplazamiento Vertical / Vertical Section (ft)")
ax.set_ylabel("Profundidad Vertical Verdadera / TVD (ft)")
ax.set_title("Perfil Estratigráfico - Geonavegación VMM")
ax.legend(loc='upper right', fontsize='small')
ax.grid(True, alpha=0.3)

st.pyplot(fig)

# --- TABLA DE DATOS (SURVEY) ---
st.subheader("📋 Registro de Survey (LWD)")
data = {
    "MD (ft)": st.session_state.md,
    "TVD (ft)": st.session_state.tvd,
    "Vertical Section (ft)": st.session_state.vs,
    "Incl (°)": st.session_state.inc,
    "DLS (°/100ft)": st.session_state.dls
}
st.table(data)
