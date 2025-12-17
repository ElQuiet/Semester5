import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import time

#ngatur tema
THEME = {
    "bg_app": "#121212", "bg_panel": "#1E1E1E", "phone_bg": "#000000",
    "text": "#E0E0E0", "accent": "#BB86FC", "good": "#03DAC6",
    "bad": "#CF6679", "warn": "#FFB74D", "btn": "#3700B3"
}

# Logika buat analisis tidurnya
class SleepLogic:
    def __init__(self):
        self.PENALTY_SNORE_PER_HOUR = 25.0
        self.PENALTY_MOVE_PER_HOUR = 40.0
        self.RECOVERY_PER_HOUR = 10.0
        self.reset()

    def reset(self):
        self.score = 100.0
        self.total_virtual_seconds = 0.0
        self.snore_duration = 0.0
        self.restless_duration = 0.0

    def update(self, delta_virtual, mic_val, mpu_val):
        self.total_virtual_seconds += delta_virtual
        delta_hour = delta_virtual / 3600.0
        
        is_disturbed = False
        if mpu_val > 40: # Tanda klo Gelisah
            self.score -= self.PENALTY_MOVE_PER_HOUR * delta_hour
            self.restless_duration += delta_virtual
            is_disturbed = True
        elif mic_val > 50: # Tanda klo Mendengkur
            self.score -= self.PENALTY_SNORE_PER_HOUR * delta_hour
            self.snore_duration += delta_virtual
            is_disturbed = True
            
        if not is_disturbed and self.score < 100:
            self.score += self.RECOVERY_PER_HOUR * delta_hour
            
        self.score = max(0, min(100, self.score))
        return self.score

    def get_analysis_report(self):
        total_h = self.total_virtual_seconds / 3600.0
        snore_h = self.snore_duration / 3600.0
        move_h = self.restless_duration / 3600.0
        
        if self.score >= 80: grade = "SANGAT BAIK"
        elif self.score >= 60: grade = "CUKUP"
        else: grade = "BURUK"
        
        tips = []
        if snore_h > 0.5: tips.append(f"• Terdeteksi mendengkur {snore_h:.1f} jam. Cek posisi tidur.")
        if move_h > 0.5: tips.append(f"• Gelisah {move_h:.1f} jam. Pastikan suhu nyaman.")
        if total_h < 6: tips.append("• Durasi tidur kurang dari 6 jam.")
        if not tips: tips.append("• Tidur Anda sempurna!")

        return grade, total_h, tips

#UI halaman utama jirs 
class MainMenu(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=THEME["bg_app"])
        center = tk.Frame(self, bg=THEME["bg_app"])
        center.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(center, text="SleepWell", font=("Helvetica", 40, "bold"), bg=THEME["bg_app"], fg=THEME["accent"]).pack(pady=10)
        
        btn_cfg = {"font": ("Arial", 12, "bold"), "width": 25, "pady": 10, "relief": "flat"}
        tk.Button(center, text="MULAI MONITORING", bg=THEME["btn"], fg="white", **btn_cfg,
                  command=lambda: controller.show_frame("Dashboard")).pack(pady=10)
        tk.Button(center, text="PENGATURAN WAKTU", bg=THEME["bg_panel"], fg="white", **btn_cfg,
                  command=lambda: controller.show_frame("Settings")).pack(pady=10)
        tk.Button(center, text="KELUAR", bg=THEME["bad"], fg="white", **btn_cfg,
                  command=controller.quit).pack(pady=10)

# UI setting
class SettingsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=THEME["bg_app"])
        self.controller = controller
        tk.Label(self, text="PENGATURAN SIMULASI", font=("Helvetica", 20, "bold"), bg=THEME["bg_app"], fg="white").pack(pady=50)

        f = tk.Frame(self, bg=THEME["bg_panel"], padx=30, pady=30)
        f.pack()
        
        self.lbl_speed = tk.Label(f, text="1x (Real-time)", bg=THEME["bg_panel"], fg="white", font=("Arial", 14))
        self.lbl_speed.pack(anchor="w")
        self.speed_var = tk.DoubleVar(value=1.0)
        ttk.Scale(f, from_=1, to=3600, variable=self.speed_var, orient="horizontal", length=400, command=self.update_txt).pack(pady=20)
        
        tk.Button(self, text="SIMPAN & KEMBALI", bg=THEME["btn"], fg="white", font=("Arial", 12), width=20, pady=10,
                  command=lambda: controller.show_frame("Menu")).pack(pady=30)

    def update_txt(self, val):
        v = float(val)
        self.controller.time_multiplier = v
        txt = f"{int(v)}x (1 Detik = {int(v/60)} Menit)" if v < 3600 else "3600x (1 Detik = 1 Jam)"
        self.lbl_speed.config(text=txt)

#UI tampilan 
class DashboardPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=THEME["bg_app"])
        self.controller = controller
        self.logic = SleepLogic()
        self.is_running = False
        self.last_real_time = 0
        self.times, self.fsr_d, self.mic_d, self.mpu_d = [], [], [], []
        
        self.sim_fsr = tk.DoubleVar(value=0)
        self.sim_mic = tk.DoubleVar(value=10)
        self.sim_mpu = tk.DoubleVar(value=0)
        self._setup_layout()

    def _setup_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        col_hp = tk.Frame(self, bg=THEME["bg_app"], width=320)
        col_hp.grid(row=0, column=0, sticky="nsew")
        col_hp.pack_propagate(False)
        
        phone = tk.Frame(col_hp, bg="black", bd=10, relief="raised")
        phone.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(phone, text="SleepWell", bg="black", fg=THEME["accent"], font=("Arial", 16, "bold")).pack(pady=20)
        
        self.canvas = tk.Canvas(phone, width=200, height=200, bg="black", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.canvas.create_oval(10, 10, 190, 190, outline="#333", width=15)
        self.arc = self.canvas.create_arc(10, 10, 190, 190, start=90, extent=359, style=tk.ARC, outline=THEME["good"], width=15)
        self.txt_score = self.canvas.create_text(100, 100, text="100", font=("Arial", 45, "bold"), fill="white")
        
        self.lbl_timer = tk.Label(phone, text="00:00:00", bg="black", fg="white", font=("Consolas", 24))
        self.lbl_timer.pack(pady=20)
        self.lbl_status = tk.Label(phone, text="Siap", bg="black", fg="#888", font=("Arial", 12))
        self.lbl_status.pack()
        
        self.btn_action = tk.Button(phone, text="MULAI TIDUR", bg=THEME["btn"], fg="white", font=("Arial", 12, "bold"),
                                    command=self.toggle_sleep, pady=10, relief="flat")
        self.btn_action.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=30)

        col_graph = tk.Frame(self, bg=THEME["bg_app"])
        col_graph.grid(row=0, column=1, sticky="nsew")
        self.fig = Figure(figsize=(5, 4), dpi=100, facecolor=THEME["bg_app"])
        self.ax1 = self.fig.add_subplot(311)
        self.ax2 = self.fig.add_subplot(312)
        self.ax3 = self.fig.add_subplot(313)
        self.canvas_plot = FigureCanvasTkAgg(self.fig, master=col_graph)
        self.canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self._init_graphs()

        col_ctrl = tk.Frame(self, bg=THEME["bg_panel"], width=280)
        col_ctrl.grid(row=0, column=2, sticky="nsew")
        col_ctrl.pack_propagate(False)
        
        tk.Label(col_ctrl, text="SENSOR CONTROL", bg=THEME["bg_panel"], fg=THEME["accent"], font=("Arial", 12, "bold")).pack(pady=20)
        
        self.add_slider(col_ctrl, "FSR (Tekanan)", self.sim_fsr, THEME["good"])
        self.add_slider(col_ctrl, "Mic (dB)", self.sim_mic, THEME["bad"])
        self.add_slider(col_ctrl, "MPU (Gerak)", self.sim_mpu, THEME["warn"])

        tk.Label(col_ctrl, text="--- Preset ---", bg=THEME["bg_panel"], fg="#888").pack(pady=10)
        ttk.Button(col_ctrl, text="Tidur Pulas", command=lambda: self.set_sim(50, 10, 0)).pack(fill=tk.X, padx=20, pady=2)
        ttk.Button(col_ctrl, text="Mendengkur", command=lambda: self.set_sim(50, 80, 5)).pack(fill=tk.X, padx=20, pady=2)
        
        nav = tk.Frame(col_ctrl, bg=THEME["bg_panel"])
        nav.pack(side=tk.BOTTOM, fill=tk.X, pady=20, padx=20)
        tk.Button(nav, text="< MENU", bg="#555", fg="white", pady=8, command=self.back_to_menu).pack(fill=tk.X, pady=5)
        tk.Button(nav, text="X EXIT", bg=THEME["bad"], fg="white", pady=8, command=self.controller.quit).pack(fill=tk.X, pady=5)

    def add_slider(self, parent, lbl, var, col):
        f = tk.Frame(parent, bg=THEME["bg_panel"], pady=5)
        f.pack(fill=tk.X, padx=15)
        tk.Label(f, text=lbl, bg=THEME["bg_panel"], fg="white").pack(anchor="w")
        val_lbl = tk.Label(f, text="0", bg=THEME["bg_panel"], fg=col, font=("Consolas", 10, "bold"))
        val_lbl.pack(anchor="e")
        ttk.Scale(f, from_=0, to=100, variable=var, command=lambda v: val_lbl.config(text=f"{float(v):.1f}")).pack(fill=tk.X)

    def _init_graphs(self):
        self.lines = []
        for ax, col, tit in zip([self.ax1, self.ax2, self.ax3], [THEME["good"], THEME["bad"], THEME["warn"]], ["FSR", "Mic", "MPU"]):
            ax.set_facecolor(THEME["bg_app"])
            ax.tick_params(colors="white", labelsize=8)
            for s in ax.spines.values(): s.set_color("#444")
            ax.set_title(tit, color=col, fontsize=9, loc='left')
            ax.grid(color="#333", linestyle="--")
            ax.set_ylim(0, 105)
            l, = ax.plot([], [], color=col, lw=1.5)
            self.lines.append(l)
        self.fig.tight_layout()

    def set_sim(self, f, m, mp):
        self.sim_fsr.set(f); self.sim_mic.set(m); self.sim_mpu.set(mp)

    def back_to_menu(self):
        if self.is_running:
            self.is_running = False
        self.controller.show_frame("Menu")

    def toggle_sleep(self):
        if not self.is_running:
            if self.sim_fsr.get() < 20:
                messagebox.showwarning("FSR Error", "Tidak ada orang di kasur (Naikkan FSR)")
                return
            self.is_running = True
            self.logic.reset()
            self.times, self.fsr_d, self.mic_d, self.mpu_d = [], [], [], []
            self.last_real_time = time.time()
            self.btn_action.config(text="BANGUN (SELESAI)", bg=THEME["bad"])
            self.loop_monitor()
        else:
            self.is_running = False
            self.btn_action.config(text="MULAI TIDUR", bg=THEME["btn"])
            self.show_final_report()

    def loop_monitor(self):
        if not self.is_running: return

        # 1. Update Waktu
        now = time.time()
        delta_real = now - self.last_real_time
        self.last_real_time = now
        mult = self.controller.time_multiplier
        delta_virtual = delta_real * mult

        # 2. Ambil Sensor
        f, m, mp = self.sim_fsr.get(), self.sim_mic.get(), self.sim_mpu.get()

        # FITUR AUTO STOP (FSR < 20) 
        if f < 20:
            self.is_running = False
            self.btn_action.config(text="MULAI TIDUR", bg=THEME["btn"])
            # Tampilkan pesan Auto Stop
            messagebox.showinfo("Auto-Stop", "Tekanan hilang (Pengguna bangun).\nMonitoring dihentikan otomatis.")
            self.show_final_report()
            return 

        # 3. Update Logika & UI
        score = self.logic.update(delta_virtual, m, mp)
        
        total_sec = int(self.logic.total_virtual_seconds)
        self.lbl_timer.config(text=f"{total_sec//3600:02}:{(total_sec%3600)//60:02}:{total_sec%60:02}")
        
        self.canvas.itemconfigure(self.arc, extent=(score/100)*359)
        col = THEME["good"] if score > 70 else (THEME["bad"] if score < 40 else THEME["warn"])
        self.canvas.itemconfigure(self.arc, outline=col)
        self.canvas.itemconfigure(self.txt_score, text=f"{int(score)}")

        st = "GELISAH!" if mp > 40 else ("MENDENGKUR" if m > 50 else "Tidur Nyenyak")
        self.lbl_status.config(text=st, fg=col)

        # 4. Update Grafik
        curr_h = self.logic.total_virtual_seconds / 3600.0
        if not self.times or (curr_h - self.times[-1] > (0.01 if mult > 100 else 0.0001)):
            self.times.append(curr_h)
            self.fsr_d.append(f); self.mic_d.append(m); self.mpu_d.append(mp)
            if len(self.times) > 100:
                self.times.pop(0); self.fsr_d.pop(0); self.mic_d.pop(0); self.mpu_d.pop(0)
            self.lines[0].set_data(self.times, self.fsr_d)
            self.lines[1].set_data(self.times, self.mic_d)
            self.lines[2].set_data(self.times, self.mpu_d)
            for ax in [self.ax1, self.ax2, self.ax3]: ax.relim(); ax.autoscale_view()
            self.canvas_plot.draw_idle()

        self.after(50, self.loop_monitor)

    def show_final_report(self):
        grade, duration, tips = self.logic.get_analysis_report()
        msg = f"Kualitas: {grade}\nSkor: {int(self.logic.score)}\nDurasi: {duration:.2f} Jam\n\n" + "\n".join(tips)
        messagebox.showinfo("Laporan Tidur", msg)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SleepWell Simulator Final Version")
        self.geometry("1100x700")
        self.time_multiplier = 1.0
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (MainMenu, SettingsPage, DashboardPage):
            page_name = "Menu" if F == MainMenu else ("Settings" if F == SettingsPage else "Dashboard")
            f = F(parent=container, controller=self)
            self.frames[page_name] = f
            f.grid(row=0, column=0, sticky="nsew")
        self.show_frame("Menu")
    def show_frame(self, name): self.frames[name].tkraise()

if __name__ == "__main__":
    App().mainloop()