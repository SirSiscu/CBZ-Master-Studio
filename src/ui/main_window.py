import webbrowser
import tkinter as tk

from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import queue
import logging
from pathlib import Path
import time
import os
import subprocess
import re

from utils.helpers import setup_logging, get_resource_path
import core.logic_compress as logic_compress
import core.logic_organize as logic_organize
import core.logic_archive as logic_archive
import utils.helpers as utils

# --- ASSETS & CONFIG ---

TRANSLATIONS = {
    "ca": {
        "title": "CBZ Master Studio",
        "mode_group": "Què vols fer?",
        "mode1": "Crear CBZ des de carpetes d'imatges",
        "mode2": "Organitzar imatges soltes per sèrie/capítol",
        "mode3": "Convertir arxius (ZIP/RAR) a CBZ/CBR",
        "path_group": "Configuració de Rutes",
        "source": "Carpeta Origen:",
        "dest": "Carpeta Destí (Opcional per Mode 2):",
        "browse": "Navegar...",
        "opts_group": "Opcions Avançades",
        "dry_run": "DRY-RUN (Simulació - No modifica res)",
        "merge_chapters": "Fusionar Capítols (Ex: 'Serie CH1', 'Serie CH2' -> 'Serie')",
        
        # Cleanup Options
        "cleanup_group": "Gestió de Fitxers Originals",
        "clean_folder": "Moure a una carpeta separada per revisar-los (Recomanat)",
        "clean_recycle": "Enviar a la Paperera de Reciclatge",
        "clean_none": "No fer res (Mantenir els originals on són)",

        "exec_btn": "EXECUTAR PROCÉS",
        "exit_btn": "Sortir",
        "status_ready": "Preparat.",
        "log_group": "Registre d'Activitat",
        "success": "Finalitzat correctament.",
        "error": "Error durant l'execució.",
        "err_source": "Selecciona una carpeta d'origen.",
        "mode1_desc": "Converteix cada subcarpeta en un fitxer .cbz independent.",
        "mode2_desc": "Mou fitxers solts a carpetes basant-se en el nom.",
        "mode3_desc": "Renombra ZIPs a CBZ (si tenen imatges) i RARs a CBR.",
        
        # Summary & Actions
        "sum_title": "Resum del Procés",
        "sum_total_time": "Temps Total:",
        "sum_processed": "Elements Processats:",
        "sum_errors": "Errors/Ignorats:",
        "sum_orig_size": "Mida Original:",
        "sum_final_size": "Mida Final:",
        "sum_saved": "Estalvi:",
        "sum_view_log": "Veure Registre d'Errors",
        "sum_close": "Tancar",
        "log_filter_title": "Registre d'Errors / Ignorats",
        
        "act_open_orig": "Obrir carpeta d'originals",
        "act_recycle_orig": "Enviar originals a la paperera",
        "act_open_dest": "Obrir carpeta de destí",
        "confirm_recycle_title": "Confirmar Esborrat",
        "confirm_recycle_msg": "Segur que vols enviar TOTS els fitxers de la carpeta d'originals a la paperera?\nAquesta acció esborrarà la carpeta '{}'.",
        "recycled_ok": "Originals enviats a la paperera.",
        
        # Dry Run Spec
        "sum_processed_dry": "Elements que es processarien:",
        "sum_errors_dry": "Errors/Ignorats previstos:",
        "sum_orig_size_dry": "Mida Original:",
        "sum_final_size_dry": "Mida Final Estimada:",
        "sum_saved_dry": "Estalvi Estimat:",
        
        # Credits
        "credits_madeby": "Fet per SirSiscu",
        "credits_github": "GitHub",
        "credits_bmac": "Buy Me a Coffee",
        
        "btn_analyze": "ANALITZAR",
        "btn_help": "Ajuda",
        "btn_sel_all": "Seleccionar tot",
        "btn_sel_none": "Seleccionar res",
        "results_group": "Resultats de l'Anàlisi",
        "col_name": "Nom de l'element",
        "col_size": "Mida Orig.",
        "col_status": "Estat/Info",
        "stats_sel": "{} items seleccionats ({})",
        
        "help_title": "Ajuda — Com funciona l’aplicació",
        "help_text": """# Passos bàsics

* Selecciona el **mode d’operació** que vols utilitzar.
* Tria la **carpeta d’origen** amb els arxius o carpetes.
* Configura **què ha de passar** amb els fitxers originals.
* Fes clic a **Analitzar** per veure què farà el programa.
* Revisa el resum i **Executa** els canvis quan estiguis segur.

# Sobre l’anàlisi

* L’anàlisi **no modifica** cap fitxer.
* Serveix per revisar què es crearà, què es mourà i l’espai que s’estalviarà.

# Sobre els fitxers originals

* Pots **mantenir-los** al lloc original.
* Pots **moure’ls** a una carpeta separada per revisar-los.
* Pots **enviar-los a la paperera** després del procés.

# Registre i errors

* Qualsevol incidència queda registrada al **registre d’activitat**.
* Els errors **no aturen** la resta del procés.

# Informació del projecte

**CBZ Master Studio**
Fet per SirSiscu

[GitHub](https://github.com/SirSiscu)
[Buy Me a Coffee](https://buymeacoffee.com/francescsala)""",
        "msg_need_analysis": "Primer has de fer una ANÀLISI.",
        "msg_select_items": "Selecciona almenys un element per processar.",
        
        # STATUS
        "status_size_est": "Llest - Mida de {} a ~{} ({}%)",
        "status_img_count": "Llest - {} imatges",
        "status_convert": "Llest - Es convertirà a {}",
        "status_invalid": "Ignorat: {}",
    },
    "es": {
        "title": "CBZ Master Studio",
        "mode_group": "¿Qué quieres hacer?",
        "mode1": "Crear CBZ desde carpetas de imágenes",
        "mode2": "Organizar imágenes sueltas por serie/capítulo",
        "mode3": "Convertir archivos (ZIP/RAR) a CBZ/CBR",
        "path_group": "Configuración de Rutas",
        "source": "Carpeta Origen:",
        "dest": "Carpeta Destino (Opcional para Modo 2):",
        "browse": "Navegar...",
        "opts_group": "Opciones Avanzadas",
        "dry_run": "DRY-RUN (Simulación - No modifica nada)",
        "merge_chapters": "Fusionar Capítulos (Ej: 'Serie CH1' -> 'Serie')",
        
        "cleanup_group": "Gestión de Archivos Originales",
        "clean_folder": "Mover a carpeta separada para revisión (Recomendado)",
        "clean_recycle": "Enviar a Papelera de Reciclaje",
        "clean_none": "No hacer nada (Mantener originales)",

        "exec_btn": "EJECUTAR",
        "exit_btn": "Salir",
        "status_ready": "Listo.",
        "log_group": "Registro de Actividad",
        "success": "Finalizado correctamente.",
        "error": "Error durante la ejecución.",
        "err_source": "Selecciona una carpeta de origen.",
        "mode1_desc": "Convierte cada subcarpeta en un archivo .cbz independiente.",
        "mode2_desc": "Mueve archivos sueltos a carpetas basándose en el nombre.",
        "mode3_desc": "Renombra ZIPs a CBZ (si tienen imágenes) y RARs a CBR.",
        
        "sum_title": "Resumen del Proceso",
        "sum_total_time": "Tiempo Total:",
        "sum_processed": "Elementos Procesados:",
        "sum_errors": "Errores/Ignorados:",
        "sum_orig_size": "Tamaño Original:",
        "sum_final_size": "Tamaño Final:",
        "sum_saved": "Ahorro:",
        "sum_view_log": "Ver Registro de Errores",
        "sum_close": "Cerrar",
        "log_filter_title": "Registro de Errores / Ignorados",
        
        "act_open_orig": "Abrir carpeta de originales",
        "act_recycle_orig": "Enviar originales a papelera",
        "act_open_dest": "Abrir carpeta de destino",
        "confirm_recycle_title": "Confirmar Borrado",
        "confirm_recycle_msg": "¿Seguro que quieres enviar TODOS los archivos de la carpeta de originales a la papelera?\nEsta acción borrará la carpeta '{}'.",
        "recycled_ok": "Originales enviados a la papelera.",
        
        # Dry Run Spec (Removed logic but kept keys for legacy safety or Summary adaptation?)
        # Let's keep them if we reuse logic, BUT we don't have DRY RUN anymore.
        # We can reuse them for "Analysis Report"? Probably not needed in same way.
        
        "credits_madeby": "Hecho por SirSiscu",
        "credits_github": "GitHub",
        "credits_bmac": "Buy Me a Coffee",
        
        "btn_analyze": "ANALIZAR",
        "btn_help": "Ayuda",
        "btn_sel_all": "Seleccionar todo",
        "btn_sel_none": "Seleccionar nada",
        "results_group": "Resultados del Análisis",
        "col_name": "Nombre Item",
        "col_size": "Tamaño Orig.",
        "col_status": "Info/Estado",
        "stats_sel": "{} items seleccionados ({})",
        "help_title": "Cómo funciona",
        "help_text": """# Pasos básicos

* Selecciona el **modo de operación** que quieras usar.
* Elige la **carpeta de origen** con los archivos o carpetas.
* Configura **qué hacer** con los archivos originales.
* Haz clic en **Analizar** para ver qué hará el programa.
* Revisa el resumen y **Ejecuta** los cambios cuando estés seguro.

# Sobre el análisis

* El análisis **no modifica** ningún archivo.
* Sirve para revisar qué se creará, moverá y el espacio ahorrado.

# Sobre los archivos originales

* Puedes **mantenerlos** en su sitio original.
* Puedes **moverlos** a una carpeta separada para revisarlos.
* Puedes **enviarlos a la papelera** tras el proceso.

# Registro y errores

* Cualquier incidencia queda en el **registro de actividad**.
* Los errores **no detienen** el resto del proceso.

# Información del proyecto

**CBZ Master Studio**
Hecho por SirSiscu

[GitHub](https://github.com/SirSiscu)
[Buy Me a Coffee](https://buymeacoffee.com/francescsala)""",

        # STATUS
        "status_size_est": "Listo - Tamaño de {} a ~{} ({}%)",
        "status_img_count": "Listo - {} imágenes",
        "status_convert": "Listo - Se convertirá a {}",
        "status_invalid": "Ignorado: {}",
    },
    "en": {
        "title": "CBZ Master Studio",
        "mode_group": "What do you want to do?",
        "mode1": "Create CBZ from image folders",
        "mode2": "Organize loose images by series/chapter",
        "mode3": "Convert archives (ZIP/RAR) to CBZ/CBR",
        "path_group": "Path Configuration",
        "source": "Source Folder:",
        "dest": "Destination Folder (Optional for Mode 2):",
        "browse": "Browse...",
        "opts_group": "Advanced Options",
        "dry_run": "DRY-RUN (Simulation - No changes)",
        "merge_chapters": "Merge Chapters (e.g. 'Series CH1' -> 'Series')",
        
        "cleanup_group": "Original Files Management",
        "clean_folder": "Move to separate review folder (Recommended)",
        "clean_recycle": "Send to Recycle Bin",
        "clean_none": "Do nothing (Keep originals)",

        "exec_btn": "EXECUTE",
        "btn_analyze": "ANALYZE",
        "btn_help": "Help",
        "btn_sel_all": "Select All",
        "btn_sel_none": "Select None",
        "results_group": "Analysis Results",
        "col_name": "Item Name",
        "col_size": "Original Size",
        "col_status": "Status/Info",
        "stats_sel": "{} items selected ({})",
        
        "credits_madeby": "Made by SirSiscu",
        "credits_github": "GitHub",
        "credits_bmac": "Buy Me a Coffee",
        "sum_close": "Exit",
        
        "sum_title": "Process Summary",
        "sum_total_time": "Total Time:",
        "sum_processed": "Processed Items:",
        "sum_errors": "Errors/Ignored:",
        "sum_orig_size": "Original Size:",
        "sum_final_size": "Final Size:",
        "sum_saved": "Savings:",
        "sum_view_log": "View Error Log",
        
        "act_open_orig": "Open originals folder",
        "act_recycle_orig": "Send originals to recycle bin",
        "act_open_dest": "Open destination folder",
        "confirm_recycle_title": "Confirm Deletion",
        "confirm_recycle_msg": "Are you sure you want to send ALL files in the originals folder to the recycle bin?\nThis will delete the folder '{}'.",
        "recycled_ok": "Originals sent to the recycle bin.",
        
        # Help Text
        "help_title": "Help — How it Works",
        "help_text": """# Basic Steps

* Select the **mode** you want to use.
* Choose the **source folder** containing files or folders.
* Configure **what happens** to original files.
* Click **Analyze** to see what will happen.
* Review the summary and **Execute** when ready.

# About Analysis

* The analysis **does not modify** any files.
* It shows what will be created, moved, and space saved.

# About Original Files

* You can **keep** them in place.
* You can **move** them to a separate folder (recommended).
* You can **recycle** them after processing.

# Log & Errors

* Any issues are recorded in the **Activity Log**.
* Errors **do not stop** the rest of the process.

# Project Info

**CBZ Master Studio**
Made by SirSiscu

[GitHub](https://github.com/SirSiscu)
[Buy Me a Coffee](https://buymeacoffee.com/francescsala)""",
        "msg_need_analysis": "You must perform an ANALYSIS first.",
        "msg_select_items": "Select at least one item to process.",

        # STATUS MESSAGES
        "status_size_est": "Ready - Size from {} to ~{} ({}%)",
        "status_img_count": "Ready - {} images",
        "status_convert": "Ready - Will convert to {}",
        "status_invalid": "Skipped: {}",
    }
}

THEMES = {
    "light": {
        "bg": "#f0f2f5",
        "fg": "#1e293b",
        "frame_bg": "#ffffff",
        "input_bg": "#ffffff",
        "input_fg": "#334155",
        "highlight": "#2563eb",
        "btn_fg": "#ffffff",
        "success": "#16a34a",
        "disabled_bg": "#cbd5e1", # Explicit disabled grey
        "disabled_fg": "#94a3b8"
    },
    "dark": {
        "bg": "#0f172a",
        "fg": "#e2e8f0",
        "frame_bg": "#1e293b",
        "input_bg": "#334155",
        "input_fg": "#f1f5f9",
        "highlight": "#3b82f6",
        "btn_fg": "#ffffff",
        "success": "#22c55e",
        "disabled_bg": "#334155", # Darker grey
        "disabled_fg": "#64748b"
    }
}

def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"

class TextHandler(logging.Handler):
    def __init__(self, text_queue):
        super().__init__()
        self.text_queue = text_queue

    def emit(self, record):
        msg = self.format(record)
        self.text_queue.put(msg)

class ToolTip(object):
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 300   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffe0", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)
        self.hidetip = self.hide # alias

    def hide(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()

class CbzApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CBZ Master Studio")
        self.root.geometry("900x800")
        
        # Set window icon if available
        icon_path = get_resource_path("assets/icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except:
                pass
        
        # State Variables
        self.lang_var = tk.StringVar(value="en")
        self.theme_var = tk.StringVar(value="light")
        
        self.source_path = tk.StringVar()
        self.dest_path = tk.StringVar()
        
        self.mode_var = tk.StringVar(value="mode1")
        self.merge_chapters_var = tk.BooleanVar(value=False)
        
        self.analysis_results = [] # Store items from analysis
    
        # Cleanup Mode: 'folder', 'recycle', 'none'
        self.cleanup_mode_var = tk.StringVar(value="folder")
        
        self.progress_var = tk.DoubleVar(value=0)
        self.status_var = tk.StringVar(value="Ready")
        self.desc_var = tk.StringVar()
        
        # Logging
        self.log_queue = queue.Queue()
        self.text_handler = TextHandler(self.log_queue)
        self.logger = setup_logging(self.text_handler)
        
        self.error_logs = [] 
        
        self.widgets = {} 
        
        self.setup_ui()
        self.apply_theme()
        self.apply_language()
        self.check_log_queue()

    def tr(self, key):
        """Translates a key."""
        lang = self.lang_var.get()
        return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)

    def _on_canvas_configure(self, event):
        # Force the inner frame to match the canvas width
        self.canvas.itemconfig(self.canvas_window_id, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def setup_ui(self):
        # Top Bar
        top_bar = ttk.Frame(self.root, padding="5")
        top_bar.pack(fill=tk.X)
        
        ttk.Label(top_bar, text="Idioma:").pack(side=tk.LEFT, padx=5)
        lang_cb = ttk.Combobox(top_bar, textvariable=self.lang_var, values=["ca", "es", "en"], state="readonly", width=5)
        lang_cb.pack(side=tk.LEFT)
        lang_cb.bind("<<ComboboxSelected>>", lambda e: self.apply_language())
        
        
        # Exit button removed


        self.btn_help = ttk.Button(top_bar, command=self.show_help_window, width=8)
        self.btn_help.pack(side=tk.RIGHT, padx=2)
        self.widgets["btn_help"] = self.btn_help
        
        ttk.Button(top_bar, text="Tema (Clar/Fosc)", command=self.toggle_theme).pack(side=tk.RIGHT, padx=5)
        
        # Footer (Credits) - Fixed at bottom outside scroll
        footer_frame = ttk.Frame(self.root, padding="5")
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        credits_container = ttk.Frame(footer_frame)
        credits_container.pack(anchor=tk.CENTER)
        
        self.lbl_made = ttk.Label(credits_container, text="Fet per SirSiscu", font=("Segoe UI", 8), foreground="#888888")
        self.lbl_made.pack(side=tk.LEFT, padx=2)
        self.widgets["credits_madeby"] = self.lbl_made
        
        ttk.Label(credits_container, text="·", font=("Segoe UI", 8), foreground="#888888").pack(side=tk.LEFT, padx=2)
        
        self.lbl_gh = ttk.Label(credits_container, text="GitHub", font=("Segoe UI", 8, "underline"), foreground="#888888", cursor="hand2")
        self.lbl_gh.pack(side=tk.LEFT, padx=2)
        self.lbl_gh.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/SirSiscu"))
        self.widgets["credits_github"] = self.lbl_gh

        ttk.Label(credits_container, text="·", font=("Segoe UI", 8), foreground="#888888").pack(side=tk.LEFT, padx=2)

        self.lbl_bmac = ttk.Label(credits_container, text="Buy Me a Coffee", font=("Segoe UI", 8, "underline"), foreground="#888888", cursor="hand2")
        self.lbl_bmac.pack(side=tk.LEFT, padx=2)
        self.lbl_bmac.bind("<Button-1>", lambda e: webbrowser.open_new("https://buymeacoffee.com/francescsala"))
        self.widgets["credits_bmac"] = self.lbl_bmac

        # Scrollable Main Content Wrapper
        container_frame = ttk.Frame(self.root)
        container_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(container_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.main_frame = ttk.Frame(self.canvas, padding="15")
        self.canvas_window_id = self.canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.main_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Logs Section (CREATED EARLY TO AVOID ATTRIBUTE ERROR)
        self.log_frame = ttk.LabelFrame(self.main_frame, padding="5")
        self.log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, pady=5)
        self.widgets["log_group"] = self.log_frame
        
        self.log_area = scrolledtext.ScrolledText(self.log_frame, state='disabled', height=8, font=("Consolas", 9))
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # Mode Section
        self.mode_frame = ttk.LabelFrame(self.main_frame, padding="10")
        self.mode_frame.pack(fill=tk.X, pady=5)
        self.widgets["mode_group"] = self.mode_frame
        
        for mode_key, val in [("mode1", "mode1"), ("mode2", "mode2"), ("mode3", "mode3")]:
            rb = ttk.Radiobutton(self.mode_frame, variable=self.mode_var, value=val, command=self.update_ui_state)
            rb.pack(anchor=tk.W, pady=2)
            self.widgets[mode_key] = rb
            
        self.lbl_desc = ttk.Label(self.mode_frame, textvariable=self.desc_var, font=("Segoe UI", 8), foreground="gray")
        self.lbl_desc.pack(anchor=tk.W, padx=20)

        # Paths Section
        self.path_frame = ttk.LabelFrame(self.main_frame, padding="10")
        self.path_frame.pack(fill=tk.X, pady=5)
        self.widgets["path_group"] = self.path_frame
        
        self.lbl_src = ttk.Label(self.path_frame)
        self.lbl_src.grid(row=0, column=0, sticky=tk.W)
        self.widgets["source"] = self.lbl_src
        
        ttk.Entry(self.path_frame, textvariable=self.source_path, width=65).grid(row=0, column=1, padx=5)
        self.btn_browse_src = ttk.Button(self.path_frame, command=self.browse_source)
        self.btn_browse_src.grid(row=0, column=2)
        self.widgets["browse"] = self.btn_browse_src
        
        self.lbl_dest = ttk.Label(self.path_frame)
        self.lbl_dest.grid(row=1, column=0, sticky=tk.W, pady=5)
        self.widgets["dest"] = self.lbl_dest
        
        self.entry_dest = ttk.Entry(self.path_frame, textvariable=self.dest_path, width=65)
        self.entry_dest.grid(row=1, column=1, padx=5, pady=5)
        
        self.btn_browse_dest = ttk.Button(self.path_frame, command=self.browse_dest)
        self.btn_browse_dest.grid(row=1, column=2, pady=5)

        # Options Section
        self.opts_frame = ttk.LabelFrame(self.main_frame, padding="10")
        self.opts_frame.pack(fill=tk.X, pady=5)
        self.widgets["opts_group"] = self.opts_frame
        
        self.chk_merge = ttk.Checkbutton(self.opts_frame, variable=self.merge_chapters_var)
        self.widgets["merge_chapters"] = self.chk_merge
        
        # Cleanup Options (Radio Buttons)
        self.cleanup_frame = ttk.LabelFrame(self.main_frame, padding="5")
        self.widgets["cleanup_group"] = self.cleanup_frame
        
        for i, (val, txt_key) in enumerate([("folder", "clean_folder"), ("recycle", "clean_recycle"), ("none", "clean_none")]):
             rb = ttk.Radiobutton(self.cleanup_frame, variable=self.cleanup_mode_var, value=val)
             rb.pack(anchor=tk.W)
             self.widgets[txt_key] = rb

        # Action Buttons (NOW ABOVE PROGRESS)
        action_frame = ttk.Frame(self.main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        self.action_frame_ref = action_frame
        
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)
        
        self.btn_analyze = ttk.Button(action_frame, command=self.start_analysis_thread)
        self.btn_analyze.grid(row=0, column=0, sticky="ew", padx=(0, 5), ipady=5)
        self.widgets["btn_analyze"] = self.btn_analyze
        
        self.btn_exec = ttk.Button(action_frame, command=self.start_execution_thread, state="disabled")
        self.btn_exec.grid(row=0, column=1, sticky="ew", padx=(5, 0), ipady=5)
        self.widgets["exec_btn"] = self.btn_exec
        
        # ToolTip for Exec Button
        self.btn_exec_tt = ToolTip(self.btn_exec, "Has d'analitzar primer")

        # Progress Area
        progress_frame = ttk.Frame(self.main_frame, padding="5")
        progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 2))
        
        self.lbl_status = ttk.Label(progress_frame, textvariable=self.status_var, font=("Segoe UI", 9, "italic"))
        self.lbl_status.pack(anchor=tk.W)
        
        # Results Table (Treeview)
        self.results_frame = ttk.LabelFrame(self.main_frame, text="Anàlisi / Selecció", padding="5")
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.widgets["results_group"] = self.results_frame
        
        # Toolbar (TOP) - Compact packing
        tools_frame = ttk.Frame(self.results_frame)
        tools_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 2))
        
        self.btn_sel_all = ttk.Button(tools_frame, command=self.select_all)
        self.btn_sel_all.pack(side=tk.LEFT, padx=(0, 5))
        self.widgets["btn_sel_all"] = self.btn_sel_all

        self.btn_sel_none = ttk.Button(tools_frame, command=self.select_none)
        self.btn_sel_none.pack(side=tk.LEFT)
        self.widgets["btn_sel_none"] = self.btn_sel_none
        
        # Stats Label aligned next to buttons
        self.lbl_stats_sel = ttk.Label(tools_frame, text="0 items selected", font=("Segoe UI", 9))
        self.lbl_stats_sel.pack(side=tk.LEFT, padx=10)
        
        # Treeview + Scrollbar
        # Use a container that strictly holds them without extra padding/gaps
        tree_container = ttk.Frame(self.results_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        cols = ("check", "name", "size", "status")
        self.tree = ttk.Treeview(tree_container, columns=cols, show='headings', selectmode='browse', height=8)
        
        self.tree.heading("check", text="Sel")
        self.tree.heading("name", text="Nom")
        self.tree.heading("size", text="Mida")
        self.tree.heading("status", text="Estat")
        
        self.tree.column("check", width=40, anchor="center", stretch=False)
        self.tree.column("name", width=300)
        self.tree.column("size", width=100)
        self.tree.column("status", width=250) 
        
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind click 
        self.tree.bind('<Button-1>', self.on_tree_click)

    def toggle_theme(self):
        current = self.theme_var.get()
        new = "dark" if current == "light" else "light"
        self.theme_var.set(new)
        self.apply_theme()

    def apply_theme(self):
        theme = THEMES[self.theme_var.get()]
        style = ttk.Style()
        style.theme_use('clam')
        
        self.root.configure(bg=theme["bg"])
        self.main_frame.configure(style="TFrame")
        
        self.root.option_add('*TCombobox*Listbox.background', theme["input_bg"])
        self.root.option_add('*TCombobox*Listbox.foreground', theme["input_fg"])
        
        style.configure(".", background=theme["bg"], foreground=theme["fg"])
        style.configure("TLabel", background=theme["bg"], foreground=theme["fg"])
        style.configure("TFrame", background=theme["bg"])
        style.configure("TLabelframe", background=theme["bg"], foreground=theme["highlight"])
        style.configure("TLabelframe.Label", background=theme["bg"], foreground=theme["highlight"])
        style.configure("TButton", background=theme["frame_bg"], foreground=theme["fg"])
        style.map("TButton", 
            background=[("active", theme["highlight"]), ("disabled", theme["disabled_bg"])],
            foreground=[("active", theme["btn_fg"]), ("disabled", theme["disabled_fg"])]
        )
        style.configure("TEntry", fieldbackground=theme["input_bg"], foreground=theme["input_fg"])
        
        style.configure("TCombobox", fieldbackground=theme["input_bg"], background=theme["bg"], foreground=theme["input_fg"], selectbackground=theme["highlight"])
        style.map("TCombobox", fieldbackground=[("readonly", theme["input_bg"])], foreground=[("readonly", theme["input_fg"])])
        
        style.configure("TCheckbutton", background=theme["bg"], foreground=theme["fg"])
        style.configure("TRadiobutton", background=theme["bg"], foreground=theme["fg"])
        
        # Treeview colors
        style.configure("Treeview", 
            background=theme["input_bg"], 
            foreground=theme["input_fg"], 
            fieldbackground=theme["input_bg"],
            borderwidth=0
        )
        style.map("Treeview", 
            background=[("selected", theme["highlight"])], 
            foreground=[("selected", theme["btn_fg"])]
        )
        style.configure("Treeview.Heading", background=theme["frame_bg"], foreground=theme["fg"], relief="flat")
        style.map("Treeview.Heading", background=[("active", theme["highlight"])])
        
        self.log_area.configure(bg=theme["input_bg"], fg=theme["input_fg"], insertbackground=theme["fg"])

        # Re-apply tags to tree to ensure colors update
        self.tree.tag_configure('valid', foreground=theme["input_fg"])
        self.tree.tag_configure('invalid', foreground=theme["disabled_fg"])

    def update_selection_stats(self):
        count = len(self.checked_items)
        size = 0
        
        lookup = {x['id']: x for x in self.analysis_results}
        
        for iid in self.checked_items:
            if iid in lookup:
                size += lookup[iid]['orig_size']
        
        # Update label instead of frame title
        txt = self.tr("stats_sel").format(count, format_bytes(size))
        try:
             self.lbl_stats_sel.configure(text=txt)
        except: pass
        
        # Reset frame title to static
        # self.results_frame.configure(text=self.tr('results_group')) 
        # Actually, let's keep it simple or just leave it. If we don't update it, it stays "Analysis/Selection".
        # But if it was updated previously, we might need to reset it? 
        # Since we create frame fresh in setup_ui, it starts clean.
        # But we should ensure we don't overwrite it with stats anymore. OK.
        
        if count > 0:
             self.btn_exec.state(["!disabled"])
        else:
             self.btn_exec.state(["disabled"])
        
        self.update_exec_tooltip()

    def apply_language(self):
        for key, widget in self.widgets.items():
            txt = self.tr(key)
            if hasattr(widget, 'configure'):
                widget.configure(text=txt)
        
        self.btn_browse_src.configure(text=self.tr("browse"))
        self.btn_browse_dest.configure(text=self.tr("browse"))
        self.update_ui_state()
    def update_ui_state(self):
        mode = self.mode_var.get()
        self.desc_var.set(self.tr(f"{mode}_desc"))
        self.entry_dest.state(["!disabled"])
        self.btn_browse_dest.state(["!disabled"])
        
        # Reset visibility
        self.opts_frame.pack_forget()
        self.cleanup_frame.pack_forget()
        self.chk_merge.pack_forget()

        if mode == "mode1":
            # Mode 1: Cleanup options only
            self.cleanup_frame.pack(fill=tk.X, padx=5, pady=5, before=self.action_frame_ref)
        elif mode == "mode2":
            # Mode 2: Advanced Options (Merge)
            self.opts_frame.pack(fill=tk.X, pady=5, before=self.action_frame_ref)
            self.chk_merge.pack(anchor=tk.W)
        elif mode == "mode3":
            # Mode 3: Cleanup options only
            self.cleanup_frame.pack(fill=tk.X, padx=5, pady=5, before=self.action_frame_ref)

    def browse_source(self):
        path = filedialog.askdirectory()
        if path:
            self.source_path.set(path)
            if not self.dest_path.get() and self.mode_var.get() != "mode2":
                self.dest_path.set(str(Path(path).parent / "CBZ_Output"))

    def browse_dest(self):
        path = filedialog.askdirectory()
        if path:
            self.dest_path.set(path)

    def check_log_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get_nowait()
            self.log_area.config(state='normal')
            self.log_area.insert(tk.END, msg + "\n")
            self.log_area.see(tk.END)
            self.log_area.config(state='disabled')
        self.root.after(100, self.check_log_queue)

    def update_exec_tooltip(self):
        state = self.btn_exec.state()
        if "disabled" in state:
            self.btn_exec_tt.text = self.tr("msg_need_analysis") if not self.analysis_results else self.tr("msg_select_items")
        else:
             self.btn_exec_tt.text = ""

    def start_analysis_thread(self):
        source = self.source_path.get()
        if not source or not os.path.exists(source):
            messagebox.showerror("Error", self.tr("err_source"))
            return
            
        # Reset UI
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.btn_exec.state(["disabled"])
        self.analysis_results = []
        self.checked_items = set()
        self.error_logs = []
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        
        self.btn_analyze.state(["disabled"])
        self.status_var.set("Analyzing...")
        
        threading.Thread(target=self.run_analysis, daemon=True).start()

    def run_analysis(self):
        mode = self.mode_var.get()
        source = self.source_path.get()
        merge = self.merge_chapters_var.get()
        
        self.logger.info(f"Starting Analysis: {mode}")
        results = []
        
        try:
            if mode == "mode1":
                results = logic_compress.analyze_folders(source)
            elif mode == "mode2":
                results = logic_organize.analyze_loose_images(source, merge)
            elif mode == "mode3":
                results = logic_archive.scan_archives(source)
                
            self.analysis_results = results
            self.root.after(0, self.update_tree_results)
            
        except Exception as e:
            self.logger.error(f"Analysis Failed: {e}")
            self.status_var.set("Analysis Error")
        finally:
            self.root.after(0, lambda: self.btn_analyze.state(["!disabled"]))

    def update_tree_results(self):
        items = self.analysis_results
        count = 0
        
        # Clear existing
        for c in self.tree.get_children():
            self.tree.delete(c)
            
        for item in items:
            size_str = format_bytes(item['orig_size'])
            
            # Checkbox char
            if item['valid']:
                check_char = "☑" # Started checked by default
                
                # Get translated status
                status_key = item.get('status_key', 'status_ready')
                status_args = item.get('status_args', ())
                try:
                    status = self.tr(status_key).format(*status_args)
                except:
                    status = item.get('reason', '')
                
                self.checked_items.add(item['id'])
                count += 1
            else:
                check_char = "☒" 
                
                # Invalid status
                status_key = item.get('status_key', 'status_invalid')
                status_args = item.get('status_args', ())
                if not status_args and 'reason' in item:
                     status_args = (item['reason'],)
                
                try:
                     status = self.tr(status_key).format(*status_args)
                except:
                     status = item.get('reason', '')
            
            tags = ('valid',) if item['valid'] else ('invalid',)
            
            self.tree.insert('', tk.END, iid=item['id'], values=(check_char, item['name'], size_str, status), tags=tags)
        
        # Tag configs
        self.tree.tag_configure('invalid', foreground='gray')
        # self.tree.tag_configure('valid') usually black
        
        self.update_selection_stats()
        
        if count > 0:
            self.status_var.set(f"Analysis done. {count} items found.")
        else:
            self.status_var.set("No valid items found.")
            
    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading": return
        
        item_id = self.tree.identify_row(event.y)
        if not item_id: return
        
        # Only toggle valid items
        # Check validity from analysis results
        item_data = next((x for x in self.analysis_results if x['id'] == item_id), None)
        if not item_data or not item_data['valid']:
            return

        # Toggle check
        if item_id in self.checked_items:
            self.checked_items.remove(item_id)
            new_char = "☐"
        else:
            self.checked_items.add(item_id)
            new_char = "☑"
            
        self.tree.set(item_id, column="check", value=new_char)
        self.update_selection_stats()

    def update_selection_stats(self):
        count = len(self.checked_items)
        size = 0
        
        lookup = {x['id']: x for x in self.analysis_results}
        
        for iid in self.checked_items:
            if iid in lookup:
                size += lookup[iid]['orig_size']
                
        txt = self.tr("stats_sel").format(count, format_bytes(size))
        self.lbl_stats_sel.configure(text=txt)
        
        if count > 0:
             self.btn_exec.state(["!disabled"])
        else:
             self.btn_exec.state(["disabled"])
        
        self.update_exec_tooltip()

    def select_all(self):
        for item in self.analysis_results:
            if item['valid']:
                self.checked_items.add(item['id'])
                if self.tree.exists(item['id']):
                    self.tree.set(item['id'], "check", "☑")
        self.update_selection_stats()
        
    def select_none(self):
        self.checked_items.clear()
        for item in self.analysis_results:
            if self.tree.exists(item['id']):
                 # If valid it becomes unchecked, if invalid it stays invalid mark
                 if item['valid']:
                    self.tree.set(item['id'], "check", "☐")
        self.update_selection_stats()

    def start_execution_thread(self):
        if not self.dest_path.get() and self.mode_var.get() != "mode2":
             messagebox.showerror("Error", self.tr("err_dest"))
             return
                 
        if not self.checked_items:
            return

        self.btn_exec.state(["disabled"])
        self.btn_analyze.state(["disabled"])
        self.progress_var.set(0)
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        
        threading.Thread(target=self.run_execution, daemon=True).start()

    def run_execution(self):
        mode = self.mode_var.get()
        source = self.source_path.get()
        dest = self.dest_path.get()
        if not dest and mode == "mode2":
            dest = source
            
        cleanup_mode = self.cleanup_mode_var.get()
        
        # Use checked_items NOT tree.selection()
        items_to_process = [x for x in self.analysis_results if x['id'] in self.checked_items]
        
        self.logger.info(f"--- {self.tr('exec_btn')} ({mode}) ---")
        self.logger.info(f"Processing {len(items_to_process)} checked items...")
        
        start_time = time.time()
        stats = {}
        
        def update_progress_cb(i, total, name):
            pct = ((i+1) / total) * 100
            self.root.after(0, lambda: self.progress_var.set(pct))

        try:
            if mode == "mode1":
                stats = logic_compress.process_batch(items_to_process, dest, cleanup_mode, update_progress_cb)
            elif mode == "mode2":
                stats = logic_organize.process_batch(items_to_process, dest, update_progress_cb)
            elif mode == "mode3":
                stats = logic_archive.process_batch(items_to_process, dest, cleanup_mode, update_progress_cb)
                
            elapsed = time.time() - start_time
            self.status_var.set(self.tr("success"))
            self.logger.info("DONE.")
            
            self.root.after(0, lambda: self.show_summary(elapsed, stats))
            
        except Exception as e:
            self.logger.error(f"CRITICAL: {e}")
            self.status_var.set(self.tr("error"))
        finally:
            self.root.after(0, lambda: self.btn_exec.state(["!disabled"]))
            self.root.after(0, lambda: self.btn_analyze.state(["!disabled"]))
            self.root.after(0, self.update_exec_tooltip)

    def show_help_window(self):
        win = tk.Toplevel(self.root)
        win.title(self.tr("help_title"))
        win.geometry("500x650")
        
        theme = THEMES[self.theme_var.get()]
        win.configure(bg=theme["bg"])
        
        # Helper to parse simplified text
        # Supported: # Header, * Bullet, **Bold**, [Link](url)
        txt_content = self.tr("help_text")
        
        text_widget = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Segoe UI", 10), padx=20, pady=20)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.configure(bg=theme["input_bg"], fg=theme["input_fg"], insertbackground=theme["fg"])
        
        # Tags formatting
        text_widget.tag_config("header", font=("Segoe UI", 14, "bold"), foreground=theme["highlight"], spacing3=10)
        text_widget.tag_config("bullet", lmargin1=15, lmargin2=25)
        text_widget.tag_config("bold", font=("Segoe UI", 10, "bold"))
        text_widget.tag_config("link", foreground="#3366CC" if theme["bg"]=="#ffffff" else "#6699FF", underline=1)
        text_widget.tag_config("normal", font=("Segoe UI", 10))
        
        # Parsing loop
        import re
        lines = txt_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                text_widget.insert(tk.END, "\n")
                continue
                
            if line.startswith("# "):
                text_widget.insert(tk.END, line[2:] + "\n", "header")
                continue
            
            tags = ["normal"]
            prefix = ""
            if line.startswith("* "):
                tags.append("bullet")
                line = "• " + line[2:]
            
            # Simple parser for **bold** and [link](url)
            # We iterate characters or stick to simple regex splits
            # Let's do a simple segment split
            
            # Split by links first: [text](url)
            parts = re.split(r'(\[.*?\]\(.*?\))', line)
            
            for part in parts:
                if part.startswith("[") and "](" in part and part.endswith(")"):
                    # It's a link
                    try:
                        lbl = part[1:part.rfind("](")]
                        url = part[part.rfind("](")+2 : -1]
                        
                        # Apply bold inside link? Too complex, assume plain link
                        tag_link_name = f"link_{len(text_widget.get('1.0', tk.END))}"
                        text_widget.tag_config(tag_link_name, foreground="#4a90e2", underline=1)
                        text_widget.tag_bind(tag_link_name, "<Button-1>", lambda e, u=url: webbrowser.open(u))
                        text_widget.tag_bind(tag_link_name, "<Enter>", lambda e: text_widget.config(cursor="hand2"))
                        text_widget.tag_bind(tag_link_name, "<Leave>", lambda e: text_widget.config(cursor=""))
                        
                        text_widget.insert(tk.END, lbl, tag_link_name)
                    except:
                        text_widget.insert(tk.END, part, tags)
                else:
                    # Parse bold **text**
                    subparts = re.split(r'(\*\*.*?\*\*)', part)
                    for sp in subparts:
                        if sp.startswith("**") and sp.endswith("**"):
                            text_widget.insert(tk.END, sp[2:-2], tuple(tags + ["bold"]))
                        else:
                            text_widget.insert(tk.END, sp, tuple(tags))
            
            text_widget.insert(tk.END, "\n", tuple(tags))

        text_widget.configure(state="disabled")
        
        ttk.Button(win, text=self.tr("sum_close"), command=win.destroy).pack(pady=10)

    def show_summary(self, elapsed, stats):
        win = tk.Toplevel(self.root)
        win.title(self.tr("sum_title"))
        win.geometry("450x450")
        
        theme = THEMES[self.theme_var.get()]
        win.configure(bg=theme["bg"])
        
        f = ttk.Frame(win, padding="20")
        f.pack(fill=tk.BOTH, expand=True)
        
        # Styles
        lbl_style = {"background": theme["bg"], "foreground": theme["fg"], "font": ("Segoe UI", 10)}
        val_style = {"background": theme["bg"], "foreground": theme["highlight"], "font": ("Segoe UI", 10, "bold")}
        
        def row(label_k, value):
            container = tk.Frame(f, bg=theme["bg"])
            container.pack(fill=tk.X, pady=2)
            tk.Label(container, text=self.tr(label_k), **lbl_style).pack(side=tk.LEFT)
            tk.Label(container, text=value, **val_style).pack(side=tk.RIGHT)
            
        # Keys
        k_processed = "sum_processed"
        k_errors = "sum_errors"
        k_orig_s = "sum_orig_size"
        k_final_s = "sum_final_size"
        k_saved = "sum_saved"

        row("sum_total_time", f"{elapsed:.1f}s")
        row(k_processed, str(stats["processed"]))
        row(k_errors, str(stats["errors"]))
        
        ttk.Separator(f, orient='horizontal').pack(fill=tk.X, pady=10)
        
        row(k_orig_s, format_bytes(stats["orig_bytes"]))
        row(k_final_s, format_bytes(stats["final_bytes"]))
        
        saved = stats["orig_bytes"] - stats["final_bytes"]
        saved_str = format_bytes(saved)
        if saved > 0:
            pct = int((saved/stats['orig_bytes'])*100) if stats['orig_bytes'] else 0
            saved_str += f" (-{pct}%)"
            
        row(k_saved, saved_str)
        
        ttk.Separator(f, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Actions
        actions_frame = tk.Frame(f, bg=theme["bg"])
        actions_frame.pack(fill=tk.X, pady=5)
        
        # 1. Open Dest (Mode 1 & 3)
        if self.mode_var.get() in ["mode1", "mode3"]:
            dest = self.dest_path.get()
            if os.path.exists(dest):
                ttk.Button(actions_frame, text=self.tr("act_open_dest"), 
                           command=lambda: os.startfile(dest)).pack(fill=tk.X, pady=2)

        # 2. Cleanup Actions (If 'folder' mode was selected and stats > 0)
        if self.cleanup_mode_var.get() == "folder" and stats["processed"] > 0 and self.mode_var.get() in ["mode1", "mode3"]:
             source_trash = Path(self.source_path.get()) / "TO_DELETE"
             if source_trash.exists():
                 ttk.Button(actions_frame, text=self.tr("act_open_orig"), 
                            command=lambda: os.startfile(source_trash)).pack(fill=tk.X, pady=2)
                            
                 ttk.Button(actions_frame, text=self.tr("act_recycle_orig"), 
                            command=lambda: self.confirm_recycle(source_trash)).pack(fill=tk.X, pady=2)

        if self.error_logs:
            btn_log = ttk.Button(f, text=self.tr("sum_view_log"), command=self.show_error_log)
            btn_log.pack(fill=tk.X, pady=5)
            
        ttk.Button(f, text=self.tr("sum_close"), command=win.destroy).pack(fill=tk.X, pady=5)

    def confirm_recycle(self, trash_path):
        msg = self.tr("confirm_recycle_msg").format(trash_path.name)
        if messagebox.askyesno(self.tr("confirm_recycle_title"), msg, icon='warning'):
            ok, err = utils.send_to_recycle_bin(trash_path)
            if ok:
                messagebox.showinfo("Info", self.tr("recycled_ok"))
            else:
                messagebox.showerror("Error", f"Failed: {err}")

    def show_error_log(self):
        win = tk.Toplevel(self.root)
        win.title(self.tr("log_filter_title"))
        win.geometry("500x400")
        
        txt = scrolledtext.ScrolledText(win, width=60, height=20)
        txt.pack(fill=tk.BOTH, expand=True)
        
        for err in self.error_logs:
            txt.insert(tk.END, err + "\n")
