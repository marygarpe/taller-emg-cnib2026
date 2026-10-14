"""
Genera una señal de EMG de superficie sintética para cargarla en Multisim
como fuente PWL (Piecewise Linear) desde archivo.

Modelo: ruido gaussiano filtrado en 20-450 Hz (banda de la sEMG),
modulado por una envolvente de activación con tres contracciones
de fuerza creciente sobre un nivel de reposo.

Salida: archivo de texto con dos columnas (tiempo [s], voltaje [V]).
"""
import numpy as np
from scipy.signal import butter, filtfilt

# ---------------- Parámetros editables ----------------
FS = 5000            # frecuencia de muestreo [Hz]
DURACION = 4.0       # duración total [s]
PICO_RMS = 0.4e-3    # RMS en la contracción más fuerte [V] (~0.4 mV)
REPOSO = 0.05        # nivel de reposo relativo a la contracción máxima
# Contracciones: (inicio [s], fin [s], fuerza relativa 0-1)
CONTRACCIONES = [(0.5, 1.2, 0.4), (1.8, 2.5, 0.7), (3.0, 3.7, 1.0)]
RAMPA = 0.08         # tiempo de subida/bajada de cada contracción [s]
SEMILLA = 7
ARCHIVO = "emg_sintetica_pwl.txt"
# ------------------------------------------------------

rng = np.random.default_rng(SEMILLA)
t = np.arange(0, DURACION, 1 / FS)

# Envolvente de activación con flancos suaves
env = np.full_like(t, REPOSO)
for t0, t1, f in CONTRACCIONES:
    sube = np.clip((t - t0) / RAMPA, 0, 1)
    baja = np.clip((t1 - t) / RAMPA, 0, 1)
    env = np.maximum(env, f * np.minimum(sube, baja))

# Ruido blanco filtrado a la banda de la sEMG
b, a = butter(4, [20, 450], btype="bandpass", fs=FS)
portadora = filtfilt(b, a, rng.standard_normal(t.size))
portadora /= np.std(portadora)

emg = PICO_RMS * env * portadora

# Extremos suaves en 0 V: evita el salto al repetir la forma de onda
# (el último punto coincide con el primero y Multisim no ve una discontinuidad)
TAPER = 0.02  # s
n = int(TAPER * FS)
ventana = 0.5 * (1 - np.cos(np.linspace(0, np.pi, n)))
emg[:n] *= ventana
emg[-n:] *= ventana[::-1]
emg[0] = 0.0
t = np.append(t, DURACION)      # punto final exacto en t = DURACION
emg = np.append(emg, 0.0)

np.savetxt(ARCHIVO, np.column_stack([t, emg]), fmt="%.6e", delimiter=" ")
print(f"{ARCHIVO}: {t.size} puntos, {DURACION} s, "
      f"pico absoluto {np.max(np.abs(emg))*1e3:.2f} mV")
