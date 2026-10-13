import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser
import json
import os
import math
import copy

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ============================================================
# КОНСТАНТЫ
# ============================================================
DEFAULT_PHASE_COLORS = {
    "A": "#E53935", "B": "#43A047", "C": "#1E88E5",
    "AB": "#8E24AA", "BC": "#FB8C00", "AC": "#00ACC1",
    "ABC": "#6D4C41",
    "NONE": "#B0BEC5",
}

USAGE_RU = {
    "constant": "постоянный",
    "temporary": "временный",
    "rare": "1 раз в сутки",
}
USAGE_KEYS = ["constant", "temporary", "rare"]
USAGE_RU_LIST = [USAGE_RU[k] for k in USAGE_KEYS]


def usage_to_key(ru):
    for k, v in USAGE_RU.items():
        if v == ru:
            return k
    return "temporary"


def usage_to_ru(key):
    return USAGE_RU.get(key, key)


TEMPLATES_FILE = "appliance_templates.json"
PHASE_COLORS_FILE = "phase_colors.json"
SETTINGS_FILE = "power_settings.json"

DEFAULT_TEMPLATES = {
    "Чайник":         {"power_kw": 2.0,  "phases": 1, "usage": "temporary", "cos_phi": 1.0},
    "Микроволновка":  {"power_kw": 1.0,  "phases": 1, "usage": "temporary", "cos_phi": 1.0},
    "Холодильник":    {"power_kw": 0.3,  "phases": 1, "usage": "constant",  "cos_phi": 0.8},
    "Стиральная машина": {"power_kw": 2.2, "phases": 1, "usage": "temporary", "cos_phi": 0.9},
    "Посудомоечная":  {"power_kw": 2.0,  "phases": 1, "usage": "temporary", "cos_phi": 0.9},
    "Утюг":           {"power_kw": 2.2,  "phases": 1, "usage": "temporary", "cos_phi": 1.0},
    "Пылесос":        {"power_kw": 1.5,  "phases": 1, "usage": "temporary", "cos_phi": 0.85},
    "Телевизор":      {"power_kw": 0.15, "phases": 1, "usage": "constant",  "cos_phi": 0.95},
    "Компьютер":      {"power_kw": 0.3,  "phases": 1, "usage": "constant",  "cos_phi": 0.95},
    "Освещение":      {"power_kw": 0.5,  "phases": 1, "usage": "constant",  "cos_phi": 1.0},
    "Кондиционер":    {"power_kw": 2.5,  "phases": 1, "usage": "temporary", "cos_phi": 0.85},
    "Обогреватель":   {"power_kw": 2.0,  "phases": 1, "usage": "temporary", "cos_phi": 1.0},
    "Бойлер":         {"power_kw": 2.0,  "phases": 1, "usage": "rare",      "cos_phi": 1.0},
    "Насос":          {"power_kw": 1.1,  "phases": 1, "usage": "rare",      "cos_phi": 0.75},
    "Котёл":          {"power_kw": 12.0, "phases": 3, "usage": "constant",  "cos_phi": 1.0},
    "Электроплита":   {"power_kw": 6.0,  "phases": 3, "usage": "temporary", "cos_phi": 1.0},
    "Сауна":          {"power_kw": 4.5,  "phases": 3, "usage": "rare",      "cos_phi": 1.0},
    "Зарядка авто":   {"power_kw": 7.0,  "phases": 3, "usage": "rare",      "cos_phi": 1.0},
}

DEFAULT_SETTINGS = {
    "voltage_A": 230.0,
    "voltage_B": 230.0,
    "voltage_C": 230.0,
    "voltage_line_AB": 400.0,
    "voltage_line_BC": 400.0,
    "voltage_line_AC": 400.0,
    "input_limit_kw": 15.0,
    "input_limit_a": 25.0,
}


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
# РАСЧЁТ
# ============================================================
def current_per_phase(power_kw, phases, phase_connections, cos_phi, settings):
    result = {"A": 0.0, "B": 0.0, "C": 0.0}
    if cos_phi <= 0:
        cos_phi = 1.0

    if phases == 1:
        ph = phase_connections[0]
        u = settings.get(f"voltage_{ph}", 230.0)
        i = (power_kw * 1000) / (u * cos_phi)
        result[ph] += i

    elif phases == 2:
        key = "".join(sorted(phase_connections))
        u = settings.get(f"voltage_line_{key}", 400.0)
        i = (power_kw * 1000) / (u * cos_phi)
        for ph in phase_connections:
            result[ph] += i

    elif phases == 3:
        u_avg = (
            settings.get("voltage_line_AB", 400.0) +
            settings.get("voltage_line_BC", 400.0) +
            settings.get("voltage_line_AC", 400.0)
        ) / 3.0
        i = (power_kw * 1000) / (math.sqrt(3) * u_avg * cos_phi)
        for ph in phase_connections:
            result[ph] += i

    return result


def _usage_filter(usage, mode):
    """True, если прибор учитывать в данном режиме."""
    if mode == "all":
        return True
    if mode == "temporary":          # Без редких
        return usage != "rare"
    if mode == "constant":           # Только постоянные
        return usage == "constant"
    if mode == "temporary_only":     # Только временные
        return usage == "temporary"
    if mode == "rare_only":          # Только редкие
        return usage == "rare"
    return True


def calc_totals(plan, settings, mode="all"):
    totals = {"A": 0.0, "B": 0.0, "C": 0.0}
    for sock in plan["sockets"]:
        a = sock.get("appliance")
        if not a:
            continue
        usage = a.get("usage", "constant")
        if not _usage_filter(usage, mode):
            continue
        cos_phi = a.get("cos_phi", 1.0)
        cur = current_per_phase(
            a["power_kw"], a["phases"], a["phase_connections"],
            cos_phi, settings
        )
        for ph in "ABC":
            totals[ph] += cur[ph]
    return totals


def calc_phase_breakdown(plan, settings, mode="all"):
    result = {"A": [], "B": [], "C": []}
    for sock in plan["sockets"]:
        a = sock.get("appliance")
        if not a:
            continue
        usage = a.get("usage", "constant")
        if not _usage_filter(usage, mode):
            continue
        cos_phi = a.get("cos_phi", 1.0)
        cur = current_per_phase(
            a["power_kw"], a["phases"], a["phase_connections"],
            cos_phi, settings
        )
        for ph in a["phase_connections"]:
            u = settings.get(f"voltage_{ph}", 230.0)
            power_on_phase = cur[ph] * u / 1000.0
            result[ph].append({
                "name": a["name"],
                "power_kw": power_on_phase,
                "total_power_kw": a["power_kw"],
                "usage": usage,
                "current": cur[ph],
                "cos_phi": cos_phi,
            })
    for ph in "ABC":
        result[ph].sort(key=lambda x: -x["power_kw"])
    return result


def imbalance(totals):
    vals = [totals["A"], totals["B"], totals["C"]]
    mx, mn = max(vals), min(vals)
    avg = sum(vals) / 3
    if avg == 0:
        return 0.0, 0.0
    return (mx - mn) / avg * 100, (mx - mn)


def appliance_color(a, colors):
    if a is None:
        return colors["NONE"]
    conn = "".join(sorted(a["phase_connections"]))
    return colors.get(conn, colors["NONE"])


# ============================================================
# ДИАЛОГ НАСТРОЕК
# ============================================================
class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.title("Параметры расчёта")
        self.geometry("460x480")
        self.result = None
        self.settings = dict(settings)

        frm = tk.Frame(self, padx=15, pady=15)
        frm.pack(fill=tk.BOTH, expand=True)

        tk.Label(frm, text="НАПРЯЖЕНИЕ ФАЗ, В",
                 font=("Arial", 11, "bold")).grid(row=0, column=0,
                                                   columnspan=2, sticky=tk.W, pady=(0, 8))

        self.var_A = tk.StringVar(value=str(self.settings.get("voltage_A", 230)))
        self.var_B = tk.StringVar(value=str(self.settings.get("voltage_B", 230)))
        self.var_C = tk.StringVar(value=str(self.settings.get("voltage_C", 230)))

        tk.Label(frm, text="Фаза A:").grid(row=1, column=0, sticky=tk.W, pady=3)
        tk.Entry(frm, textvariable=self.var_A, width=12).grid(row=1, column=1, sticky=tk.W)

        tk.Label(frm, text="Фаза B:").grid(row=2, column=0, sticky=tk.W, pady=3)
        tk.Entry(frm, textvariable=self.var_B, width=12).grid(row=2, column=1, sticky=tk.W)

        tk.Label(frm, text="Фаза C:").grid(row=3, column=0, sticky=tk.W, pady=3)
        tk.Entry(frm, textvariable=self.var_C, width=12).grid(row=3, column=1, sticky=tk.W)

        tk.Label(frm, text="ЛИНЕЙНОЕ НАПРЯЖЕНИЕ, В",
                 font=("Arial", 11, "bold")).grid(row=4, column=0,
                                                   columnspan=2, sticky=tk.W, pady=(15, 8))

        self.var_AB = tk.StringVar(value=str(self.settings.get("voltage_line_AB", 400)))
        self.var_BC = tk.StringVar(value=str(self.settings.get("voltage_line_BC", 400)))
        self.var_AC = tk.StringVar(value=str(self.settings.get("voltage_line_AC", 400)))

        tk.Label(frm, text="AB:").grid(row=5, column=0, sticky=tk.W, pady=3)
        tk.Entry(frm, textvariable=self.var_AB, width=12).grid(row=5, column=1, sticky=tk.W)

        tk.Label(frm, text="BC:").grid(row=6, column=0, sticky=tk.W, pady=3)
        tk.Entry(frm, textvariable=self.var_BC, width=12).grid(row=6, column=1, sticky=tk.W)

        tk.Label(frm, text="AC:").grid(row=7, column=0, sticky=tk.W, pady=3)
        tk.Entry(frm, textvariable=self.var_AC, width=12).grid(row=7, column=1, sticky=tk.W)

        tk.Label(frm, text="ЛИМИТЫ ВВОДА",
                 font=("Arial", 11, "bold")).grid(row=8, column=0,
                                                   columnspan=2, sticky=tk.W, pady=(15, 8))

        self.var_limit_kw = tk.StringVar(value=str(self.settings.get("input_limit_kw", 15)))
        tk.Label(frm, text="Мощность, кВт:").grid(row=9, column=0, sticky=tk.W, pady=3)
        tk.Entry(frm, textvariable=self.var_limit_kw, width=12).grid(row=9, column=1, sticky=tk.W)

        self.var_limit_a = tk.StringVar(value=str(self.settings.get("input_limit_a", 25)))
        tk.Label(frm, text="Ток, А (на фазу):").grid(row=10, column=0, sticky=tk.W, pady=3)
        tk.Entry(frm, textvariable=self.var_limit_a, width=12).grid(row=10, column=1, sticky=tk.W)

        btn = tk.Frame(self)
        btn.pack(pady=10)
        tk.Button(btn, text="OK", command=self.on_ok, bg="#4CAF50", fg="white",
                  width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Сбросить", command=self.reset,
                  width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Отмена", command=self.destroy,
                  width=10).pack(side=tk.LEFT, padx=5)

        self.transient(parent)
        self.grab_set()

    def reset(self):
        self.var_A.set("230")
        self.var_B.set("230")
        self.var_C.set("230")
        self.var_AB.set("400")
        self.var_BC.set("400")
        self.var_AC.set("400")
        self.var_limit_kw.set("15")
        self.var_limit_a.set("25")

    def on_ok(self):
        try:
            self.result = {
                "voltage_A": float(self.var_A.get()),
                "voltage_B": float(self.var_B.get()),
                "voltage_C": float(self.var_C.get()),
                "voltage_line_AB": float(self.var_AB.get()),
                "voltage_line_BC": float(self.var_BC.get()),
                "voltage_line_AC": float(self.var_AC.get()),
                "input_limit_kw": float(self.var_limit_kw.get()),
                "input_limit_a": float(self.var_limit_a.get()),
            }
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)


# ============================================================
# ДИАЛОГ ЦВЕТОВ ФАЗ
# ============================================================
class PhaseColorsDialog(tk.Toplevel):
    def __init__(self, parent, colors):
        super().__init__(parent)
        self.title("Цвета фаз")
        self.geometry("420x420")
        self.colors = dict(colors)
        self.result = None
        self.swatches = {}

        tk.Label(self, text="Настройка цветов для каждой фазы",
                 font=("Arial", 12, "bold")).pack(pady=8)

        frame = tk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        keys = [("A", "Фаза A"),
                ("B", "Фаза B"),
                ("C", "Фаза C"),
                ("AB", "Двухфазные AB"),
                ("BC", "Двухфазные BC"),
                ("AC", "Двухфазные AC"),
                ("ABC", "Трёхфазные ABC"),
                ("NONE", "Пустая розетка")]

        for i, (key, label) in enumerate(keys):
            tk.Label(frame, text=label, font=("Arial", 10),
                     width=18, anchor=tk.W).grid(row=i, column=0, pady=4)
            sw = tk.Label(frame, text="      ", bg=self.colors[key],
                           relief=tk.SOLID, borderwidth=1, width=8)
            sw.grid(row=i, column=1, padx=5)
            self.swatches[key] = sw
            tk.Button(frame, text="Выбрать цвет...",
                      command=lambda k=key: self.pick(k)
                      ).grid(row=i, column=2, padx=5)

        btn = tk.Frame(self)
        btn.pack(pady=10)
        tk.Button(btn, text="OK", command=self.on_ok, bg="#4CAF50",
                  fg="white", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Сбросить", command=self.reset,
                  width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Отмена", command=self.destroy,
                  width=10).pack(side=tk.LEFT, padx=5)

        self.transient(parent)
        self.grab_set()

    def pick(self, key):
        color = colorchooser.askcolor(color=self.colors[key],
                                       title=f"Цвет для {key}")[1]
        if color:
            self.colors[key] = color
            self.swatches[key].config(bg=color)

    def reset(self):
        self.colors = dict(DEFAULT_PHASE_COLORS)
        for key, sw in self.swatches.items():
            sw.config(bg=self.colors[key])

    def on_ok(self):
        self.result = dict(self.colors)
        self.destroy()


# ============================================================
# ДИАЛОГ: ПРИБОР НА РОЗЕТКЕ
# ============================================================
class ApplianceDialog(tk.Toplevel):
    def __init__(self, parent, templates, socket):
        super().__init__(parent)
        self.title("Прибор на розетке")
        self.geometry("540x640")
        self.result = None
        self.templates = templates
        self.socket = socket

        tk.Label(self, text="Шаблоны приборов:",
                 font=("Arial", 11, "bold")).pack(pady=5)
        self.template_list = tk.Listbox(self, height=10, font=("Arial", 10))
        self.template_list.pack(fill=tk.X, padx=10)
        for name in sorted(templates.keys()):
            t = templates[name]
            self.template_list.insert(
                tk.END,
                f"{name} — {t['power_kw']} кВт, {t['phases']}ф, "
                f"cosφ={t.get('cos_phi', 1.0)}, {usage_to_ru(t['usage'])}")
        self.template_list.bind("<<ListboxSelect>>", self.on_template_select)

        frm = tk.Frame(self)
        frm.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frm, text="Название:").grid(row=0, column=0, sticky=tk.W)
        self.name_var = tk.StringVar()
        tk.Entry(frm, textvariable=self.name_var, width=25).grid(row=0, column=1, sticky=tk.W)

        tk.Label(frm, text="Мощность (кВт):").grid(row=1, column=0, sticky=tk.W)
        self.power_var = tk.StringVar()
        tk.Entry(frm, textvariable=self.power_var, width=25).grid(row=1, column=1, sticky=tk.W)

        tk.Label(frm, text="Число фаз (1/2/3):").grid(row=2, column=0, sticky=tk.W)
        self.phases_var = tk.StringVar(value="1")
        tk.Entry(frm, textvariable=self.phases_var, width=25).grid(row=2, column=1, sticky=tk.W)

        tk.Label(frm, text="cos φ:").grid(row=3, column=0, sticky=tk.W)
        self.cos_phi_var = tk.StringVar(value="1.0")
        tk.Entry(frm, textvariable=self.cos_phi_var, width=25).grid(row=3, column=1, sticky=tk.W)

        tk.Label(frm, text="Режим:").grid(row=4, column=0, sticky=tk.W)
        self.usage_var = tk.StringVar(value=usage_to_ru("temporary"))
        ttk.Combobox(frm, textvariable=self.usage_var,
                     values=USAGE_RU_LIST, state="readonly",
                     width=22).grid(row=4, column=1, sticky=tk.W)

        tk.Label(frm, text="Фазы подключения:").grid(row=5, column=0, sticky=tk.W)
        self.phases_conn_var = tk.StringVar(value="A")
        ttk.Combobox(frm, textvariable=self.phases_conn_var,
                     values=["A", "B", "C", "AB", "BC", "AC", "ABC"],
                     state="readonly",
                     width=22).grid(row=5, column=1, sticky=tk.W)

        btn = tk.Frame(self)
        btn.pack(pady=10)
        tk.Button(btn, text="OK", command=self.on_ok, bg="#4CAF50", fg="white",
                  width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Отмена", command=self.destroy,
                  width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Снять прибор", command=self.on_remove,
                  bg="#E53935", fg="white", width=14).pack(side=tk.LEFT, padx=5)

        if socket.get("appliance"):
            a = socket["appliance"]
            self.name_var.set(a["name"])
            self.power_var.set(str(a["power_kw"]))
            self.phases_var.set(str(a["phases"]))
            self.cos_phi_var.set(str(a.get("cos_phi", 1.0)))
            self.usage_var.set(usage_to_ru(a["usage"]))
            self.phases_conn_var.set("".join(a["phase_connections"]))

        self.transient(parent)
        self.grab_set()

    def on_template_select(self, event):
        sel = self.template_list.curselection()
        if not sel:
            return
        name = self.template_list.get(sel[0]).split(" — ")[0]
        t = self.templates[name]
        self.name_var.set(name)
        self.power_var.set(str(t["power_kw"]))
        self.phases_var.set(str(t["phases"]))
        self.cos_phi_var.set(str(t.get("cos_phi", 1.0)))
        self.usage_var.set(usage_to_ru(t["usage"]))
        if t["phases"] == 1:
            self.phases_conn_var.set("A")
        elif t["phases"] == 2:
            self.phases_conn_var.set("AB")
        else:
            self.phases_conn_var.set("ABC")

    def on_ok(self):
        try:
            name = self.name_var.get().strip()
            if not name:
                raise ValueError("Введите название")
            power = float(self.power_var.get())
            phases = int(self.phases_var.get())
            if phases not in (1, 2, 3):
                raise ValueError("Фазы: 1, 2 или 3")
            cos_phi = float(self.cos_phi_var.get())
            if not (0 < cos_phi <= 1):
                raise ValueError("cos φ должен быть от 0 до 1")
            usage = usage_to_key(self.usage_var.get())
            conn = self.phases_conn_var.get().upper()
            if phases == 1 and conn not in ("A", "B", "C"):
                raise ValueError("Для 1 фазы: A, B или C")
            if phases == 2 and conn not in ("AB", "BC", "AC", "BA", "CB", "CA"):
                raise ValueError("Для 2 фаз: AB, BC или AC")
            if phases == 3:
                conn = "ABC"
            self.result = {
                "name": name, "power_kw": power, "phases": phases,
                "usage": usage, "phase_connections": list(conn),
                "cos_phi": cos_phi,
            }
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)

    def on_remove(self):
        self.result = "REMOVE"
        self.destroy()


# ============================================================
# ДИАЛОГ РЕДАКТИРОВАНИЯ ШАБЛОНА
# ============================================================
class TemplateEditDialog(tk.Toplevel):
    def __init__(self, parent, name="", template=None):
        super().__init__(parent)
        self.title("Шаблон прибора")
        self.geometry("400x320")
        self.result = None
        self.template = template or {"power_kw": 1.0, "phases": 1,
                                      "usage": "temporary", "cos_phi": 1.0}

        frm = tk.Frame(self, padx=15, pady=15)
        frm.pack(fill=tk.BOTH, expand=True)

        tk.Label(frm, text="Название:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.name_var = tk.StringVar(value=name)
        tk.Entry(frm, textvariable=self.name_var, width=25).grid(row=0, column=1, pady=4)

        tk.Label(frm, text="Мощность (кВт):").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.power_var = tk.StringVar(value=str(self.template["power_kw"]))
        tk.Entry(frm, textvariable=self.power_var, width=25).grid(row=1, column=1, pady=4)

        tk.Label(frm, text="Число фаз:").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.phases_var = tk.StringVar(value=str(self.template["phases"]))
        ttk.Combobox(frm, textvariable=self.phases_var,
                     values=["1", "2", "3"], state="readonly",
                     width=22).grid(row=2, column=1, pady=4)

        tk.Label(frm, text="cos φ:").grid(row=3, column=0, sticky=tk.W, pady=4)
        self.cos_phi_var = tk.StringVar(value=str(self.template.get("cos_phi", 1.0)))
        tk.Entry(frm, textvariable=self.cos_phi_var, width=25).grid(row=3, column=1, pady=4)

        tk.Label(frm, text="Режим:").grid(row=4, column=0, sticky=tk.W, pady=4)
        self.usage_var = tk.StringVar(value=usage_to_ru(self.template["usage"]))
        ttk.Combobox(frm, textvariable=self.usage_var,
                     values=USAGE_RU_LIST, state="readonly",
                     width=22).grid(row=4, column=1, pady=4)

        btn = tk.Frame(self)
        btn.pack(pady=10)
        tk.Button(btn, text="OK", command=self.on_ok, bg="#4CAF50", fg="white",
                  width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Отмена", command=self.destroy,
                  width=10).pack(side=tk.LEFT, padx=5)

        self.transient(parent)
        self.grab_set()

    def on_ok(self):
        try:
            name = self.name_var.get().strip()
            if not name:
                raise ValueError("Введите название")
            power = float(self.power_var.get())
            phases = int(self.phases_var.get())
            cos_phi = float(self.cos_phi_var.get())
            if not (0 < cos_phi <= 1):
                raise ValueError("cos φ должен быть от 0 до 1")
            usage = usage_to_key(self.usage_var.get())
            self.result = {
                "name": name,
                "template": {
                    "power_kw": power, "phases": phases,
                    "usage": usage, "cos_phi": cos_phi,
                }
            }
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)


# ============================================================
# ДИАЛОГ СПИСКА ШАБЛОНОВ
# ============================================================
class TemplatesDialog(tk.Toplevel):
    def __init__(self, parent, templates):
        super().__init__(parent)
        self.title("Шаблоны приборов")
        self.geometry("780x520")
        self.templates = templates

        tk.Label(self, text="Шаблоны приборов",
                 font=("Arial", 12, "bold")).pack(pady=5)

        self.tree = ttk.Treeview(self, columns=("name", "power", "phases", "cos", "usage"),
                                  show="headings", height=15)
        self.tree.heading("name", text="Название")
        self.tree.heading("power", text="Мощность, кВт")
        self.tree.heading("phases", text="Фаз")
        self.tree.heading("cos", text="cos φ")
        self.tree.heading("usage", text="Режим")
        self.tree.column("name", width=200)
        self.tree.column("power", width=110, anchor=tk.CENTER)
        self.tree.column("phases", width=60, anchor=tk.CENTER)
        self.tree.column("cos", width=70, anchor=tk.CENTER)
        self.tree.column("usage", width=150, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.refresh()

        btn = tk.Frame(self)
        btn.pack(pady=5)
        tk.Button(btn, text="Добавить", command=self.add, width=12).pack(side=tk.LEFT, padx=3)
        tk.Button(btn, text="Редактировать", command=self.edit, width=14).pack(side=tk.LEFT, padx=3)
        tk.Button(btn, text="Удалить", command=self.remove, width=12).pack(side=tk.LEFT, padx=3)
        tk.Button(btn, text="Сохранить", command=self.save, width=12,
                  bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=3)

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for name in sorted(self.templates.keys()):
            t = self.templates[name]
            self.tree.insert("", tk.END, values=(
                name, f"{t['power_kw']:.2f}",
                t["phases"], f"{t.get('cos_phi', 1.0):.2f}",
                usage_to_ru(t["usage"])
            ))

    def add(self):
        dlg = TemplateEditDialog(self, name="", template=None)
        self.wait_window(dlg)
        if dlg.result:
            name = dlg.result["name"]
            self.templates[name] = dlg.result["template"]
            self.refresh()

    def edit(self):
        sel = self.tree.selection()
        if not sel:
            return
        name = self.tree.item(sel[0])["values"][0]
        dlg = TemplateEditDialog(self, name=name, template=self.templates[name])
        self.wait_window(dlg)
        if dlg.result:
            new_name = dlg.result["name"]
            if name != new_name and name in self.templates:
                del self.templates[name]
            self.templates[new_name] = dlg.result["template"]
            self.refresh()

    def remove(self):
        sel = self.tree.selection()
        if not sel:
            return
        name = self.tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Удалить", f"Удалить '{name}'?", parent=self):
            del self.templates[name]
            self.refresh()

    def save(self):
        save_json(TEMPLATES_FILE, self.templates)
        messagebox.showinfo("Готово", "Шаблоны сохранены.", parent=self)


# ============================================================
# ВСПЛЫВАЮЩАЯ ПОДСКАЗКА
# ============================================================
class HoverTip:
    def __init__(self, widget):
        self.widget = widget
        self.tip = None
        self.hide_id = None

    def show(self, x, y, text):
        self.cancel_hide()
        if self.tip is not None:
            self.tip.destroy()
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=text, justify=tk.LEFT,
                 background="#FFFFE0", relief=tk.SOLID, borderwidth=1,
                 font=("Arial", 9)).pack()

    def hide(self):
        self.cancel_hide()
        self.hide_id = self.widget.after(300, self._do_hide)

    def cancel_hide(self):
        if self.hide_id is not None:
            self.widget.after_cancel(self.hide_id)
            self.hide_id = None

    def _do_hide(self):
        if self.tip is not None:
            self.tip.destroy()
            self.tip = None


# ============================================================
# ПРАВАЯ ПАНЕЛЬ РАСЧЁТА
# ============================================================
class RightPanel(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#FAFAFA")
        self.app = app

        tk.Label(self, text="РАСЧЁТ ПО ФАЗАМ",
                 font=("Arial", 10, "bold"),
                 bg="#37474F", fg="white").pack(fill=tk.X)

        # Режим
        mode_frame = tk.Frame(self, bg="#FAFAFA")
        mode_frame.pack(fill=tk.X, padx=3, pady=3)
        tk.Label(mode_frame, text="Режим:", bg="#FAFAFA",
                 font=("Arial", 8, "bold")).pack(anchor=tk.W)
        self.mode_var = tk.StringVar(value="all")
        for key, text in [("all", "Всё"),
                           ("temporary", "Без редких"),
                           ("constant", "Только постоянные"),
                           ("temporary_only", "Только временные"),
                           ("rare_only", "Только редкие")]:
            tk.Radiobutton(mode_frame, text=text, variable=self.mode_var,
                           value=key, bg="#FAFAFA", font=("Arial", 8),
                           anchor=tk.W, command=self.refresh
                           ).pack(fill=tk.X)

        # Прокрутка
        self.canvas = tk.Canvas(self, bg="#FAFAFA", highlightthickness=0)
        self.scroll = tk.Scrollbar(self, orient=tk.VERTICAL,
                                    command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.phases_frame = tk.Frame(self.canvas, bg="#FAFAFA")
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.phases_frame, anchor=tk.NW
        )
        self.phases_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )

        self.summary_label = tk.Label(self, text="", bg="#FAFAFA",
                                       font=("Arial", 9, "italic"),
                                       justify=tk.LEFT, anchor=tk.W,
                                       wraplength=280)
        self.summary_label.pack(fill=tk.X, padx=4, pady=4)

        self.refresh()

    def refresh(self):
        for w in self.phases_frame.winfo_children():
            w.destroy()

        colors = self.app.phase_colors
        settings = self.app.settings
        mode = self.mode_var.get()
        totals = calc_totals(self.app.plan, settings, mode)
        breakdown = calc_phase_breakdown(self.app.plan, settings, mode)

        max_i = max(totals["A"], totals["B"], totals["C"], 0.1)
        panel_w = max(self.canvas.winfo_width(), 240)
        limit_a = settings.get("input_limit_a", 25.0)

        for ph in "ABC":
            color = colors[ph]
            u = settings.get(f"voltage_{ph}", 230.0)
            frame = tk.LabelFrame(self.phases_frame,
                                   text=f"Фаза {ph}  ({u:.0f} В)",
                                   font=("Arial", 9, "bold"),
                                   fg=color, bg="#FAFAFA",
                                   labelanchor=tk.NW,
                                   padx=2, pady=2)
            frame.pack(fill=tk.X, padx=3, pady=3)

            header = tk.Frame(frame, bg="#FAFAFA")
            header.pack(fill=tk.X, padx=2, pady=1)
            tk.Label(header, text=f"{totals[ph]:.1f} А",
                     font=("Arial", 9, "bold"), fg=color,
                     bg="#FAFAFA").pack(side=tk.LEFT)
            tk.Label(header,
                     text=f" {totals[ph] * u / 1000:.2f} кВт",
                     font=("Arial", 8), bg="#FAFAFA").pack(side=tk.LEFT)
            if totals[ph] > limit_a:
                tk.Label(header, text=" ⚠", fg="#B71C1C",
                         bg="#FAFAFA", font=("Arial", 10, "bold")).pack(side=tk.RIGHT)

            # Полоса загрузки
            bar_bg = tk.Frame(frame, bg="#E0E0E0", height=4)
            bar_bg.pack(fill=tk.X, padx=3, pady=(0, 2))
            ratio = totals[ph] / max_i if max_i > 0 else 0
            bar_width = max(1, int((panel_w - 20) * ratio))
            bar_fill = tk.Frame(bar_bg, bg=color, height=4)
            bar_fill.place(x=0, y=0, width=bar_width, height=4)

            if not breakdown[ph]:
                tk.Label(frame, text="(нет приборов)", bg="#FAFAFA",
                         fg="#999", font=("Arial", 8, "italic")
                         ).pack(anchor=tk.W, padx=3)
            else:
                for item in breakdown[ph]:
                    row = tk.Frame(frame, bg="#FAFAFA")
                    row.pack(fill=tk.X, padx=2)
                    tk.Label(row, text="•", bg="#FAFAFA",
                             fg=color, font=("Arial", 8)
                             ).pack(side=tk.LEFT)
                    tk.Label(row, text=item['name'],
                             bg="#FAFAFA", font=("Arial", 8),
                             anchor=tk.W).pack(side=tk.LEFT)
                    tk.Label(row,
                             text=f"{item['power_kw']:.2f}кВт/{item['current']:.1f}А",
                             bg="#FAFAFA", font=("Arial", 7),
                             fg="#555").pack(side=tk.RIGHT)

        # Подвал — перекос и суммарно по режимам
        pct, diff = imbalance(totals)
        total_kw = sum(totals[ph] * settings.get(f"voltage_{ph}", 230.0)
                       for ph in "ABC") / 1000.0

        t_const = calc_totals(self.app.plan, settings, "constant")
        t_temp = calc_totals(self.app.plan, settings, "temporary_only")
        t_rare = calc_totals(self.app.plan, settings, "rare_only")

        def _sum_kw(t):
            return sum(t[ph] * settings.get(f"voltage_{ph}", 230.0)
                       for ph in "ABC") / 1000.0

        lines = []
        if pct > 15:
            lines.append(f"⚠ Сильный перекос: {pct:.1f}%")
        elif pct > 5:
            lines.append(f"~ Небольшой перекос: {pct:.1f}%")
        else:
            lines.append(f"✓ Перекос: {pct:.1f}%")
        lines.append(f"Суммарно: {total_kw:.2f} кВт")
        lines.append(f"  [П] Постоянные: {_sum_kw(t_const):.2f} кВт")
        lines.append(f"  [В] Временные:  {_sum_kw(t_temp):.2f} кВт")
        lines.append(f"  [Р] Редкие:     {_sum_kw(t_rare):.2f} кВт")
        self.summary_label.config(
            text="\n".join(lines),
            fg="#B71C1C" if pct > 15 else "#33691E"
        )


# ============================================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ============================================================
class PowerPlanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("План щита — распределение по 3 фазам")
        self.root.geometry("1600x900")

        self.templates = load_json(TEMPLATES_FILE, DEFAULT_TEMPLATES.copy())
        self.phase_colors = load_json(PHASE_COLORS_FILE, dict(DEFAULT_PHASE_COLORS))
        self.settings = load_json(SETTINGS_FILE, dict(DEFAULT_SETTINGS))

        for k, v in DEFAULT_PHASE_COLORS.items():
            if k not in self.phase_colors:
                self.phase_colors[k] = v
        for k, v in DEFAULT_SETTINGS.items():
            if k not in self.settings:
                self.settings[k] = v

        self.plan = {
            "walls": [],
            "sockets": [],
            "photo_path": None,
            "room_width": 1400,
            "room_height": 900,
        }
        self.current_file = None
        self.photo_img = None
        self.photo_size = (0, 0)

        self.socket_diameter = 12
        self.mode = "select"
        self.wall_start = None
        self.selected_socket = None
        self.dragging = False
        self.drag_offset = (0, 0)
        self.undo_stack = []

        self._build_ui()
        self._draw_all()

    def _build_ui(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Новый план", command=self.new_plan)
        file_menu.add_command(label="Открыть план...", command=self.open_plan)
        file_menu.add_command(label="Сохранить план", command=self.save_plan)
        file_menu.add_command(label="Сохранить как...", command=self.save_plan_as)
        file_menu.add_separator()
        file_menu.add_command(label="Загрузить фото (JPG/PNG)...", command=self.load_photo)
        file_menu.add_command(label="Убрать фото", command=self.clear_photo)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Отменить последнее действие",
                               command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_separator()
        edit_menu.add_command(label="Параметры расчёта (напряжение, лимиты)...",
                               command=self.edit_settings)
        edit_menu.add_command(label="Цвета фаз...",
                               command=self.edit_phase_colors)
        edit_menu.add_command(label="Редактировать шаблоны",
                               command=self.open_templates)
        menubar.add_cascade(label="Настройки", menu=edit_menu)

        self.root.config(menu=menubar)

        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Delete>", lambda e: self.delete_selected())
        self.root.bind("<BackSpace>", lambda e: self.delete_selected())

        # Панель инструментов
        toolbar = tk.Frame(self.root, bg="#ECEFF1", height=44)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Label(toolbar, text="Режим:", bg="#ECEFF1",
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)

        self.mode_var = tk.StringVar(value="select")
        for text, val in [("Выбор", "select"),
                           ("Стена гориз.", "wall_h"),
                           ("Стена верт.", "wall_v"),
                           ("Розетка", "place_socket")]:
            tk.Radiobutton(toolbar, text=text, variable=self.mode_var,
                           value=val, bg="#ECEFF1",
                           command=lambda: self.set_mode(self.mode_var.get())
                           ).pack(side=tk.LEFT, padx=2)

        tk.Label(toolbar, text="  Диаметр:", bg="#ECEFF1").pack(side=tk.LEFT, padx=5)
        self.diameter_var = tk.IntVar(value=self.socket_diameter)
        tk.Spinbox(toolbar, from_=4, to=40, width=4,
                   textvariable=self.diameter_var,
                   command=self.update_diameter).pack(side=tk.LEFT)
        self.diameter_var.trace_add("write", lambda *a: self.update_diameter())

        tk.Button(toolbar, text="Отменить", command=self.undo,
                  bg="#FFB300").pack(side=tk.RIGHT, padx=5)
        tk.Button(toolbar, text="Удалить выделенное", command=self.delete_selected,
                  bg="#E53935", fg="white").pack(side=tk.RIGHT, padx=5)

        # Основная область
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Правая панель (фикс. ширина 320)
        right_frame = tk.Frame(main_frame, width=320, bg="#FAFAFA")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_frame.pack_propagate(False)

        self.right_panel = RightPanel(right_frame, self)
        self.right_panel.pack(fill=tk.BOTH, expand=True)

        # Левая часть — холст
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.h_scroll = tk.Scrollbar(left_frame, orient=tk.HORIZONTAL)
        self.v_scroll = tk.Scrollbar(left_frame, orient=tk.VERTICAL)
        self.canvas = tk.Canvas(left_frame, bg="white",
                                 xscrollcommand=self.h_scroll.set,
                                 yscrollcommand=self.v_scroll.set)
        self.h_scroll.config(command=self.canvas.xview)
        self.v_scroll.config(command=self.canvas.yview)

        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Leave>", lambda e: self.hover.hide())

        self.hover = HoverTip(self.canvas)

        # Статус
        self.status = tk.Label(self.root, text="Готово", anchor=tk.W,
                                bg="#CFD8DC", font=("Arial", 10))
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def set_mode(self, mode):
        self.mode = mode
        self.mode_var.set(mode)
        self.wall_start = None
        self.status.config(text=f"Режим: {mode}")

    def update_diameter(self):
        try:
            self.socket_diameter = int(self.diameter_var.get())
        except Exception:
            pass

    def push_undo(self, snapshot):
        self.undo_stack.append(copy.deepcopy(snapshot))
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            self.status.config(text="Нет действий для отмены")
            return
        prev = self.undo_stack.pop()
        photo_path = self.plan.get("photo_path")
        self.plan = prev
        self.plan["photo_path"] = photo_path
        self.selected_socket = None
        self.dragging = False
        self._load_photo_from_path()
        self._draw_all()
        self.right_panel.refresh()
        self.status.config(text="Действие отменено")

    def _load_photo_from_path(self):
        self.photo_img = None
        path = self.plan.get("photo_path")
        if not path or not os.path.exists(path):
            return
        try:
            if PIL_AVAILABLE:
                img = Image.open(path)
                self.photo_img = ImageTk.PhotoImage(img)
                self.photo_size = (img.width, img.height)
            else:
                self.photo_img = tk.PhotoImage(file=path)
                self.photo_size = (self.photo_img.width(), self.photo_img.height())
        except Exception as e:
            print("Ошибка загрузки фото:", e)
            self.photo_img = None

    def _draw_all(self):
        self.canvas.delete("all")

        if self.photo_img is not None:
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_img)
            w, h = self.photo_size
            self.canvas.config(scrollregion=(0, 0, w, h))
        else:
            w = self.plan.get("room_width", 1400)
            h = self.plan.get("room_height", 900)
            self.canvas.config(scrollregion=(0, 0, w, h))

        for wall in self.plan["walls"]:
            x1, y1, x2, y2 = wall
            self.canvas.create_line(x1, y1, x2, y2, fill="#37474F", width=5)

        for i, sock in enumerate(self.plan["sockets"]):
            self._draw_socket(i, sock)

        if self.wall_start is not None:
            x, y = self.wall_start
            self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4,
                                     outline="#B71C1C", width=2)

    def _draw_socket(self, idx, sock):
        x, y = sock["x"], sock["y"]
        r = sock.get("diameter", 12) / 2
        a = sock.get("appliance")
        color = appliance_color(a, self.phase_colors)

        self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                 fill=color, outline="#263238", width=1,
                                 tags=f"socket_{idx}")

        if a:
            short = a["name"][:3]
            self.canvas.create_text(x, y - r - 6, text=short,
                                     font=("Arial", 7), fill="#000",
                                     tags=f"socket_{idx}")

        if self.selected_socket == idx:
            self.canvas.create_oval(x - r - 4, y - r - 4,
                                     x + r + 4, y + r + 4,
                                     outline="#FF6F00", width=2,
                                     tags=f"socket_{idx}")

    def _find_socket(self, x, y):
        best = None
        best_dist = None
        for i, sock in enumerate(self.plan["sockets"]):
            r = sock.get("diameter", 12) / 2
            dx = x - sock["x"]
            dy = y - sock["y"]
            d2 = dx * dx + dy * dy
            if d2 <= r * r:
                if best_dist is None or d2 < best_dist:
                    best = i
                    best_dist = d2
        return best

    def on_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        if self.mode == "place_socket":
            self.push_undo(self.plan)
            sock = {"x": x, "y": y, "diameter": self.socket_diameter, "appliance": None}
            self.plan["sockets"].append(sock)
            self.selected_socket = len(self.plan["sockets"]) - 1
            self._draw_all()
            self.right_panel.refresh()
            return

        if self.mode in ("wall_h", "wall_v"):
            if self.wall_start is None:
                self.wall_start = (x, y)
            else:
                x1, y1 = self.wall_start
                if self.mode == "wall_h":
                    y2 = y1
                    x2 = x
                else:
                    x2 = x1
                    y2 = y
                self.push_undo(self.plan)
                self.plan["walls"].append([x1, y1, x2, y2])
                self.wall_start = None
                self._draw_all()
            return

        idx = self._find_socket(x, y)
        if idx is not None:
            self.selected_socket = idx
            self.dragging = True
            sock = self.plan["sockets"][idx]
            self.drag_offset = (x - sock["x"], y - sock["y"])
            self._draw_all()

    def on_drag(self, event):
        if not self.dragging or self.selected_socket is None:
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        sock = self.plan["sockets"][self.selected_socket]
        sock["x"] = x - self.drag_offset[0]
        sock["y"] = y - self.drag_offset[1]
        self._draw_all()

    def on_release(self, event):
        self.dragging = False

    def on_right_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        idx = self._find_socket(x, y)
        if idx is None:
            return
        self.selected_socket = idx
        self._show_socket_menu(idx, event.x_root, event.y_root)

    def _show_socket_menu(self, idx, x_root, y_root):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Назначить прибор...",
                          command=lambda: self.edit_appliance(idx))
        menu.add_command(label="Удалить розетку",
                          command=lambda: self.delete_socket(idx))
        menu.tk_popup(x_root, y_root)

    def edit_appliance(self, idx):
        sock = self.plan["sockets"][idx]
        self.push_undo(self.plan)
        dlg = ApplianceDialog(self.root, self.templates, sock)
        self.root.wait_window(dlg)
        if dlg.result == "REMOVE":
            sock["appliance"] = None
        elif dlg.result:
            sock["appliance"] = dlg.result
        self._draw_all()
        self.right_panel.refresh()

    def delete_socket(self, idx):
        self.push_undo(self.plan)
        del self.plan["sockets"][idx]
        self.selected_socket = None
        self._draw_all()
        self.right_panel.refresh()
        self.status.config(text=f"Розетка {idx + 1} удалена")

    def delete_selected(self):
        if self.selected_socket is None:
            self.status.config(text="Ничего не выбрано")
            return
        self.delete_socket(self.selected_socket)

    def on_motion(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        idx = self._find_socket(x, y)
        if idx is None:
            self.status.config(text="Готово")
            self.hover.hide()
            return
        sock = self.plan["sockets"][idx]
        a = sock.get("appliance")
        if a:
            conn = "+".join(a["phase_connections"])
            cos_phi = a.get("cos_phi", 1.0)
            i = current_per_phase(a["power_kw"], a["phases"],
                                   a["phase_connections"], cos_phi, self.settings)
            i_str = " ".join(f"{ph}={i[ph]:.1f}A" for ph in a["phase_connections"])
            text = (f"Розетка {idx + 1}\n"
                    f"Прибор: {a['name']}\n"
                    f"Мощность: {a['power_kw']} кВт\n"
                    f"Фазы: {conn}\n"
                    f"cos φ: {cos_phi}\n"
                    f"Режим: {usage_to_ru(a['usage'])}\n"
                    f"Ток: {i_str}")
            self.status.config(
                text=f"Розетка {idx+1}: {a['name']} | {a['power_kw']} кВт | "
                     f"фазы {conn} | cosφ={cos_phi}"
            )
        else:
            text = f"Розетка {idx + 1}\nПусто"
            self.status.config(text=f"Розетка {idx + 1}: пусто")
        self.hover.show(event.x_root + 15, event.y_root + 15, text)

    # ============================================================
    # ФАЙЛЫ
    # ============================================================
    def new_plan(self):
        if not messagebox.askyesno("Новый план", "Очистить текущий план?"):
            return
        self.push_undo(self.plan)
        self.plan = {"walls": [], "sockets": [], "photo_path": None,
                     "room_width": 1400, "room_height": 900}
        self.current_file = None
        self.photo_img = None
        self.selected_socket = None
        self._draw_all()
        self.right_panel.refresh()

    def save_plan(self):
        if self.current_file is None:
            self.save_plan_as()
            return
        save_json(self.current_file, self.plan)
        self.status.config(text=f"Сохранено: {self.current_file}")

    def save_plan_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Power plan", "*.json")],
            initialfile="plan.json"
        )
        if not path:
            return
        save_json(path, self.plan)
        self.current_file = path
        self.status.config(text=f"Сохранено: {path}")

    def open_plan(self):
        path = filedialog.askopenfilename(filetypes=[("Power plan", "*.json")])
        if not path:
            return
        data = load_json(path, None)
        if not data:
            return
        self.plan = data
        self.current_file = path
        self.selected_socket = None
        self._load_photo_from_path()
        self._draw_all()
        self.right_panel.refresh()
        self.status.config(text=f"Загружено: {path}")

    def load_photo(self):
        if not PIL_AVAILABLE:
            messagebox.showwarning(
                "Pillow не установлен",
                "Для загрузки JPG/PNG установите Pillow:\n\npip install pillow"
            )
            return
        path = filedialog.askopenfilename(
            filetypes=[("Изображения", "*.jpg *.jpeg *.png"),
                        ("Все файлы", "*.*")]
        )
        if not path:
            return
        try:
            img = Image.open(path)
            self.photo_img = ImageTk.PhotoImage(img)
            self.photo_size = (img.width, img.height)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")
            return
        self.plan["photo_path"] = path
        self._draw_all()
        self.status.config(text=f"Фото: {os.path.basename(path)}")

    def clear_photo(self):
        self.plan["photo_path"] = None
        self.photo_img = None
        self._draw_all()

    # ============================================================
    # НАСТРОЙКИ
    # ============================================================
    def open_templates(self):
        dlg = TemplatesDialog(self.root, self.templates)
        self.root.wait_window(dlg)
        self.templates = load_json(TEMPLATES_FILE, self.templates)

    def edit_phase_colors(self):
        dlg = PhaseColorsDialog(self.root, self.phase_colors)
        self.root.wait_window(dlg)
        if dlg.result:
            self.phase_colors = dlg.result
            save_json(PHASE_COLORS_FILE, self.phase_colors)
            self._draw_all()
            self.right_panel.refresh()

    def edit_settings(self):
        dlg = SettingsDialog(self.root, self.settings)
        self.root.wait_window(dlg)
        if dlg.result:
            self.settings = dlg.result
            save_json(SETTINGS_FILE, self.settings)
            self.right_panel.refresh()


# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = PowerPlanApp(root)
    root.mainloop()
