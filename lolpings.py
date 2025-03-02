# RUEDA DE SMART PINGS DEL LOL PARA ESCRITORIO, VERSIÓN 1.0
import tkinter as tk
from PIL import Image, ImageTk
import os
import math
import sys
import threading
import time
import pygame
import keyboard as kb
import pystray
from pystray import MenuItem as item

# Función para obtener la ruta de recursos, compatible con PyInstaller
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Rutas de recursos (se utilizan en el código, pero luego se usan también en la función resource_path)
icono_ruta = resource_path("recursos/icono.ico")
missing_ruta = resource_path("recursos/missing.png")
onmyway_ruta = resource_path("recursos/onmyway.png")
danger_ruta = resource_path("recursos/danger.png")
help_ruta = resource_path("recursos/help.png")
ping_ruta = resource_path("recursos/ping.png")
sound1_ruta = resource_path("recursos/missing.ogg")
sound2_ruta = resource_path("recursos/onmyway.ogg")
sound3_ruta = resource_path("recursos/danger.ogg")
sound4_ruta = resource_path("recursos/help.ogg")
sound5_ruta = resource_path("recursos/ping.ogg")

# ===================== CONFIGURACIÓN PRINCIPAL =====================
DEBUG_MODE = True                  # Activar mensajes de depuración
TRANSPARENCY_COLOR = "#010101"       # Color clave para transparencia
VOLUME = 0.3                       # Volumen predeterminado (0.0 a 1.0)
TOLERANCE = 13                     # Umbral para considerar un píxel "casi negro" (RGB)
ALPHA_TOLERANCE = 183              # Umbral para forzar píxeles con baja transparencia (valor alfa)
ELIMINAR_PIXELES_NEGROS = True     # Forzar a que los píxeles exactamente negros sean totalmente transparentes
MUTED = False                      # Estado de mute (False por defecto)

# ----------------------- Inicialización básica ---------------------
print("Inicializando aplicación...") if DEBUG_MODE else None

# Configuración de rutas (para recursos) usando resource_path
def configurar_rutas():
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    recursos_path = os.path.join(base_path, "recursos")
    if not os.path.exists(recursos_path):
        print(f"ERROR: No se encontró la carpeta de recursos en {recursos_path}")
        sys.exit(1)
    
    return recursos_path

RUTA_RECURSOS = configurar_rutas()

# ======================== DEFINICIÓN DE PINGS ========================
PINGS_CONFIG = {
    "arriba": {"imagen": "danger.png", "sonido": "danger.ogg"},
    "abajo": {"imagen": "help.png", "sonido": "help.ogg"},
    "izquierda": {"imagen": "missing.png", "sonido": "missing.ogg"},
    "derecha": {"imagen": "onmyway.png", "sonido": "onmyway.ogg"},
    "centro": {"imagen": "ping.png", "sonido": "ping.ogg"},
}

# ==================== SISTEMA DE VISUALIZACIÓN =====================
class PingManager:
    """Manejador principal para la visualización de pings."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.setup_audio()
        
    def setup_audio(self):
        """Configura el sistema de audio."""
        pygame.mixer.init()
        
    def mostrar_ping(self, direccion, x, y):
        """Muestra un ping en las coordenadas especificadas."""
        try:
            ventana = self.crear_ventana_transparente()
            imagen = self.cargar_imagen(direccion)
            self.configurar_ventana(ventana, imagen, direccion, x, y)
            self.iniciar_animacion(ventana)
            self.reproducir_sonido(direccion)
        except Exception as e:
            if DEBUG_MODE:
                print(f"ERROR al mostrar ping: {str(e)}")
    
    def crear_ventana_transparente(self):
        """Crea una ventana transparente para el ping."""
        ventana = tk.Toplevel()
        ventana.overrideredirect(True)
        ventana.attributes("-topmost", True)
        ventana.config(bg=TRANSPARENCY_COLOR)
        ventana.attributes("-transparentcolor", TRANSPARENCY_COLOR)
        return ventana
    
    def cargar_imagen(self, direccion):
        """Carga y procesa la imagen del ping, forzando píxeles oscuros o con baja transparencia a ser totalmente transparentes."""
        archivo = PINGS_CONFIG[direccion]["imagen"]
        ruta = os.path.join(RUTA_RECURSOS, archivo)
        with Image.open(ruta) as img:
            img = img.convert("RGBA")
            tamaño = (50, 50) if direccion == "centro" else (100, 100)
            img = img.resize(tamaño, Image.LANCZOS)
            # Procesar cada píxel:
            datos = img.getdata()
            nueva_data = []
            for r, g, b, a in datos:
                if ELIMINAR_PIXELES_NEGROS and (r, g, b) == (0, 0, 0):
                    nueva_data.append((r, g, b, 0))
                elif r <= TOLERANCE and g <= TOLERANCE and b <= TOLERANCE:
                    nueva_data.append((r, g, b, 0))
                elif a < ALPHA_TOLERANCE:
                    nueva_data.append((r, g, b, 0))
                else:
                    nueva_data.append((r, g, b, a))
            img.putdata(nueva_data)
            return img
    
    def configurar_ventana(self, ventana, imagen, direccion, x, y):
        """Posiciona y muestra la imagen en la ventana."""
        foto = ImageTk.PhotoImage(imagen)
        label = tk.Label(ventana, image=foto, bg=TRANSPARENCY_COLOR)
        label.image = foto
        label.pack()
        if direccion == "centro":
            ventana.geometry(f"+{x-25}+{y-50}")
        else:
            ventana.geometry(f"+{x-50}+{y-50}")
    
    def iniciar_animacion(self, ventana):
        """Controla la animación de aparición y desvanecimiento."""
        def fade(alpha, step):
            if ventana.winfo_exists():
                ventana.attributes("-alpha", alpha)
                if step < 20:    # Fade in (400ms)
                    ventana.after(20, fade, min(alpha + 0.05, 1.0), step + 1)
                elif step == 20:   # Tiempo visible (1000ms)
                    ventana.after(1000, fade, alpha, step + 1)
                elif alpha > 0.0:  # Fade out (400ms)
                    ventana.after(20, fade, max(alpha - 0.05, 0.0), step + 1)
                else:
                    ventana.destroy()
        fade(0.0, 0)
    
    def reproducir_sonido(self, direccion):
        """Reproduce el efecto de sonido asociado."""
        def play():
            try:
                archivo = PINGS_CONFIG[direccion]["sonido"]
                ruta = os.path.join(RUTA_RECURSOS, archivo)
                sound = pygame.mixer.Sound(ruta)
                current_volume = 0 if MUTED else VOLUME
                sound.set_volume(current_volume)
                sound.play()
            except Exception as e:
                if DEBUG_MODE:
                    print(f"ERROR de audio: {str(e)}")
        threading.Thread(target=play, daemon=True).start()

# ==================== SISTEMA DE CAPTURA =====================
class CaptureManager:
    """Manejador de la captura de input del usuario."""
    
    def __init__(self, ping_manager):
        self.ping_manager = ping_manager
        self.pos_inicial = None
        self.captura_activa = False
        
    def iniciar_captura(self, event):
        """Inicia el seguimiento del movimiento del mouse."""
        self.pos_inicial = (event.x_root, event.y_root)
        self.captura_activa = True
        if DEBUG_MODE:
            print(f"Captura iniciada en: {self.pos_inicial}")
    
    def finalizar_captura(self, event):
        """Procesa el movimiento y muestra el ping."""
        if self.captura_activa:
            pos_final = (event.x_root, event.y_root)
            dx, dy = pos_final[0] - self.pos_inicial[0], pos_final[1] - self.pos_inicial[1]
            direccion = self.calcular_direccion(dx, dy)
            if DEBUG_MODE:
                print(f"Dirección detectada: {direccion}")
            self.ping_manager.root.after(0, self.ping_manager.mostrar_ping, direccion, *self.pos_inicial)
            self.pos_inicial = None
            self.captura_activa = False
    
    def calcular_direccion(self, dx, dy):
        """Determina la dirección basada en el movimiento del mouse."""
        if dx == 0 and dy == 0:
            return "centro"
        angulo = math.degrees(math.atan2(dy, dx)) % 360
        if 315 <= angulo or angulo < 45:
            return "derecha"
        elif 45 <= angulo < 135:
            return "abajo"
        elif 135 <= angulo < 225:
            return "izquierda"
        else:
            return "arriba"

# ==================== INTERFAZ DE CAPTURA =====================
def crear_overlay(capture_manager):
    """Crea la ventana transparente para capturar eventos."""
    ventana = tk.Toplevel()
    ventana.overrideredirect(True)
    ventana.geometry(f"{ventana.winfo_screenwidth()}x{ventana.winfo_screenheight()}+0+0")
    ventana.attributes("-topmost", True)
    ventana.config(bg="black")
    ventana.attributes("-alpha", 0.01)
    ventana.bind("<ButtonPress-1>", capture_manager.iniciar_captura)
    ventana.bind("<ButtonRelease-1>", capture_manager.finalizar_captura)
    ventana.bind("<Motion>", lambda e: None)
    ventana.focus_force()
    ventana.grab_set()
    return ventana

# ==================== VENTANA DE CONTROL DE VOLUMEN =====================
def open_volume_control_window(root):
    """Crea una ventana para controlar el volumen y mute."""
    vol_window = tk.Toplevel(root)
    vol_window.title("Volumen control")
    vol_window.geometry("300x100")
    vol_scale = tk.Scale(vol_window, from_=0, to=100, orient=tk.HORIZONTAL, label="Volumen")
    vol_scale.set(VOLUME * 100)
    vol_scale.pack(fill=tk.X, padx=10, pady=5)
    mute_var = tk.BooleanVar(value=MUTED)
    def update_volume(val):
        global VOLUME, MUTED
        VOLUME = float(val) / 100.0
        if MUTED:
            MUTED = False
            mute_var.set(False)
    vol_scale.config(command=update_volume)
    mute_check = tk.Checkbutton(vol_window, text="Mute", variable=mute_var, command=lambda: toggle_mute(mute_var))
    mute_check.pack(pady=5)
    return vol_window

def toggle_mute(mute_var):
    """Alterna el estado de mute."""
    global MUTED
    MUTED = mute_var.get()

# ==================== SISTEMA DE BARRA DE TAREA (TRAY ICON) =====================
def create_tray_icon(root):
    """Crea el icono de la bandeja del sistema con menú para controlar volumen y salir."""
    # Usamos resource_path para obtener el ícono empaquetado
    icon_path = resource_path("recursos/icono.ico")
    tray_image = Image.open(icon_path)
    menu = (item('Volumen control', lambda: root.after(0, open_volume_control_window, root)),
            item('Exit', lambda: exit_app(root)))
    tray_icon = pystray.Icon("SmartPings", tray_image, "Smart Pings", menu)
    tray_icon.run_detached()
    return tray_icon

def exit_app(root):
    """Cierra la aplicación."""
    root.quit()

# ==================== CONTROL PRINCIPAL =====================
def main():
    global MUTED  # Asegurarse de que MUTED esté definido globalmente
    MUTED = False
    ping_manager = PingManager()
    capture_manager = CaptureManager(ping_manager)
    tray_icon = create_tray_icon(ping_manager.root)
    
    def gestionar_tecla_alt():
        """Controla la activación/desactivación del overlay."""
        ventana = None
        while True:
            if kb.is_pressed('alt'):
                if not ventana:
                    ventana = crear_overlay(capture_manager)
                    if DEBUG_MODE:
                        print("Overlay activado")
            else:
                if ventana:
                    try:
                        ventana.destroy()
                    except Exception as e:
                        if DEBUG_MODE:
                            print(f"Error al cerrar overlay: {str(e)}")
                    ventana = None
                    if DEBUG_MODE:
                        print("Overlay desactivado")
            time.sleep(0.1)
    
    try:
        threading.Thread(target=gestionar_tecla_alt, daemon=True).start()
        ping_manager.root.mainloop()
    except Exception as e:
        print(f"ERROR crítico: {str(e)}")
    finally:
        tray_icon.stop()
        pygame.mixer.quit()
        ping_manager.root.quit()

if __name__ == "__main__":
    main()


