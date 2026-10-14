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
# КОНСТАНТЫ ПЛАНА ДОМА
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

SEASON_RU = {
    "all": "Круглый год",
    "winter": "Зима",
    "summer": "Лето",
}
SEASON_RU_LIST = list(SEASON_RU.values())

SWITCH_ON_COLOR = "#FFEB3B"
SWITCH_OFF_COLOR = "#9E9E9E"
WIRE_COLOR = "#000000"
WIRE_SELECTED_COLOR = "#FF6F00"
GLOW_COLOR = "#FFD54F"
DISABLED_COLOR = "#CFD8DC"

MIN_SCALE = 0.2
MAX_SCALE = 5.0
ZOOM_STEP = 1.15

TEMPLATES_FILE = "appliance_templates.json"
PHASE_COLORS_FILE = "phase_colors.json"
SETTINGS_FILE = "power_settings.json"


# ============================================================
# КОНСТАНТЫ ЩИТА
# ============================================================
CABLE_TYPES = {
    "L1": {"color": "#E53935", "label": "L1"},
    "L2": {"color": "#43A047", "label": "L2"},
    "L3": {"color": "#000000", "label": "L3"},
    "N":  {"color": "#1E88E5", "label": "N"},
    "PE": {"color": "#FDD835", "label": "PE"},
}
CABLE_SELECTED_COLOR = "#FF6F00"
GRAB_TOLERANCE = 25

BREAKER_TEMPLATES_FILE = "breaker_templates.json"
SHIELD_FILE_DEFAULT = "shield.json"

BREAKER_ON_FILL = "#C8E6C9"
BREAKER_OFF_FILL = "#F8BBD0"
BREAKER_BORDER = "#263238"

NOMINALS = [6, 10, 13, 16, 20, 25, 32, 40, 50, 63]
LEAKS = [10, 30, 100, 300, 500]
CHARS = ["B", "C", "D"]

BUS_CONTACT_STEP = 30
BUS_PADDING = 20
BUS_HEIGHT = 20
CABLE_OVERLAP_SHIFT = 5

TEMPLATE_GROUPS = {
    "auto": "Автоматы",
    "rcd": "УЗО",
    "diff": "Диффавтоматы",
    "main": "Рубильники",
    "stabilizer": "Стабилизаторы",
    "meter": "Счётчики",
    "out": "Выводные",
    "bus": "Шины",
}

DIALOG_STATE = {
    "poles": "",
    "nominal": "",
    "leak": "",
    "group": "Все",
    "search": "",
    "group_open": {},
}


# ============================================================
# ШАБЛОНЫ
# ============================================================
DEFAULT_TEMPLATES = {
    "Чайник":         {"power_kw": 2.0,  "phases": 1, "usage": "temporary", "season": "all"},
    "Микроволновка":  {"power_kw": 1.0,  "phases": 1, "usage": "temporary", "season": "all"},
    "Холодильник":    {"power_kw": 0.3,  "phases": 1, "usage": "constant",  "season": "all"},
    "Стиральная машина": {"power_kw": 2.2, "phases": 1, "usage": "temporary", "season": "all"},
    "Посудомоечная":  {"power_kw": 2.0,  "phases": 1, "usage": "temporary", "season": "all"},
    "Утюг":           {"power_kw": 2.2,  "phases": 1, "usage": "temporary", "season": "all"},
    "Пылесос":        {"power_kw": 1.5,  "phases": 1, "usage": "temporary", "season": "all"},
    "Телевизор":      {"power_kw": 0.15, "phases": 1, "usage": "constant",  "season": "all"},
    "Компьютер":      {"power_kw": 0.3,  "phases": 1, "usage": "constant",  "season": "all"},
    "Освещение":      {"power_kw": 0.5,  "phases": 1, "usage": "constant",  "season": "all"},
    "Кондиционер":    {"power_kw": 2.5,  "phases": 1, "usage": "temporary", "season": "summer"},
    "Вентилятор":     {"power_kw": 0.05, "phases": 1, "usage": "temporary", "season": "summer"},
    "Насос полива":   {"power_kw": 0.8,  "phases": 1, "usage": "rare",      "season": "summer"},
    "Обогреватель":   {"power_kw": 2.0,  "phases": 1, "usage": "temporary", "season": "winter"},
    "Тёплый пол":     {"power_kw": 1.5,  "phases": 1, "usage": "constant",  "season": "winter"},
    "Бойлер":         {"power_kw": 2.0,  "phases": 1, "usage": "rare",      "season": "all"},
    "Насос":          {"power_kw": 1.1,  "phases": 1, "usage": "rare",      "season": "all"},
    "Котёл":          {"power_kw": 12.0, "phases": 3, "usage": "constant",  "season": "winter"},
    "Электроплита":   {"power_kw": 6.0,  "phases": 3, "usage": "temporary", "season": "all"},
    "Сауна":          {"power_kw": 4.5,  "phases": 3, "usage": "rare",      "season": "winter"},
    "Зарядка авто":   {"power_kw": 7.0,  "phases": 3, "usage": "rare",      "season": "all"},
    "Настольная лампа": {"power_kw": 0.06, "phases": 1, "usage": "temporary", "season": "all"},
    "Зарядка телефона": {"power_kw": 0.01, "phases": 1, "usage": "temporary", "season": "all"},
    "Лампочка":       {"power_kw": 0.06, "phases": 1, "usage": "temporary", "season": "all"},
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


def default_breaker_templates():
    tpl = {}
    for char in ["B", "C", "D"]:
        for nom in NOMINALS:
            tpl[f"Автомат 1P {char}{nom}"] = {
                "type": "auto", "poles": 1, "nominal": nom,
                "leak": None, "char": char,
                "desc": f"{char}{nom}", "group": "auto",
            }
    for char in ["C"]:
        for nom in [16, 25, 32, 40, 63]:
            tpl[f"Автомат 2P {char}{nom}"] = {
                "type": "auto", "poles": 2, "nominal": nom,
                "leak": None, "char": char,
                "desc": f"2P {char}{nom}", "group": "auto",
            }
    for char in ["C"]:
        for nom in [16, 25, 32, 40, 50, 63]:
            tpl[f"Автомат 3P {char}{nom}"] = {
                "type": "auto", "poles": 3, "nominal": nom,
                "leak": None, "char": char,
                "desc": f"3P {char}{nom}", "group": "auto",
            }
    for nom in [25, 32, 40, 63]:
        tpl[f"Автомат 4P C{nom}"] = {
            "type": "auto", "poles": 4, "nominal": nom,
            "leak": None, "char": "C",
            "desc": f"4P C{nom}", "group": "auto",
        }
    for nom in [25, 32, 40, 63]:
        for leak in [10, 30, 100, 300]:
            tpl[f"УЗО 2P {nom}/{leak}"] = {
                "type": "rcd", "poles": 2, "nominal": nom,
                "leak": leak, "char": None,
                "desc": f"УЗО {nom}А {leak}мА", "group": "rcd",
            }
    for nom in [25, 40, 63]:
        for leak in [30, 100, 300]:
            tpl[f"УЗО 4P {nom}/{leak}"] = {
                "type": "rcd", "poles": 4, "nominal": nom,
                "leak": leak, "char": None,
                "desc": f"УЗО 4P {nom}А {leak}мА", "group": "rcd",
            }
    for nom in [16, 25, 32, 40]:
        for leak in [10, 30]:
            tpl[f"Дифф 2P {nom}/{leak}"] = {
                "type": "diff", "poles": 2, "nominal": nom,
                "leak": leak, "char": "C",
                "desc": f"Дифф {nom}А {leak}мА", "group": "diff",
            }
    for nom in [25, 32, 40, 63]:
        for leak in [10, 30, 300]:
            tpl[f"Дифф 3P {nom}/{leak}"] = {
                "type": "diff", "poles": 3, "nominal": nom,
                "leak": leak, "char": "C",
                "desc": f"Дифф 3P {nom}А {leak}мА", "group": "diff",
            }
    for nom in [25, 32, 40, 63]:
        for leak in [30, 300]:
            tpl[f"Дифф 4P {nom}/{leak}"] = {
                "type": "diff", "poles": 4, "nominal": nom,
                "leak": leak, "char": "C",
                "desc": f"Дифф 4P {nom}А {leak}мА", "group": "diff",
            }
    for poles in [2, 3, 4]:
        for nom in [40, 63]:
            tpl[f"Рубильник {poles}P {nom}"] = {
                "type": "main", "poles": poles, "nominal": nom,
                "leak": None, "char": None,
                "desc": f"Рубильник {poles}P {nom}А", "group": "main",
            }
    for power in [5, 8, 10, 15]:
        for nom in [25, 32, 40, 63]:
            tpl[f"Стабилизатор {power}кВт {nom}А"] = {
                "type": "stabilizer", "poles": 2, "nominal": nom,
                "leak": None, "char": None,
                "desc": f"Стаб. {power}кВт", "group": "stabilizer",
            }
    tpl["Счётчик 1ф"] = {"type": "meter", "poles": 2, "nominal": 63,
                          "leak": None, "char": None,
                          "desc": "Счётчик 1ф", "group": "meter"}
    tpl["Счётчик 3ф"] = {"type": "meter", "poles": 4, "nominal": 63,
                          "leak": None, "char": None,
                          "desc": "Счётчик 3ф", "group": "meter"}
    for label, color in [("N", "#1E88E5"), ("PE", "#FDD835"),
                          ("L1", "#E53935"), ("L2", "#43A047"), ("L3", "#000000")]:
        for n_out in [2, 4, 6, 8, 12]:
            tpl[f"Шина {label} ({n_out})"] = {
                "type": "bus", "poles": 1, "nominal": 63,
                "leak": None, "char": None,
                "desc": f"Шина {label}", "group": "bus",
                "bus_color": color, "bus_outputs": n_out,
            }
    return tpl


DEFAULT_BREAKER_TEMPLATES = default_breaker_templates()


# ============================================================
# УТИЛИТЫ
# ============================================================
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


def usage_to_key(ru):
    for k, v in USAGE_RU.items():
        if v == ru:
            return k
    return "temporary"


def usage_to_ru(key):
    return USAGE_RU.get(key, key)


def season_to_key(ru):
    for k, v in SEASON_RU.items():
        if v == ru:
            return k
    return "all"


def season_to_ru(key):
    return SEASON_RU.get(key, key)


def orthogonalize(points):
    if len(points) < 2:
        return list(points)
    result = [points[0]]
    for i in range(1, len(points)):
        x_prev, y_prev = result[-1]
        x_cur, y_cur = points[i]
        dx = x_cur - x_prev
        dy = y_cur - y_prev
        if abs(dx) < 1 and abs(dy) < 1:
            continue
        if abs(dx) < 1:
            result.append((x_prev, y_cur))
        elif abs(dy) < 1:
            result.append((x_cur, y_prev))
        else:
            if abs(dx) >= abs(dy):
                result.append((x_cur, y_prev))
                result.append((x_cur, y_cur))
            else:
                result.append((x_prev, y_cur))
                result.append((x_cur, y_cur))
    cleaned = [result[0]]
    for p in result[1:]:
        if p != cleaned[-1]:
            cleaned.append(p)
    if len(cleaned) > 2:
        final = [cleaned[0]]
        for i in range(1, len(cleaned) - 1):
            x0, y0 = final[-1]
            x1, y1 = cleaned[i]
            x2, y2 = cleaned[i + 1]
            if (abs(x0 - x1) < 1 and abs(x1 - x2) < 1) or \
               (abs(y0 - y1) < 1 and abs(y1 - y2) < 1):
                continue
            final.append(cleaned[i])
        final.append(cleaned[-1])
        cleaned = final
    return cleaned


def lighten_color(hex_color, amount):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = int(r * (1 - amount) + 255 * amount)
    g = int(g * (1 - amount) + 255 * amount)
    b = int(b * (1 - amount) + 255 * amount)
    return f"#{r:02x}{g:02x}{b:02x}"


def seg_key(x1, y1, x2, y2):
    if abs(x2 - x1) < 1:
        xs = round(x1)
        y0, y1n = sorted([y1, y2])
        return ("V", xs, round(y0), round(y1n))
    else:
        ys = round(y1)
        x0, x1n = sorted([x1, x2])
        return ("H", ys, round(x0), round(x1n))


# ============================================================
# РАСЧЁТ
# ============================================================
def current_per_phase(power_kw, phases, phase_connections, settings):
    result = {"A": 0.0, "B": 0.0, "C": 0.0}
    if phases == 1:
        ph = phase_connections[0]
        u = settings.get(f"voltage_{ph}", 230.0)
        result[ph] += (power_kw * 1000) / u
    elif phases == 2:
        key = "".join(sorted(phase_connections))
        u = settings.get(f"voltage_line_{key}", 400.0)
        i = (power_kw * 1000) / u
        for ph in phase_connections:
            result[ph] += i
    elif phases == 3:
        u_avg = (
            settings.get("voltage_line_AB", 400.0) +
            settings.get("voltage_line_BC", 400.0) +
            settings.get("voltage_line_AC", 400.0)
        ) / 3.0
        i = (power_kw * 1000) / (math.sqrt(3) * u_avg)
        for ph in phase_connections:
            result[ph] += i
    return result


def _usage_filter(usage, mode):
    if mode == "all":
        return True
    if mode == "temporary":
        return usage != "rare"
    if mode == "constant":
        return usage == "constant"
    if mode == "temporary_only":
        return usage == "temporary"
    if mode == "rare_only":
        return usage == "rare"
    return True


def _season_filter(season, mode):
    if mode == "all":
        return True
    if mode == "winter":
        return season in ("winter", "all")
    if mode == "summer":
        return season in ("summer", "all")
    return True


def _socket_active(sock, plan):
    """Розетка активна, если:
       1) не помечена disabled;
       2) если связана с выключателем — хотя бы один выключатель включён;
       3) иначе — активна.
    """
    if sock.get("disabled", False):
        return False
    linked_switches = []
    for wire in plan.get("wires", []):
        if wire.get("socket_ref") is sock:
            sw_idx = wire.get("switch_idx")
            if sw_idx is not None and 0 <= sw_idx < len(plan.get("switches", [])):
                linked_switches.append(plan["switches"][sw_idx])
    if not linked_switches:
        return True
    return any(sw.get("state", False) for sw in linked_switches)


def calc_totals(plan, settings, mode="all", season="all"):
    totals = {"A": 0.0, "B": 0.0, "C": 0.0}
    for sock in plan["sockets"]:
        if not _socket_active(sock, plan):
            continue
        a = sock.get("appliance")
        if not a:
            continue
        usage = a.get("usage", "constant")
        seas = a.get("season", "all")
        if not _usage_filter(usage, mode):
            continue
        if not _season_filter(seas, season):
            continue
        cur = current_per_phase(a["power_kw"], a["phases"], a["phase_connections"], settings)
        for ph in "ABC":
            totals[ph] += cur[ph]
    return totals


def calc_phase_breakdown(plan, settings, mode="all", season="all"):
    result = {"A": [], "B": [], "C": []}
    for sock in plan["sockets"]:
        if not _socket_active(sock, plan):
            continue
        a = sock.get("appliance")
        if not a:
            continue
        usage = a.get("usage", "constant")
        seas = a.get("season", "all")
        if not _usage_filter(usage, mode):
            continue
        if not _season_filter(seas, season):
            continue
        cur = current_per_phase(a["power_kw"], a["phases"], a["phase_connections"], settings)
        for ph in a["phase_connections"]:
            u = settings.get(f"voltage_{ph}", 230.0)
            result[ph].append({
                "name": a["name"],
                "power_kw": cur[ph] * u / 1000.0,
                "usage": usage,
                "season": seas,
                "current": cur[ph],
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


def appliance_color(a, colors, disabled=False):
    if disabled:
        return DISABLED_COLOR
    if a is None:
        return colors["NONE"]
    conn = "".join(sorted(a["phase_connections"]))
    return colors.get(conn, colors["NONE"])


def reapply_templates_to_plan(plan, templates):
    changed = 0
    reset = 0
    for sock in plan["sockets"]:
        a = sock.get("appliance")
        if not a:
            continue
        name = a.get("name")
        if name not in templates:
            sock["appliance"] = None
            reset += 1
            continue
        t = templates[name]
        new_phases = t.get("phases", 1)
        a["power_kw"] = t.get("power_kw", a["power_kw"])
        a["usage"] = t.get("usage", a["usage"])
        a["season"] = t.get("season", "all")
        a["phases"] = new_phases
        a.pop("cos_phi", None)
        old_conn = a.get("phase_connections", [])
        if new_phases == 1:
            if len(old_conn) != 1 or old_conn[0] not in ("A", "B", "C"):
                a["phase_connections"] = ["A"]
        elif new_phases == 2:
            if len(old_conn) != 2 or any(p not in ("A", "B", "C") for p in old_conn):
                a["phase_connections"] = ["A", "B"]
            else:
                a["phase_connections"] = list(dict.fromkeys(old_conn))
                if len(a["phase_connections"]) != 2:
                    a["phase_connections"] = ["A", "B"]
        elif new_phases == 3:
            a["phase_connections"] = ["A", "B", "C"]
        changed += 1
    return changed, reset


# ============================================================
# ПОДСКАЗКА
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
# ДИАЛОГИ ПЛАНА ДОМА
# ============================================================
class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.title("Параметры расчёта")
        self.geometry("460x420")
        self.result = None
        self.settings = dict(settings)

        frm = tk.Frame(self, padx=15, pady=15)
        frm.pack(fill=tk.BOTH, expand=True)

        tk.Label(frm, text="НАПРЯЖЕНИЕ ФАЗ, В",
                 font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2,
                                                   sticky=tk.W, pady=(0, 8))
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
                 font=("Arial", 11, "bold")).grid(row=4, column=0, columnspan=2,
                                                   sticky=tk.W, pady=(15, 8))
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
                 font=("Arial", 11, "bold")).grid(row=8, column=0, columnspan=2,
                                                   sticky=tk.W, pady=(15, 8))
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
        tk.Button(btn, text="Сбросить", command=self.reset, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Отмена", command=self.destroy, width=10).pack(side=tk.LEFT, padx=5)

        self.transient(parent)
        self.wait_visibility()
        self.grab_set()

    def reset(self):
        self.var_A.set("230"); self.var_B.set("230"); self.var_C.set("230")
        self.var_AB.set("400"); self.var_BC.set("400"); self.var_AC.set("400")
        self.var_limit_kw.set("15"); self.var_limit_a.set("25")

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

        keys = [("A", "Фаза A"), ("B", "Фаза B"), ("C", "Фаза C"),
                ("AB", "Двухфазные AB"), ("BC", "Двухфазные BC"),
                ("AC", "Двухфазные AC"), ("ABC", "Трёхфазные ABC"),
                ("NONE", "Пустая розетка")]

        for i, (key, label) in enumerate(keys):
            tk.Label(frame, text=label, font=("Arial", 10),
                     width=18, anchor=tk.W).grid(row=i, column=0, pady=4)
            sw = tk.Label(frame, text="      ", bg=self.colors[key],
                           relief=tk.SOLID, borderwidth=1, width=8)
            sw.grid(row=i, column=1, padx=5)
            self.swatches[key] = sw
            tk.Button(frame, text="Выбрать цвет...",
                      command=lambda k=key: self.pick(k)).grid(row=i, column=2, padx=5)

        btn = tk.Frame(self)
        btn.pack(pady=10)
        tk.Button(btn, text="OK", command=self.on_ok, bg="#4CAF50",
                  fg="white", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Сбросить", command=self.reset, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Отмена", command=self.destroy, width=10).pack(side=tk.LEFT, padx=5)

        self.transient(parent)
        self.wait_visibility()
        self.grab_set()

    def pick(self, key):
        color = colorchooser.askcolor(color=self.colors[key], title=f"Цвет для {key}")[1]
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


class ApplianceDialog(tk.Toplevel):
    def __init__(self, parent, templates, socket):
        super().__init__(parent)
        self.title("Прибор на розетке")
        self.geometry("540x620")
        self.result = None
        self.disabled_result = None
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
                f"{usage_to_ru(t['usage'])}, {season_to_ru(t.get('season', 'all'))}")
        self.template_list.bind("<<ListboxSelect>>", self.on_template_select)

        self.disabled_var = tk.BooleanVar(value=socket.get("disabled", False))
        tk.Checkbutton(self, text="Розетка выключена",
                       variable=self.disabled_var,
                       bg="#FFF3E0", font=("Arial", 9, "bold")).pack(pady=5)

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
        tk.Label(frm, text="Режим:").grid(row=3, column=0, sticky=tk.W)
        self.usage_var = tk.StringVar(value=usage_to_ru("temporary"))
        ttk.Combobox(frm, textvariable=self.usage_var,
                     values=USAGE_RU_LIST, state="readonly",
                     width=22).grid(row=3, column=1, sticky=tk.W)
        tk.Label(frm, text="Сезон:").grid(row=4, column=0, sticky=tk.W)
        self.season_var = tk.StringVar(value="Круглый год")
        ttk.Combobox(frm, textvariable=self.season_var,
                     values=SEASON_RU_LIST, state="readonly",
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
        tk.Button(btn, text="Отмена", command=self.destroy, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Снять прибор", command=self.on_remove,
                  bg="#E53935", fg="white", width=14).pack(side=tk.LEFT, padx=5)

        if socket.get("appliance"):
            a = socket["appliance"]
            self.name_var.set(a["name"])
            self.power_var.set(str(a["power_kw"]))
            self.phases_var.set(str(a["phases"]))
            self.usage_var.set(usage_to_ru(a["usage"]))
            self.season_var.set(season_to_ru(a.get("season", "all")))
            self.phases_conn_var.set("".join(a["phase_connections"]))

        self.transient(parent)
        self.wait_visibility()
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
        self.usage_var.set(usage_to_ru(t["usage"]))
        self.season_var.set(season_to_ru(t.get("season", "all")))

    def on_ok(self):
        try:
            disabled = self.disabled_var.get()
            if not self.name_var.get().strip():
                self.result = "REMOVE"
                self.disabled_result = False
                self.destroy()
                return
            name = self.name_var.get().strip()
            power = float(self.power_var.get())
            phases = int(self.phases_var.get())
            if phases not in (1, 2, 3):
                raise ValueError("Фазы: 1, 2 или 3")
            usage = usage_to_key(self.usage_var.get())
            season = season_to_key(self.season_var.get())
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
                "season": season,
            }
            self.disabled_result = disabled
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)

    def on_remove(self):
        self.result = "REMOVE"
        self.disabled_result = False
        self.destroy()


class TemplateEditDialog(tk.Toplevel):
    def __init__(self, parent, name="", template=None):
        super().__init__(parent)
        self.title("Шаблон прибора")
        self.geometry("400x320")
        self.result = None
        self.template = template or {"power_kw": 1.0, "phases": 1,
                                      "usage": "temporary", "season": "all"}

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
        tk.Label(frm, text="Режим:").grid(row=3, column=0, sticky=tk.W, pady=4)
        self.usage_var = tk.StringVar(value=usage_to_ru(self.template["usage"]))
        ttk.Combobox(frm, textvariable=self.usage_var,
                     values=USAGE_RU_LIST, state="readonly",
                     width=22).grid(row=3, column=1, pady=4)
        tk.Label(frm, text="Сезон:").grid(row=4, column=0, sticky=tk.W, pady=4)
        self.season_var = tk.StringVar(value=season_to_ru(self.template.get("season", "all")))
        ttk.Combobox(frm, textvariable=self.season_var,
                     values=SEASON_RU_LIST, state="readonly",
                     width=22).grid(row=4, column=1, pady=4)

        btn = tk.Frame(self)
        btn.pack(pady=10)
        tk.Button(btn, text="OK", command=self.on_ok, bg="#4CAF50", fg="white",
                  width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Отмена", command=self.destroy, width=10).pack(side=tk.LEFT, padx=5)

        self.transient(parent)
        self.wait_visibility()
        self.grab_set()

    def on_ok(self):
        try:
            name = self.name_var.get().strip()
            if not name:
                raise ValueError("Введите название")
            power = float(self.power_var.get())
            phases = int(self.phases_var.get())
            usage = usage_to_key(self.usage_var.get())
            season = season_to_key(self.season_var.get())
            self.result = {
                "name": name,
                "template": {"power_kw": power, "phases": phases,
                              "usage": usage, "season": season}
            }
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)


class TemplatesDialog(tk.Toplevel):
    def __init__(self, parent, templates):
        super().__init__(parent)
        self.title("Шаблоны приборов")
        self.geometry("760x520")
        self.templates = templates

        tk.Label(self, text="Шаблоны приборов",
                 font=("Arial", 12, "bold")).pack(pady=5)

        self.tree = ttk.Treeview(
            self,
            columns=("name", "power", "phases", "usage", "season"),
            show="headings", height=15)
        self.tree.heading("name", text="Название")
        self.tree.heading("power", text="Мощность, кВт")
        self.tree.heading("phases", text="Фаз")
        self.tree.heading("usage", text="Режим")
        self.tree.heading("season", text="Сезон")
        self.tree.column("name", width=220)
        self.tree.column("power", width=110, anchor=tk.CENTER)
        self.tree.column("phases", width=60, anchor=tk.CENTER)
        self.tree.column("usage", width=150, anchor=tk.CENTER)
        self.tree.column("season", width=110, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.refresh()

        btn = tk.Frame(self)
        btn.pack(pady=5)
        tk.Button(btn, text="Добавить", command=self.add, width=12).pack(side=tk.LEFT, padx=3)
        tk.Button(btn, text="Редактировать", command=self.edit, width=14).pack(side=tk.LEFT, padx=3)
        tk.Button(btn, text="Удалить", command=self.remove, width=12).pack(side=tk.LEFT, padx=3)
        tk.Button(btn, text="Сохранить", command=self.save, width=12,
                  bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=3)

        self.transient(parent)
        self.wait_visibility()
        self.grab_set()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for name in sorted(self.templates.keys()):
            t = self.templates[name]
            self.tree.insert("", tk.END, values=(
                name, f"{t['power_kw']:.2f}", t["phases"],
                usage_to_ru(t["usage"]), season_to_ru(t.get("season", "all"))))

    def add(self):
        dlg = TemplateEditDialog(self, name="", template=None)
        self.wait_window(dlg)
        if dlg.result:
            self.templates[dlg.result["name"]] = dlg.result["template"]
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
        self.destroy()


# ============================================================
# ДИАЛОГИ ЩИТА
# ============================================================
class BreakerPickDialog(tk.Toplevel):
    def __init__(self, parent, templates):
        super().__init__(parent)
        self.title("Выбор устройства")
        self.geometry("640x640")
        self.result = None
        self.templates = templates

        tk.Label(self, text="Выбор устройства", font=("Arial", 12, "bold")).pack(pady=5)

        filt_frame = tk.LabelFrame(self, text="Фильтры", padx=10, pady=5)
        filt_frame.pack(fill=tk.X, padx=10)

        row1 = tk.Frame(filt_frame)
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="Полюсов:", width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.poles_var = tk.StringVar(value=DIALOG_STATE["poles"])
        ttk.Combobox(row1, textvariable=self.poles_var,
                     values=["", "1", "2", "3", "4"],
                     width=5, state="readonly").pack(side=tk.LEFT, padx=5)
        tk.Label(row1, text="  Номинал А:").pack(side=tk.LEFT)
        self.nominal_var = tk.StringVar(value=DIALOG_STATE["nominal"])
        ttk.Combobox(row1, textvariable=self.nominal_var,
                     values=[""] + [str(n) for n in NOMINALS],
                     width=6, state="readonly").pack(side=tk.LEFT, padx=5)
        tk.Label(row1, text="  Утечка мА:").pack(side=tk.LEFT)
        self.leak_var = tk.StringVar(value=DIALOG_STATE["leak"])
        ttk.Combobox(row1, textvariable=self.leak_var,
                     values=[""] + [str(l) for l in LEAKS],
                     width=6, state="readonly").pack(side=tk.LEFT, padx=5)

        row2 = tk.Frame(filt_frame)
        row2.pack(fill=tk.X, pady=2)
        tk.Label(row2, text="Группа:", width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.group_var = tk.StringVar(value=DIALOG_STATE["group"])
        ttk.Combobox(row2, textvariable=self.group_var,
                     values=["Все"] + list(TEMPLATE_GROUPS.values()),
                     width=18, state="readonly").pack(side=tk.LEFT, padx=5)
        tk.Label(row2, text="  Поиск:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar(value=DIALOG_STATE["search"])
        tk.Entry(row2, textvariable=self.search_var, width=20).pack(side=tk.LEFT, padx=5)

        for var in [self.poles_var, self.nominal_var, self.leak_var,
                    self.group_var, self.search_var]:
            var.trace_add("write", lambda *a: self.refresh())

        tk.Button(filt_frame, text="Сбросить фильтры", command=self.reset_filters,
                  bg="#ECEFF1").pack(pady=4)

        tk.Label(self, text="Доступные устройства:",
                 font=("Arial", 10, "bold")).pack(pady=(5, 0))

        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(list_frame, columns=("desc", "poles", "nom", "leak"),
                                  show="tree headings", height=18)
        self.tree.heading("#0", text="Устройство")
        self.tree.heading("desc", text="Описание")
        self.tree.heading("poles", text="P")
        self.tree.heading("nom", text="А")
        self.tree.heading("leak", text="мА")
        self.tree.column("#0", width=220)
        self.tree.column("desc", width=180)
        self.tree.column("poles", width=40, anchor=tk.CENTER)
        self.tree.column("nom", width=50, anchor=tk.CENTER)
        self.tree.column("leak", width=50, anchor=tk.CENTER)

        tree_scroll = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<Double-Button-1>", lambda e: self.on_ok())
        self.tree.bind("<<TreeviewOpen>>", self._save_open_state)
        self.tree.bind("<<TreeviewClose>>", self._save_open_state)

        btn = tk.Frame(self)
        btn.pack(pady=10)
        tk.Button(btn, text="OK", command=self.on_ok, bg="#4CAF50",
                  fg="white", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Отмена", command=self.destroy,
                  width=10).pack(side=tk.LEFT, padx=5)

        self.refresh()
        self.transient(parent)
        self.wait_visibility()
        self.grab_set()
        self.focus_force()

    def _save_open_state(self, event=None):
        for item in self.tree.get_children():
            text = self.tree.item(item, "text")
            is_open = self.tree.item(item, "open")
            DIALOG_STATE["group_open"][text] = is_open

    def _save_filters(self):
        DIALOG_STATE["poles"] = self.poles_var.get()
        DIALOG_STATE["nominal"] = self.nominal_var.get()
        DIALOG_STATE["leak"] = self.leak_var.get()
        DIALOG_STATE["group"] = self.group_var.get()
        DIALOG_STATE["search"] = self.search_var.get()

    def reset_filters(self):
        self.poles_var.set("")
        self.nominal_var.set("")
        self.leak_var.set("")
        self.group_var.set("Все")
        self.search_var.set("")
        self._save_filters()

    def refresh(self):
        self._save_open_state()
        self._save_filters()
        for item in self.tree.get_children():
            self.tree.delete(item)

        poles_f = self.poles_var.get()
        nominal_f = self.nominal_var.get()
        leak_f = self.leak_var.get()
        group_f = self.group_var.get()
        search_f = self.search_var.get().lower()

        groups = {}
        for name, t in self.templates.items():
            if poles_f and str(t.get("poles", 1)) != poles_f:
                continue
            if nominal_f and str(t.get("nominal", "")) != nominal_f:
                continue
            if leak_f:
                if t.get("leak") is None or str(t["leak"]) != leak_f:
                    continue
            group_key = t.get("group", "auto")
            group_ru = TEMPLATE_GROUPS.get(group_key, "Прочее")
            if group_f != "Все" and group_ru != group_f:
                continue
            if search_f and search_f not in name.lower() and \
                    search_f not in str(t.get("desc", "")).lower():
                continue
            groups.setdefault(group_ru, []).append((name, t))

        for group_ru in sorted(groups.keys()):
            is_open = DIALOG_STATE["group_open"].get(group_ru, False)
            group_id = self.tree.insert("", tk.END, text=group_ru, open=is_open,
                                          values=("", "", "", ""))
            for name, t in sorted(groups[group_ru]):
                self.tree.insert(group_id, tk.END, text=name,
                                  values=(t.get("desc", ""),
                                          t.get("poles", 1),
                                          t.get("nominal", ""),
                                          t.get("leak") or ""))

    def on_ok(self):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        parent = self.tree.parent(item)
        if not parent:
            return
        name = self.tree.item(item, "text")
        if name in self.templates:
            self._save_filters()
            self.result = dict(self.templates[name])
            self.result["name"] = name
            self.destroy()


class BreakerEditDialog(tk.Toplevel):
    def __init__(self, parent, breaker):
        super().__init__(parent)
        self.title("Устройство")
        self.geometry("400x340")
        self.result = None
        self.breaker = dict(breaker)

        frm = tk.Frame(self, padx=15, pady=15)
        frm.pack(fill=tk.BOTH, expand=True)

        tk.Label(frm, text="Подпись:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.desc_var = tk.StringVar(value=self.breaker.get("desc", ""))
        tk.Entry(frm, textvariable=self.desc_var, width=25).grid(row=0, column=1, pady=4)
        tk.Label(frm, text="Номинал (А):").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.nominal_var = tk.StringVar(value=str(self.breaker.get("nominal", 16)))
        ttk.Combobox(frm, textvariable=self.nominal_var,
                     values=[str(n) for n in NOMINALS],
                     state="readonly", width=22).grid(row=1, column=1, pady=4)
        tk.Label(frm, text="Ток утечки (мА):").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.leak_var = tk.StringVar(value=str(self.breaker.get("leak") or ""))
        ttk.Combobox(frm, textvariable=self.leak_var,
                     values=[""] + [str(l) for l in LEAKS],
                     state="readonly", width=22).grid(row=2, column=1, pady=4)
        tk.Label(frm, text="Характеристика:").grid(row=3, column=0, sticky=tk.W, pady=4)
        self.char_var = tk.StringVar(value=self.breaker.get("char") or "C")
        ttk.Combobox(frm, textvariable=self.char_var, values=[""] + CHARS,
                     state="readonly", width=22).grid(row=3, column=1, pady=4)

        btn = tk.Frame(self)
        btn.pack(pady=10)
        tk.Button(btn, text="OK", command=self.on_ok, bg="#4CAF50",
                  fg="white", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Отмена", command=self.destroy,
                  width=10).pack(side=tk.LEFT, padx=5)

        self.transient(parent)
        self.wait_visibility()
        self.grab_set()

    def on_ok(self):
        try:
            leak_str = self.leak_var.get().strip()
            self.result = {
                "desc": self.desc_var.get().strip(),
                "nominal": int(self.nominal_var.get()),
                "leak": int(leak_str) if leak_str else None,
                "char": self.char_var.get() or None,
            }
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)


class CableTypeDialog(tk.Toplevel):
    def __init__(self, parent, current):
        super().__init__(parent)
        self.title("Тип кабеля")
        self.geometry("280x280")
        self.result = None

        tk.Label(self, text="Тип кабеля:", font=("Arial", 11, "bold")).pack(pady=10)
        self.var = tk.StringVar(value=current)
        for key in ["L1", "L2", "L3", "N", "PE"]:
            color = CABLE_TYPES[key]["color"]
            fg = "white" if key != "PE" else "black"
            tk.Radiobutton(self, text=key, variable=self.var, value=key,
                           bg=color, fg=fg, font=("Arial", 12, "bold"),
                           selectcolor=color, indicatoron=False,
                           width=20, pady=5).pack(pady=2)

        btn = tk.Frame(self)
        btn.pack(pady=10)
        tk.Button(btn, text="OK", command=self.on_ok, bg="#4CAF50",
                  fg="white", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Отмена", command=self.destroy,
                  width=10).pack(side=tk.LEFT, padx=5)

        self.transient(parent)
        self.wait_visibility()
        self.grab_set()

    def on_ok(self):
        self.result = self.var.get()
        self.destroy()


class BreakerTemplateEditDialog(tk.Toplevel):
    TYPES = [("auto", "Автомат"), ("rcd", "УЗО"), ("diff", "Диффавтомат"),
             ("main", "Рубильник"), ("stabilizer", "Стабилизатор"),
             ("meter", "Счётчик"), ("out", "Выводной"), ("bus", "Шина")]

    def __init__(self, parent, name="", template=None):
        super().__init__(parent)
        self.title("Шаблон устройства")
        self.geometry("460x540")
        self.result = None
        self.template = template or {"type": "auto", "poles": 1, "nominal": 16,
                                      "leak": None, "char": "C", "desc": "",
                                      "group": "auto"}

        frm = tk.Frame(self, padx=15, pady=15)
        frm.pack(fill=tk.BOTH, expand=True)

        tk.Label(frm, text="Название шаблона:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.name_var = tk.StringVar(value=name)
        tk.Entry(frm, textvariable=self.name_var, width=25).grid(row=0, column=1, pady=4)
        tk.Label(frm, text="Тип:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.type_var = tk.StringVar(value=self._type_to_ru(self.template["type"]))
        ttk.Combobox(frm, textvariable=self.type_var,
                     values=[t[1] for t in self.TYPES], state="readonly",
                     width=22).grid(row=1, column=1, pady=4)
        tk.Label(frm, text="Группа:").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.group_var = tk.StringVar(value=self.template.get("group", "auto"))
        ttk.Combobox(frm, textvariable=self.group_var,
                     values=list(TEMPLATE_GROUPS.keys()), state="readonly",
                     width=22).grid(row=2, column=1, pady=4)
        tk.Label(frm, text="Число полюсов (1–4):").grid(row=3, column=0, sticky=tk.W, pady=4)
        self.poles_var = tk.StringVar(value=str(self.template["poles"]))
        ttk.Combobox(frm, textvariable=self.poles_var,
                     values=["1", "2", "3", "4"], state="readonly",
                     width=22).grid(row=3, column=1, pady=4)
        tk.Label(frm, text="Номинал, А:").grid(row=4, column=0, sticky=tk.W, pady=4)
        self.nominal_var = tk.StringVar(value=str(self.template["nominal"]))
        ttk.Combobox(frm, textvariable=self.nominal_var,
                     values=[str(n) for n in NOMINALS],
                     state="readonly", width=22).grid(row=4, column=1, pady=4)
        tk.Label(frm, text="Ток утечки, мА:").grid(row=5, column=0, sticky=tk.W, pady=4)
        self.leak_var = tk.StringVar(value=str(self.template["leak"]) if self.template.get("leak") else "")
        ttk.Combobox(frm, textvariable=self.leak_var,
                     values=[""] + [str(l) for l in LEAKS],
                     state="readonly", width=22).grid(row=5, column=1, pady=4)
        tk.Label(frm, text="Характеристика:").grid(row=6, column=0, sticky=tk.W, pady=4)
        self.char_var = tk.StringVar(value=self.template.get("char") or "")
        ttk.Combobox(frm, textvariable=self.char_var, values=[""] + CHARS,
                     state="readonly", width=22).grid(row=6, column=1, pady=4)
        tk.Label(frm, text="Подпись:").grid(row=7, column=0, sticky=tk.W, pady=4)
        self.desc_var = tk.StringVar(value=self.template.get("desc", ""))
        tk.Entry(frm, textvariable=self.desc_var, width=25).grid(row=7, column=1, pady=4)
        tk.Label(frm, text="Выходов шины (2–12):").grid(row=8, column=0, sticky=tk.W, pady=4)
        self.outputs_var = tk.StringVar(value=str(self.template.get("bus_outputs", 6)))
        ttk.Combobox(frm, textvariable=self.outputs_var,
                     values=["2", "4", "6", "8", "12"],
                     state="readonly", width=22).grid(row=8, column=1, pady=4)

        btn = tk.Frame(self)
        btn.pack(pady=10)
        tk.Button(btn, text="OK", command=self.on_ok, bg="#4CAF50",
                  fg="white", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Отмена", command=self.destroy,
                  width=10).pack(side=tk.LEFT, padx=5)

        self.transient(parent)
        self.wait_visibility()
        self.grab_set()

    def _type_to_ru(self, t):
        for key, ru in self.TYPES:
            if key == t:
                return ru
        return "Автомат"

    def _ru_to_type(self, ru):
        for key, r in self.TYPES:
            if r == ru:
                return key
        return "auto"

    def on_ok(self):
        try:
            name = self.name_var.get().strip()
            if not name:
                raise ValueError("Введите название")
            ttype = self._ru_to_type(self.type_var.get())
            poles = int(self.poles_var.get())
            nominal = int(self.nominal_var.get())
            leak_str = self.leak_var.get().strip()
            leak = int(leak_str) if leak_str else None
            char = self.char_var.get() or None
            desc = self.desc_var.get().strip()
            group = self.group_var.get()
            outputs = int(self.outputs_var.get()) if ttype == "bus" else None
            tpl = {"type": ttype, "poles": poles, "nominal": nominal,
                    "leak": leak, "char": char, "desc": desc, "group": group}
            if ttype == "bus":
                tpl["bus_outputs"] = outputs
                label = desc.replace("Шина ", "").strip()
                tpl["bus_color"] = CABLE_TYPES.get(label, {}).get("color", "#FFC107")
            self.result = {"name": name, "template": tpl}
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)


class BreakerTemplatesDialog(tk.Toplevel):
    def __init__(self, parent, templates):
        super().__init__(parent)
        self.title("Шаблоны устройств")
        self.geometry("900x600")
        self.templates = templates

        tk.Label(self, text="Шаблоны устройств", font=("Arial", 12, "bold")).pack(pady=5)

        self.tree = ttk.Treeview(
            self,
            columns=("name", "group", "type", "poles", "nominal", "leak", "char", "desc"),
            show="headings", height=20)
        for col, title, width in [
            ("name", "Название", 200),
            ("group", "Группа", 100),
            ("type", "Тип", 90),
            ("poles", "P", 40),
            ("nominal", "А", 50),
            ("leak", "мА", 50),
            ("char", "Х-ка", 50),
            ("desc", "Подпись", 200),
        ]:
            self.tree.heading(col, text=title)
            anchor = tk.W if col in ("name", "desc") else tk.CENTER
            self.tree.column(col, width=width, anchor=anchor)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.refresh()

        btn = tk.Frame(self)
        btn.pack(pady=5)
        tk.Button(btn, text="Добавить", command=self.add, width=12).pack(side=tk.LEFT, padx=3)
        tk.Button(btn, text="Редактировать", command=self.edit, width=14).pack(side=tk.LEFT, padx=3)
        tk.Button(btn, text="Удалить", command=self.remove, width=12).pack(side=tk.LEFT, padx=3)
        tk.Button(btn, text="Сохранить", command=self.save, width=12,
                  bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=3)

        self.transient(parent)
        self.wait_visibility()
        self.grab_set()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for name in sorted(self.templates.keys()):
            t = self.templates[name]
            group_ru = TEMPLATE_GROUPS.get(t.get("group", "auto"), "Прочее")
            self.tree.insert("", tk.END, values=(
                name, group_ru, t.get("type", ""), t.get("poles", ""),
                t.get("nominal", ""), t.get("leak") or "",
                t.get("char") or "", t.get("desc", "")))

    def add(self):
        dlg = BreakerTemplateEditDialog(self, name="", template=None)
        self.wait_window(dlg)
        if dlg.result:
            self.templates[dlg.result["name"]] = dlg.result["template"]
            self.refresh()

    def edit(self):
        sel = self.tree.selection()
        if not sel:
            return
        name = self.tree.item(sel[0])["values"][0]
        dlg = BreakerTemplateEditDialog(self, name=name, template=self.templates[name])
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
        save_json(BREAKER_TEMPLATES_FILE, self.templates)
        messagebox.showinfo("Готово", "Шаблоны сохранены.", parent=self)
        self.destroy()


class BusPickDialog(tk.Toplevel):
    def __init__(self, parent, templates):
        super().__init__(parent)
        self.title("Выбор шины")
        self.geometry("360x300")
        self.result = None
        self.templates = templates

        tk.Label(self, text="Выберите шину:", font=("Arial", 11, "bold")).pack(pady=10)

        self.listbox = tk.Listbox(self, height=10, font=("Arial", 10))
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._names = []
        for name in sorted(templates.keys()):
            t = templates[name]
            if t.get("type") == "bus":
                self.listbox.insert(tk.END, name)
                self._names.append(name)
        if self._names:
            self.listbox.selection_set(0)

        btn = tk.Frame(self)
        btn.pack(pady=10)
        tk.Button(btn, text="OK", command=self.on_ok, bg="#4CAF50",
                  fg="white", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="Отмена", command=self.destroy,
                  width=10).pack(side=tk.LEFT, padx=5)

        self.transient(parent)
        self.wait_visibility()
        self.grab_set()

    def on_ok(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        name = self._names[sel[0]]
        self.result = dict(self.templates[name])
        self.destroy()


# ============================================================
# ВКЛАДКА 1: ПЛАН ДОМА (с масштабированием фото)
# ============================================================
class HomePlanTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.plan = {
            "walls": [], "sockets": [], "switches": [], "wires": [],
            "photo_path": None, "room_width": 1400, "room_height": 900,
        }
        self.current_file = None
        self.photo_img = None
        self.photo_pil = None
        self.photo_size = (0, 0)
        self.socket_diameter = 12
        self.mode = "select"
        self.wall_start = None
        self.selected_socket = None
        self.selected_switch = None
        self.selected_wire = None
        self.dragging = False
        self.drag_offset = (0, 0)
        self.undo_stack = []
        self.wire_points = []
        self.wire_mode_active = False
        self.hover = None
        self.scale = 1.0

        self._build_ui()
        self._draw_all()

    def _build_ui(self):
        toolbar = tk.Frame(self, bg="#ECEFF1", height=44)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Label(toolbar, text="Режим:", bg="#ECEFF1",
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)

        self.mode_var = tk.StringVar(value="select")
        for text, val in [("Выбор", "select"),
                           ("Стена гориз.", "wall_h"),
                           ("Стена верт.", "wall_v"),
                           ("Розетка", "place_socket"),
                           ("Выключатель", "place_switch"),
                           ("Провод", "draw_wire")]:
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

        tk.Label(toolbar, text="  Масштаб:", bg="#ECEFF1").pack(side=tk.LEFT, padx=5)
        self.scale_label = tk.Label(toolbar, text="100%", bg="#ECEFF1",
                                     font=("Arial", 10, "bold"))
        self.scale_label.pack(side=tk.LEFT)
        tk.Button(toolbar, text="+", command=lambda: self.zoom(ZOOM_STEP),
                  width=2).pack(side=tk.LEFT, padx=1)
        tk.Button(toolbar, text="−", command=lambda: self.zoom(1 / ZOOM_STEP),
                  width=2).pack(side=tk.LEFT, padx=1)
        tk.Button(toolbar, text="1:1", command=lambda: self.zoom(1.0 / self.scale),
                  width=3).pack(side=tk.LEFT, padx=1)

        tk.Button(toolbar, text="Отменить", command=self.undo,
                  bg="#FFB300").pack(side=tk.RIGHT, padx=5)
        tk.Button(toolbar, text="Удалить выделенное", command=self.delete_selected,
                  bg="#E53935", fg="white").pack(side=tk.RIGHT, padx=5)

        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        right_frame = tk.Frame(main_frame, width=320, bg="#FAFAFA")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_frame.pack_propagate(False)

        self.right_panel = RightPanel(right_frame, self.app, self.plan)
        self.right_panel.pack(fill=tk.BOTH, expand=True)

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
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Leave>", lambda e: self.hover.hide() if self.hover else None)

        self.hover = HoverTip(self.canvas)

    # ---------- Масштаб ----------
    def on_zoom_wheel(self, event):
        factor = ZOOM_STEP if event.delta > 0 else 1 / ZOOM_STEP
        self.zoom_at(event.x, event.y, factor)

    def zoom_at(self, x, y, factor):
        old_scale = self.scale
        new_scale = max(MIN_SCALE, min(MAX_SCALE, old_scale * factor))
        if abs(new_scale - old_scale) < 0.001:
            return
        self.scale = new_scale
        self._draw_all()
        self.scale_label.config(text=f"{int(self.scale * 100)}%")

    def zoom(self, factor):
        self.scale = max(MIN_SCALE, min(MAX_SCALE, self.scale * factor))
        self._draw_all()
        self.scale_label.config(text=f"{int(self.scale * 100)}%")

    def S(self, v):
        return v * self.scale

    def set_mode(self, mode):
        if self.mode == "draw_wire" and mode != "draw_wire":
            self.finish_wire()
        self.mode = mode
        self.mode_var.set(mode)
        self.wall_start = None
        self.wire_points = []
        self.wire_mode_active = (mode == "draw_wire")

    def update_diameter(self):
        try:
            self.socket_diameter = int(self.diameter_var.get())
        except Exception:
            pass

    def push_undo(self):
        self.undo_stack.append(copy.deepcopy(self.plan))
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            return
        prev = self.undo_stack.pop()
        photo_path = self.plan.get("photo_path")
        self.plan.clear()
        self.plan.update(prev)
        self.plan["photo_path"] = photo_path
        self._load_photo()
        self._draw_all()
        self.right_panel.refresh()

    def _load_photo(self):
        self.photo_img = None
        self.photo_pil = None
        path = self.plan.get("photo_path")
        if not path or not os.path.exists(path):
            return
        try:
            if PIL_AVAILABLE:
                img = Image.open(path)
                self.photo_pil = img.copy()
                self.photo_size = (img.width, img.height)
                self._render_photo()
            else:
                self.photo_img = tk.PhotoImage(file=path)
                self.photo_size = (self.photo_img.width(), self.photo_img.height())
        except Exception as e:
            print("Ошибка загрузки фото:", e)

    def _render_photo(self):
        if self.photo_pil is None:
            return
        w = max(1, int(self.photo_size[0] * self.scale))
        h = max(1, int(self.photo_size[1] * self.scale))
        try:
            resized = self.photo_pil.resize((w, h), Image.LANCZOS)
            self.photo_img = ImageTk.PhotoImage(resized)
        except Exception as e:
            print("Ошибка масштабирования фото:", e)

    def _draw_all(self):
        self.canvas.delete("all")

        if self.photo_pil is not None:
            self._render_photo()
        if self.photo_img is not None:
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_img)
            w = int(self.photo_size[0] * self.scale)
            h = int(self.photo_size[1] * self.scale)
            self.canvas.config(scrollregion=(0, 0, w, h))
        else:
            w = self.S(self.plan.get("room_width", 1400))
            h = self.S(self.plan.get("room_height", 900))
            self.canvas.config(scrollregion=(0, 0, w, h))

        for wall in self.plan["walls"]:
            x1, y1, x2, y2 = wall
            self.canvas.create_line(self.S(x1), self.S(y1), self.S(x2), self.S(y2),
                                     fill="#37474F", width=max(1, int(self.S(5))))

        for i, wire in enumerate(self.plan.get("wires", [])):
            pts = wire.get("points", [])
            if len(pts) < 2:
                continue
            flat = []
            for p in pts:
                flat.extend((self.S(p[0]), self.S(p[1])))
            selected = (self.selected_wire == i)
            color = WIRE_SELECTED_COLOR if selected else WIRE_COLOR
            width = max(1, int(self.S(5) if selected else self.S(3)))
            self.canvas.create_line(*flat, fill=color, width=width,
                                     capstyle=tk.ROUND, joinstyle=tk.ROUND,
                                     tags=f"wire_{i}")

        for i, sw in enumerate(self.plan.get("switches", [])):
            self._draw_switch(i, sw)

        for i, sock in enumerate(self.plan["sockets"]):
            self._draw_socket(i, sock)

        if self.wire_mode_active and len(self.wire_points) >= 2:
            flat = []
            for p in self.wire_points:
                flat.extend((self.S(p[0]), self.S(p[1])))
            self.canvas.create_line(*flat, fill=WIRE_COLOR, width=max(1, int(self.S(3))),
                                     capstyle=tk.ROUND, joinstyle=tk.ROUND)
        for p in self.wire_points:
            x, y = self.S(p[0]), self.S(p[1])
            r = max(2, int(self.S(4)))
            self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                     fill="#FF6F00", outline="")

        if self.wall_start is not None:
            x, y = self.S(self.wall_start[0]), self.S(self.wall_start[1])
            r = max(2, int(self.S(4)))
            self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                     outline="#B71C1C", width=2)

    def _draw_socket(self, idx, sock):
        x, y = self.S(sock["x"]), self.S(sock["y"])
        r = self.S(sock.get("diameter", 12)) / 2
        a = sock.get("appliance")
        active = _socket_active(sock, self.plan)
        is_lamp = a and "лампоч" in a.get("name", "").lower()
        if is_lamp and active:
            self.canvas.create_oval(x - r * 2, y - r * 2, x + r * 2, y + r * 2,
                                     fill=GLOW_COLOR, outline="")
        disabled = sock.get("disabled", False)
        color = appliance_color(a, self.app.phase_colors, disabled or not active)
        self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                 fill=color, outline="#263238", width=1)
        if disabled:
            self.canvas.create_line(x - r * 0.7, y - r * 0.7,
                                     x + r * 0.7, y + r * 0.7,
                                     fill="#B71C1C", width=max(1, int(self.S(2))))
            self.canvas.create_line(x - r * 0.7, y + r * 0.7,
                                     x + r * 0.7, y - r * 0.7,
                                     fill="#B71C1C", width=max(1, int(self.S(2))))
        if a:
            self.canvas.create_text(x, y - r - self.S(6), text=a["name"][:3],
                                     font=("Arial", max(6, int(self.S(8)))),
                                     fill="#000")
        if self.selected_socket == idx:
            pad = self.S(4)
            self.canvas.create_oval(x - r - pad, y - r - pad,
                                     x + r + pad, y + r + pad,
                                     outline="#FF6F00", width=2)

    def _draw_switch(self, idx, sw):
        x, y = self.S(sw["x"]), self.S(sw["y"])
        h = self.S(sw.get("diameter", 12)) / 2
        state = sw.get("state", False)
        color = SWITCH_ON_COLOR if state else SWITCH_OFF_COLOR
        if state:
            pad = self.S(4)
            self.canvas.create_rectangle(x - h - pad, y - h - pad,
                                           x + h + pad, y + h + pad,
                                           fill="#FFF9C4", outline="")
        self.canvas.create_rectangle(x - h, y - h, x + h, y + h,
                                       fill=color, outline="#263238", width=2)
        self.canvas.create_text(x, y - h - self.S(8),
                                 text="ВКЛ" if state else "ВЫКЛ",
                                 font=("Arial", max(6, int(self.S(8))), "bold"),
                                 fill="#000")
        if self.selected_switch == idx:
            pad = self.S(4)
            self.canvas.create_rectangle(x - h - pad, y - h - pad,
                                           x + h + pad, y + h + pad,
                                           outline="#FF6F00", width=2)

    def _find_socket(self, x, y):
        for i, sock in enumerate(self.plan["sockets"]):
            r = sock.get("diameter", 12) / 2
            if (x - sock["x"]) ** 2 + (y - sock["y"]) ** 2 <= r * r:
                return i
        return None

    def _find_switch(self, x, y):
        for i, sw in enumerate(self.plan.get("switches", [])):
            h = sw.get("diameter", 12) / 2
            if abs(x - sw["x"]) <= h and abs(y - sw["y"]) <= h:
                return i
        return None

    def _find_wire(self, x, y, tolerance=8):
        for i, wire in enumerate(self.plan.get("wires", [])):
            pts = wire.get("points", [])
            for j in range(len(pts) - 1):
                d = self._seg_dist(x, y, pts[j][0], pts[j][1],
                                    pts[j + 1][0], pts[j + 1][1])
                if d <= tolerance:
                    return i
        return None

    @staticmethod
    def _seg_dist(px, py, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(px - x1, py - y1)
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))

    def on_click(self, event):
        x = self.canvas.canvasx(event.x) / self.scale
        y = self.canvas.canvasy(event.y) / self.scale

        if self.mode == "place_socket":
            self.push_undo()
            self.plan["sockets"].append({"x": x, "y": y,
                                          "diameter": self.socket_diameter,
                                          "appliance": None, "disabled": False})
            self.selected_socket = len(self.plan["sockets"]) - 1
            self._draw_all()
            self.right_panel.refresh()
            return

        if self.mode == "place_switch":
            self.push_undo()
            self.plan.setdefault("switches", []).append({
                "x": x, "y": y, "diameter": self.socket_diameter, "state": False})
            self.selected_switch = len(self.plan["switches"]) - 1
            self._draw_all()
            return

        if self.mode == "draw_wire":
            self.wire_points.append((x, y))
            self._draw_all()
            return

        if self.mode in ("wall_h", "wall_v"):
            if self.wall_start is None:
                self.wall_start = (x, y)
            else:
                x1, y1 = self.wall_start
                if self.mode == "wall_h":
                    y2, x2 = y1, x
                else:
                    x2, y2 = x1, y
                self.push_undo()
                self.plan["walls"].append([x1, y1, x2, y2])
                self.wall_start = None
                self._draw_all()
            return

        sw_idx = self._find_switch(x, y)
        if sw_idx is not None:
            self.push_undo()
            self.plan["switches"][sw_idx]["state"] = not self.plan["switches"][sw_idx].get("state", False)
            self.selected_switch = sw_idx
            self._draw_all()
            self.right_panel.refresh()
            return

        sock_idx = self._find_socket(x, y)
        if sock_idx is not None:
            self.push_undo()
            sock = self.plan["sockets"][sock_idx]
            sock["disabled"] = not sock.get("disabled", False)
            self.selected_socket = sock_idx
            self._draw_all()
            self.right_panel.refresh()
            return

        wire_idx = self._find_wire(x, y)
        if wire_idx is not None:
            self.selected_wire = wire_idx
            self.selected_socket = None
            self.selected_switch = None
            self._draw_all()
            return

        self.selected_socket = None
        self.selected_switch = None
        self.selected_wire = None
        self._draw_all()

    def on_double_click(self, event):
        if self.mode == "draw_wire":
            self.finish_wire()

    def finish_wire(self):
        if len(self.wire_points) < 2:
            self.wire_points = []
            self._draw_all()
            return

        start = self.wire_points[0]
        end = self.wire_points[-1]

        sw_idx = None
        best = 40
        for i, sw in enumerate(self.plan.get("switches", [])):
            d = math.hypot(start[0] - sw["x"], start[1] - sw["y"])
            if d < best:
                best = d
                sw_idx = i

        sock_ref = None
        best = 40
        for sock in self.plan["sockets"]:
            d = math.hypot(end[0] - sock["x"], end[1] - sock["y"])
            if d < best:
                best = d
                sock_ref = sock

        self.push_undo()
        self.plan.setdefault("wires", []).append({
            "points": list(self.wire_points),
            "switch_idx": sw_idx,
            "socket_ref": sock_ref,
        })
        self.wire_points = []
        self._draw_all()
        self.right_panel.refresh()

    def on_drag(self, event):
        if not self.dragging or self.selected_socket is None:
            return
        x = self.canvas.canvasx(event.x) / self.scale
        y = self.canvas.canvasy(event.y) / self.scale
        sock = self.plan["sockets"][self.selected_socket]
        sock["x"] = x - self.drag_offset[0]
        sock["y"] = y - self.drag_offset[1]
        self._draw_all()

    def on_release(self, event):
        self.dragging = False

    def on_right_click(self, event):
        x = self.canvas.canvasx(event.x) / self.scale
        y = self.canvas.canvasy(event.y) / self.scale

        if self.mode == "draw_wire":
            self.finish_wire()
            return

        sw_idx = self._find_switch(x, y)
        if sw_idx is not None:
            self.selected_switch = sw_idx
            self._popup_switch(sw_idx, event.x_root, event.y_root)
            return

        sock_idx = self._find_socket(x, y)
        if sock_idx is not None:
            self.selected_socket = sock_idx
            self._popup_socket(sock_idx, event.x_root, event.y_root)
            return

        wire_idx = self._find_wire(x, y)
        if wire_idx is not None:
            self.selected_wire = wire_idx
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Удалить провод",
                              command=lambda: self.delete_wire(wire_idx))
            menu.tk_popup(event.x_root, event.y_root)

    def _popup_socket(self, idx, xr, yr):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Назначить прибор...",
                          command=lambda: self.edit_appliance(idx))
        menu.add_command(label="Удалить розетку",
                          command=lambda: self.delete_socket(idx))
        menu.tk_popup(xr, yr)

    def _popup_switch(self, idx, xr, yr):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Удалить выключатель",
                          command=lambda: self.delete_switch(idx))
        menu.tk_popup(xr, yr)

    def edit_appliance(self, idx):
        sock = self.plan["sockets"][idx]
        self.push_undo()
        dlg = ApplianceDialog(self, self.app.templates, sock)
        self.wait_window(dlg)
        if dlg.result == "REMOVE":
            sock["appliance"] = None
        elif dlg.result:
            sock["appliance"] = dlg.result
        if dlg.disabled_result is not None:
            sock["disabled"] = dlg.disabled_result
        self._draw_all()
        self.right_panel.refresh()

    def delete_socket(self, idx):
        self.push_undo()
        sock = self.plan["sockets"][idx]
        self.plan["wires"] = [w for w in self.plan.get("wires", [])
                                if w.get("socket_ref") is not sock]
        del self.plan["sockets"][idx]
        self.selected_socket = None
        self._draw_all()
        self.right_panel.refresh()

    def delete_switch(self, idx):
        self.push_undo()
        self.plan["wires"] = [w for w in self.plan.get("wires", [])
                                if w.get("switch_idx") != idx]
        for w in self.plan["wires"]:
            if w.get("switch_idx") is not None and w["switch_idx"] > idx:
                w["switch_idx"] -= 1
        del self.plan["switches"][idx]
        self.selected_switch = None
        self._draw_all()
        self.right_panel.refresh()

    def delete_wire(self, idx):
        self.push_undo()
        del self.plan["wires"][idx]
        self.selected_wire = None
        self._draw_all()
        self.right_panel.refresh()

    def delete_selected(self):
        if self.selected_wire is not None:
            self.delete_wire(self.selected_wire)
        elif self.selected_switch is not None:
            self.delete_switch(self.selected_switch)
        elif self.selected_socket is not None:
            self.delete_socket(self.selected_socket)

    def on_motion(self, event):
        x = self.canvas.canvasx(event.x) / self.scale
        y = self.canvas.canvasy(event.y) / self.scale

        sw_idx = self._find_switch(x, y)
        if sw_idx is not None:
            sw = self.plan["switches"][sw_idx]
            self.hover.show(event.x_root + 15, event.y_root + 15,
                            f"Выключатель #{sw_idx+1}\n"
                            f"{'ВКЛ' if sw.get('state') else 'ВЫКЛ'}")
            return

        sock_idx = self._find_socket(x, y)
        if sock_idx is not None:
            sock = self.plan["sockets"][sock_idx]
            a = sock.get("appliance")
            if a:
                active = _socket_active(sock, self.plan)
                self.hover.show(event.x_root + 15, event.y_root + 15,
                                f"{a['name']}\n{a['power_kw']} кВт\n"
                                f"фазы {','.join(a['phase_connections'])}\n"
                                f"{'Активна' if active else 'Обесточена'}")
            return

        self.hover.hide()

    def new_plan(self):
        if not messagebox.askyesno("Новый план", "Очистить текущий план?"):
            return
        self.push_undo()
        self.plan.clear()
        self.plan.update({"walls": [], "sockets": [], "switches": [], "wires": [],
                           "photo_path": None, "room_width": 1400, "room_height": 900})
        self.current_file = None
        self.photo_img = None
        self.photo_pil = None
        self._draw_all()
        self.right_panel.refresh()

    def save_plan(self):
        if not self.current_file:
            self.save_plan_as()
            return
        save_json(self.current_file, self._prepare_for_save())
        self.app.status.config(text=f"Сохранено: {self.current_file}")

    def save_plan_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                              filetypes=[("Power plan", "*.json")],
                                              initialfile="plan.json")
        if not path:
            return
        save_json(path, self._prepare_for_save())
        self.current_file = path
        self.app.status.config(text=f"Сохранено: {path}")

    def _prepare_for_save(self):
        orig_sockets = self.plan.get("sockets", [])

        sockets_copy = []
        for s in orig_sockets:
            sockets_copy.append({
                "x": s.get("x", 0),
                "y": s.get("y", 0),
                "diameter": s.get("diameter", 12),
                "disabled": s.get("disabled", False),
                "appliance": copy.deepcopy(s.get("appliance")) if s.get("appliance") else None,
            })

        switches_copy = []
        for sw in self.plan.get("switches", []):
            switches_copy.append({
                "x": sw.get("x", 0),
                "y": sw.get("y", 0),
                "diameter": sw.get("diameter", 12),
                "state": sw.get("state", False),
            })

        id_to_idx = {id(s): i for i, s in enumerate(orig_sockets)}

        wires_copy = []
        for w in self.plan.get("wires", []):
            sock_ref = w.get("socket_ref")
            sock_idx = None
            if sock_ref is not None:
                sock_idx = id_to_idx.get(id(sock_ref), None)
            wires_copy.append({
                "points": [list(p) for p in w.get("points", [])],
                "switch_idx": w.get("switch_idx"),
                "socket_idx": sock_idx,
            })

        walls_copy = [list(w) for w in self.plan.get("walls", [])]

        return {
            "walls": walls_copy,
            "sockets": sockets_copy,
            "switches": switches_copy,
            "wires": wires_copy,
            "photo_path": self.plan.get("photo_path"),
            "room_width": self.plan.get("room_width", 1400),
            "room_height": self.plan.get("room_height", 900),
        }

    def open_plan(self):
        path = filedialog.askopenfilename(filetypes=[("Power plan", "*.json")])
        if not path:
            return
        data = load_json(path, None)
        if not data:
            return
        data.setdefault("switches", [])
        data.setdefault("wires", [])
        self.plan.clear()
        self.plan.update(data)
        for wire in self.plan.get("wires", []):
            sock_idx = wire.pop("socket_idx", None)
            if sock_idx is not None and 0 <= sock_idx < len(self.plan["sockets"]):
                wire["socket_ref"] = self.plan["sockets"][sock_idx]
            else:
                wire["socket_ref"] = None
        self.current_file = path
        self._load_photo()
        self._draw_all()
        self.right_panel.refresh()

    def load_photo(self):
        if not PIL_AVAILABLE:
            messagebox.showwarning("Pillow", "Установите Pillow:\n\npip install pillow")
            return
        path = filedialog.askopenfilename(filetypes=[("Изображения", "*.jpg *.jpeg *.png")])
        if not path:
            return
        try:
            img = Image.open(path)
            self.photo_pil = img.copy()
            self.photo_size = (img.width, img.height)
            self.photo_img = None
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return
        self.plan["photo_path"] = path
        self._draw_all()

    def clear_photo(self):
        self.plan["photo_path"] = None
        self.photo_img = None
        self.photo_pil = None
        self._draw_all()

# ============================================================
# ПРАВАЯ ПАНЕЛЬ ПЛАНА ДОМА
# ============================================================
class RightPanel(tk.Frame):
    def __init__(self, parent, app, plan):
        super().__init__(parent, bg="#FAFAFA")
        self.app = app
        self.plan = plan

        tk.Label(self, text="РАСЧЁТ ПО ФАЗАМ",
                 font=("Arial", 10, "bold"),
                 bg="#37474F", fg="white").pack(fill=tk.X)

        season_frame = tk.Frame(self, bg="#FAFAFA")
        season_frame.pack(fill=tk.X, padx=3, pady=3)
        tk.Label(season_frame, text="Сезон:", bg="#FAFAFA",
                 font=("Arial", 8, "bold")).pack(anchor=tk.W)
        self.season_var = tk.StringVar(value="all")
        for key, text in [("all", "Круглый год"), ("winter", "Зима"), ("summer", "Лето")]:
            tk.Radiobutton(season_frame, text=text, variable=self.season_var,
                           value=key, bg="#FAFAFA", font=("Arial", 8),
                           anchor=tk.W, command=self.refresh).pack(fill=tk.X)

        mode_frame = tk.Frame(self, bg="#FAFAFA")
        mode_frame.pack(fill=tk.X, padx=3, pady=3)
        tk.Label(mode_frame, text="Режим:", bg="#FAFAFA",
                 font=("Arial", 8, "bold")).pack(anchor=tk.W)
        self.mode_var = tk.StringVar(value="all")
        for key, text in [("all", "Всё"), ("temporary", "Без редких"),
                           ("constant", "Только постоянные"),
                           ("temporary_only", "Только временные"),
                           ("rare_only", "Только редкие")]:
            tk.Radiobutton(mode_frame, text=text, variable=self.mode_var,
                           value=key, bg="#FAFAFA", font=("Arial", 8),
                           anchor=tk.W, command=self.refresh).pack(fill=tk.X)

        self.canvas = tk.Canvas(self, bg="#FAFAFA", highlightthickness=0)
        self.scroll = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.phases_frame = tk.Frame(self.canvas, bg="#FAFAFA")
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.phases_frame, anchor=tk.NW)
        self.phases_frame.bind("<Configure>",
                                lambda e: self.canvas.configure(
                                    scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
                          lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        self.summary_label = tk.Label(self, text="", bg="#FAFAFA",
                                       font=("Arial", 9, "italic"),
                                       justify=tk.LEFT, anchor=tk.W, wraplength=280)
        self.summary_label.pack(fill=tk.X, padx=4, pady=4)

        self.refresh()

    def refresh(self):
        for w in self.phases_frame.winfo_children():
            w.destroy()

        colors = self.app.phase_colors
        settings = self.app.settings
        mode = self.mode_var.get()
        season = self.season_var.get()
        totals = calc_totals(self.plan, settings, mode, season)
        breakdown = calc_phase_breakdown(self.plan, settings, mode, season)

        max_i = max(totals["A"], totals["B"], totals["C"], 0.1)
        panel_w = max(self.canvas.winfo_width(), 240)

        for ph in "ABC":
            color = colors[ph]
            u = settings.get(f"voltage_{ph}", 230.0)
            frame = tk.LabelFrame(self.phases_frame, text=f"Фаза {ph}  ({u:.0f} В)",
                                   font=("Arial", 9, "bold"), fg=color, bg="#FAFAFA",
                                   labelanchor=tk.NW, padx=2, pady=2)
            frame.pack(fill=tk.X, padx=3, pady=3)

            header = tk.Frame(frame, bg="#FAFAFA")
            header.pack(fill=tk.X, padx=2, pady=1)
            tk.Label(header, text=f"{totals[ph]:.1f} А",
                     font=("Arial", 9, "bold"), fg=color, bg="#FAFAFA").pack(side=tk.LEFT)
            tk.Label(header, text=f" {totals[ph] * u / 1000:.2f} кВт",
                     font=("Arial", 8), bg="#FAFAFA").pack(side=tk.LEFT)

            bar_bg = tk.Frame(frame, bg="#E0E0E0", height=4)
            bar_bg.pack(fill=tk.X, padx=3, pady=(0, 2))
            ratio = totals[ph] / max_i if max_i > 0 else 0
            bar_width = max(1, int((panel_w - 20) * ratio))
            tk.Frame(bar_bg, bg=color, height=4).place(x=0, y=0,
                                                         width=bar_width, height=4)

            for item in breakdown[ph]:
                row = tk.Frame(frame, bg="#FAFAFA")
                row.pack(fill=tk.X, padx=2)
                tk.Label(row, text="•", bg="#FAFAFA", fg=color,
                         font=("Arial", 8)).pack(side=tk.LEFT)
                tk.Label(row, text=item['name'], bg="#FAFAFA",
                         font=("Arial", 8)).pack(side=tk.LEFT)
                tk.Label(row, text=f"{item['power_kw']:.2f}кВт/{item['current']:.1f}А",
                         bg="#FAFAFA", font=("Arial", 7),
                         fg="#555").pack(side=tk.RIGHT)

        pct, _ = imbalance(totals)
        total_kw = sum(totals[ph] * settings.get(f"voltage_{ph}", 230.0)
                       for ph in "ABC") / 1000.0
        if pct > 15:
            txt, c = f"⚠ Перекос: {pct:.1f}%", "#B71C1C"
        elif pct > 5:
            txt, c = f"~ Перекос: {pct:.1f}%", "#E65100"
        else:
            txt, c = f"✓ Перекос: {pct:.1f}%", "#33691E"
        self.summary_label.config(text=f"{txt}\nВсего: {total_kw:.2f} кВт", fg=c)


# ============================================================
# ВКЛАДКА 2: ЭЛЕКТРОЩИТ
# ============================================================
class PanelTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.templates = load_json(BREAKER_TEMPLATES_FILE,
                                     dict(DEFAULT_BREAKER_TEMPLATES))

        self.shield = {
            "rails": 3,
            "rail_spacing": 180,
            "module_width": 28,
            "rail_y_start": 200,
            "breakers": [],
            "cables": [],
            "buses": [],
        }
        self.current_file = None

        self.scale = 1.0
        self.mode = "select"
        self.selected_breaker = None
        self.selected_cable = None
        self.selected_bus = None
        self.cable_points = []
        self.cable_type = "L1"
        self.cable_width = 2
        self.drag_breaker = None
        self.drag_bus = None
        self.drag_offset = (0, 0)
        self.drag_start_x = 0
        self._pending_toggle = False
        self.undo_stack = []
        self.hover = None
        self.preview_pos = None

        self._build_ui()
        self._draw_all()

    def _build_ui(self):
        toolbar = tk.Frame(self, bg="#ECEFF1")
        toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Label(toolbar, text="Режим:", bg="#ECEFF1",
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)

        self.mode_var = tk.StringVar(value="select")
        for text, val in [("Выбор", "select"),
                           ("Устройство", "add_breaker"),
                           ("Шина", "add_bus"),
                           ("Кабель", "draw_cable")]:
            tk.Radiobutton(toolbar, text=text, variable=self.mode_var,
                           value=val, bg="#ECEFF1",
                           command=lambda: self.set_mode(self.mode_var.get())
                           ).pack(side=tk.LEFT, padx=2)

        tk.Label(toolbar, text="  Кабель:", bg="#ECEFF1").pack(side=tk.LEFT, padx=5)
        self.cable_type_var = tk.StringVar(value="L1")
        for key in ["L1", "L2", "L3", "N", "PE"]:
            color = CABLE_TYPES[key]["color"]
            fg = "white" if key != "PE" else "black"
            tk.Radiobutton(toolbar, text=key, variable=self.cable_type_var,
                           value=key, bg="#ECEFF1", fg=fg,
                           font=("Arial", 10, "bold"), selectcolor=color,
                           command=self.on_cable_type_change).pack(side=tk.LEFT, padx=2)

        tk.Label(toolbar, text="  Толщина:", bg="#ECEFF1").pack(side=tk.LEFT, padx=5)
        self.width_var = tk.IntVar(value=self.cable_width)
        tk.Spinbox(toolbar, from_=1, to=20, width=3,
                   textvariable=self.width_var,
                   command=self.on_width_change).pack(side=tk.LEFT)
        self.width_var.trace_add("write", lambda *a: self.on_width_change())

        tk.Label(toolbar, text="  Реек:", bg="#ECEFF1").pack(side=tk.LEFT, padx=5)
        self.rails_var = tk.IntVar(value=self.shield["rails"])
        tk.Spinbox(toolbar, from_=1, to=10, width=3, textvariable=self.rails_var,
                   command=self.on_rails_change).pack(side=tk.LEFT)
        self.rails_var.trace_add("write", lambda *a: self.on_rails_change())

        tk.Label(toolbar, text="  Масштаб:", bg="#ECEFF1").pack(side=tk.LEFT, padx=5)
        self.scale_label = tk.Label(toolbar, text="100%", bg="#ECEFF1",
                                     font=("Arial", 10, "bold"))
        self.scale_label.pack(side=tk.LEFT)
        tk.Button(toolbar, text="+", command=lambda: self.zoom(ZOOM_STEP),
                  width=2).pack(side=tk.LEFT, padx=1)
        tk.Button(toolbar, text="−", command=lambda: self.zoom(1 / ZOOM_STEP),
                  width=2).pack(side=tk.LEFT, padx=1)
        tk.Button(toolbar, text="1:1", command=lambda: self.zoom(1.0 / self.scale),
                  width=3).pack(side=tk.LEFT, padx=1)

        tk.Button(toolbar, text="Шаблоны",
                  command=self.open_templates, bg="#8E24AA", fg="white"
                  ).pack(side=tk.RIGHT, padx=5)
        tk.Button(toolbar, text="Отменить", command=self.undo,
                  bg="#FFB300").pack(side=tk.RIGHT, padx=5)
        tk.Button(toolbar, text="Удалить", command=self.delete_selected,
                  bg="#E53935", fg="white").pack(side=tk.RIGHT, padx=5)

        canvas_frame = tk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.h_scroll = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        self.v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        self.canvas = tk.Canvas(canvas_frame, bg="#FFFFFF",
                                 xscrollcommand=self.h_scroll.set,
                                 yscrollcommand=self.v_scroll.set)
        self.h_scroll.config(command=self.canvas.xview)
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Leave>", self.on_leave)

        self.hover = HoverTip(self.canvas)

    def on_zoom_wheel(self, event):
        factor = ZOOM_STEP if event.delta > 0 else 1 / ZOOM_STEP
        self.zoom_at(event.x, event.y, factor)

    def zoom_at(self, x, y, factor):
        old_scale = self.scale
        new_scale = max(MIN_SCALE, min(MAX_SCALE, old_scale * factor))
        if abs(new_scale - old_scale) < 0.001:
            return
        self.scale = new_scale
        self._draw_all()
        self.scale_label.config(text=f"{int(self.scale * 100)}%")

    def zoom(self, factor):
        self.scale = max(MIN_SCALE, min(MAX_SCALE, self.scale * factor))
        self._draw_all()
        self.scale_label.config(text=f"{int(self.scale * 100)}%")

    def S(self, v):
        return v * self.scale

    def on_cable_type_change(self):
        self.cable_type = self.cable_type_var.get()

    def on_width_change(self):
        try:
            self.cable_width = max(1, int(self.width_var.get()))
        except Exception:
            pass

    def on_rails_change(self):
        try:
            self.shield["rails"] = max(1, min(10, int(self.rails_var.get())))
        except Exception:
            pass
        self._draw_all()

    def set_mode(self, mode):
        if self.mode == "draw_cable" and mode != "draw_cable":
            self.finish_cable()
        self.mode = mode
        self.mode_var.set(mode)
        self.cable_points = []
        self.preview_pos = None
        self._draw_all()

    def push_undo(self):
        self.undo_stack.append(copy.deepcopy(self.shield))
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            return
        prev = self.undo_stack.pop()
        self.shield.clear()
        self.shield.update(prev)
        self.shield.setdefault("buses", [])
        self.rails_var.set(self.shield["rails"])
        for cable in self.shield["cables"]:
            if cable.get("start_ref"):
                cable["start_ref"] = tuple(cable["start_ref"])
            if cable.get("end_ref"):
                cable["end_ref"] = tuple(cable["end_ref"])
        self._recalc_energized()
        self._draw_all()

    def _rail_y(self, idx):
        return self.S(self.shield["rail_y_start"] + idx * self.shield["rail_spacing"])

    def _breaker_size(self, br):
        mw = self.S(self.shield["module_width"])
        width = mw * br.get("poles", 1)
        height = self.S(self.shield["rail_spacing"] * 0.5)
        return width, height

    def _breaker_bbox(self, br):
        w, h = self._breaker_size(br)
        x = self.S(br["x"])
        y = self._rail_y(br["rail"])
        return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)

    def _breaker_bbox_unscaled(self, br):
        mw = self.shield["module_width"]
        width = mw * br.get("poles", 1)
        height = self.shield["rail_spacing"] * 0.5
        x = br["x"]
        y = self.shield["rail_y_start"] + br["rail"] * self.shield["rail_spacing"]
        return (x - width / 2, y - height / 2, x + width / 2, y + height / 2)

    def _breaker_terminals(self, br):
        x1, y1, x2, y2 = self._breaker_bbox_unscaled(br)
        poles = br.get("poles", 1)
        w = x2 - x1
        return [(x1 + (p + 0.5) * (w / poles), y1) for p in range(poles)]

    def _breaker_terminals_bottom(self, br):
        x1, y1, x2, y2 = self._breaker_bbox_unscaled(br)
        poles = br.get("poles", 1)
        w = x2 - x1
        return [(x1 + (p + 0.5) * (w / poles), y2) for p in range(poles)]

    def _bus_size_unscaled(self, bus):
        n_out = bus.get("bus_outputs", 6)
        w = max(60, (n_out - 1) * BUS_CONTACT_STEP + 2 * BUS_PADDING)
        h = BUS_HEIGHT
        return w, h

    def _bus_bbox(self, bus):
        w_u, h_u = self._bus_size_unscaled(bus)
        w = self.S(w_u)
        h = self.S(h_u)
        x = self.S(bus["x"])
        y = self.S(bus["y"])
        return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)

    def _bus_bbox_unscaled(self, bus):
        w, h = self._bus_size_unscaled(bus)
        x = bus["x"]
        y = bus["y"]
        return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)

    def _bus_top_contact(self, bus):
        x1, y1, x2, y2 = self._bus_bbox_unscaled(bus)
        return ((x1 + x2) / 2, y1)

    def _bus_bottom_contacts(self, bus):
        x1, y1, x2, y2 = self._bus_bbox_unscaled(bus)
        n_out = bus.get("bus_outputs", 6)
        result = []
        if n_out > 1:
            step = (x2 - x1 - 2 * BUS_PADDING) / (n_out - 1)
            for k in range(n_out):
                cx = x1 + BUS_PADDING + k * step
                result.append((cx, y2))
        else:
            result.append(((x1 + x2) / 2, y2))
        return result

    def _find_breaker(self, x, y):
        for i, br in enumerate(self.shield["breakers"]):
            x1, y1, x2, y2 = self._breaker_bbox(br)
            if x1 <= x <= x2 and y1 <= y <= y2:
                return i
        return None

    def _find_bus(self, x, y):
        for i, bus in enumerate(self.shield.get("buses", [])):
            x1, y1, x2, y2 = self._bus_bbox(bus)
            if x1 <= x <= x2 and y1 <= y <= y2:
                return i
        return None

    def _find_cable(self, x, y, tol=8):
        for i, cable in enumerate(self.shield["cables"]):
            pts = cable.get("points", [])
            for j in range(len(pts) - 1):
                d = self._seg_dist(x, y,
                                    self.S(pts[j][0]), self.S(pts[j][1]),
                                    self.S(pts[j + 1][0]), self.S(pts[j + 1][1]))
                if d <= tol:
                    return i
        return None

    @staticmethod
    def _seg_dist(px, py, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(px - x1, py - y1)
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))

    def _find_endpoint_ref(self, pt):
        for i, bus in enumerate(self.shield.get("buses", [])):
            cx_top, cy_top = self._bus_top_contact(bus)
            if math.hypot(pt[0] - cx_top, pt[1] - cy_top) < GRAB_TOLERANCE:
                return ("bus", i, "top", 0)
            for k, (cx, cy) in enumerate(self._bus_bottom_contacts(bus)):
                if math.hypot(pt[0] - cx, pt[1] - cy) < GRAB_TOLERANCE:
                    return ("bus", i, "bottom", k)
        for i, br in enumerate(self.shield["breakers"]):
            for pole, (cx, cy) in enumerate(self._breaker_terminals(br)):
                if math.hypot(pt[0] - cx, pt[1] - cy) < GRAB_TOLERANCE:
                    return ("breaker", i, "top", pole)
            for pole, (cx, cy) in enumerate(self._breaker_terminals_bottom(br)):
                if math.hypot(pt[0] - cx, pt[1] - cy) < GRAB_TOLERANCE:
                    return ("breaker", i, "bottom", pole)
        for i in range(5):
            kx = 60 + i * 50
            ky = 60
            if math.hypot(pt[0] - kx, pt[1] - ky) < GRAB_TOLERANCE:
                return ("input", i, None, None)
        return None

    def _ref_position(self, ref):
        if ref is None:
            return None
        kind = ref[0]
        idx = ref[1]
        side = ref[2] if len(ref) > 2 else None
        pole = ref[3] if len(ref) > 3 else 0

        if kind == "input":
            return (60 + idx * 50, 60)
        if kind == "breaker":
            brs = self.shield["breakers"]
            if 0 <= idx < len(brs):
                br = brs[idx]
                if side == "top":
                    ts = self._breaker_terminals(br)
                    if 0 <= pole < len(ts):
                        return ts[pole]
                elif side == "bottom":
                    ts = self._breaker_terminals_bottom(br)
                    if 0 <= pole < len(ts):
                        return ts[pole]
                x1, y1, x2, y2 = self._breaker_bbox_unscaled(br)
                return ((x1 + x2) / 2, (y1 + y2) / 2)
        if kind == "bus":
            buses = self.shield.get("buses", [])
            if 0 <= idx < len(buses):
                bus = buses[idx]
                if side == "top":
                    return self._bus_top_contact(bus)
                elif side == "bottom":
                    contacts = self._bus_bottom_contacts(bus)
                    if 0 <= pole < len(contacts):
                        return contacts[pole]
                return (bus["x"], bus["y"])
        return None

    def _ref_energized(self, ref):
        if ref is None:
            return False
        kind = ref[0]
        idx = ref[1]
        if kind == "input":
            return True
        if kind == "bus":
            return True
        if kind == "breaker":
            brs = self.shield["breakers"]
            if 0 <= idx < len(brs):
                return brs[idx].get("state", False)
        return False

    def _is_cable_energized(self, cable):
        return self._ref_energized(cable.get("start_ref"))

    def _recalc_energized(self):
        for cable in self.shield["cables"]:
            cable["energized"] = self._is_cable_energized(cable)

    def _is_source_ref(self, ref):
        if ref is None:
            return False
        kind = ref[0]
        return kind in ("input", "bus", "breaker")

    def _rebuild_cable(self, cable):
        pts = cable.get("points", [])
        if len(pts) < 2:
            return
        start_ref = cable.get("start_ref")
        end_ref = cable.get("end_ref")
        if not start_ref and not end_ref:
            return
        old_start = pts[0]
        old_end = pts[-1]
        new_start = self._ref_position(start_ref) if start_ref else old_start
        new_end = self._ref_position(end_ref) if end_ref else old_end
        if new_start is None:
            new_start = old_start
        if new_end is None:
            new_end = old_end
        dx_s = new_start[0] - old_start[0]
        dy_s = new_start[1] - old_start[1]
        dx_e = new_end[0] - old_end[0]
        dy_e = new_end[1] - old_end[1]
        if abs(dx_s) < 0.5 and abs(dy_s) < 0.5 and \
           abs(dx_e) < 0.5 and abs(dy_e) < 0.5:
            return
        n = len(pts)
        for i in range(n):
            t = i / (n - 1) if n > 1 else 0
            dx = dx_s * (1 - t) + dx_e * t
            dy = dy_s * (1 - t) + dy_e * t
            pts[i] = (pts[i][0] + dx, pts[i][1] + dy)
        pts[0] = new_start
        pts[-1] = new_end
        cable["points"] = orthogonalize(pts)

    def _cable_offsets(self, idx, cable):
        pts = cable.get("points", [])
        n = len(pts) - 1
        offsets = [(0, 0)] * n
        prev_counts = {}
        for j in range(idx):
            prev = self.shield["cables"][j]
            prev_pts = prev.get("points", [])
            for k in range(len(prev_pts) - 1):
                kk = seg_key(prev_pts[k][0], prev_pts[k][1],
                              prev_pts[k + 1][0], prev_pts[k + 1][1])
                prev_counts[kk] = prev_counts.get(kk, 0) + 1
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            kk = seg_key(x1, y1, x2, y2)
            count = prev_counts.get(kk, 0)
            if count > 0:
                shift = count * CABLE_OVERLAP_SHIFT * self.scale
                if abs(x2 - x1) < 1:
                    offsets[i] = (shift, 0)
                else:
                    offsets[i] = (0, shift)
        return offsets

    def _draw_all(self):
        self.canvas.delete("all")
        canvas_w = max(self.canvas.winfo_width(), 800)
        rail_w = int(canvas_w * 0.8 / self.scale)
        rail_x0 = int(canvas_w * 0.05 / self.scale)
        rail_x1 = rail_x0 + rail_w
        self.shield["rail_x0"] = rail_x0
        self.shield["rail_x1"] = rail_x1
        h = self._rail_y(self.shield["rails"] - 1) + self.S(200)
        total_w = max(self.S(rail_x1) + self.S(100), canvas_w)
        self.canvas.config(scrollregion=(0, 0, total_w, h))

        for i in range(self.shield["rails"]):
            y = self._rail_y(i)
            self.canvas.create_line(self.S(rail_x0), y, self.S(rail_x1), y,
                                     fill="#B0BEC5", width=max(3, int(self.S(8))))
            self.canvas.create_text(self.S(rail_x0) + 5, y - self.S(20),
                                     text=f"Рейка {i+1}",
                                     font=("Arial", max(8, int(self.S(10)))),
                                     fill="#607D8B", anchor=tk.W)

        self._draw_input()

        for i, bus in enumerate(self.shield.get("buses", [])):
            self._draw_bus(i, bus)

        for i, cable in enumerate(self.shield["cables"]):
            self._draw_cable(i, cable)

        for i, br in enumerate(self.shield["breakers"]):
            self._draw_breaker(i, br)

        if self.mode == "draw_cable" and self.cable_points:
            all_pts = list(self.cable_points)
            if self.preview_pos is not None:
                all_pts.append(self.preview_pos)
            ortho = orthogonalize(all_pts)
            if len(ortho) >= 2:
                flat = []
                for p in ortho:
                    flat.extend((self.S(p[0]), self.S(p[1])))
                color = CABLE_TYPES[self.cable_type]["color"]
                if self.preview_pos is not None:
                    self.canvas.create_line(*flat, fill=color,
                                             width=self.S(self.cable_width),
                                             capstyle=tk.ROUND, joinstyle=tk.MITER,
                                             dash=(6, 4))
                else:
                    self.canvas.create_line(*flat, fill=color,
                                             width=self.S(self.cable_width),
                                             capstyle=tk.ROUND, joinstyle=tk.MITER)
            for p in self.cable_points:
                x, y = self.S(p[0]), self.S(p[1])
                r = max(2, int(self.S(4)))
                self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                         fill="#FF6F00", outline="")

    def _draw_input(self):
        x0 = self.S(60)
        y0 = self.S(60)
        gap = self.S(50)
        size = self.S(15)
        for i, t in enumerate(["L1", "L2", "L3", "N", "PE"]):
            x = x0 + i * gap
            color = CABLE_TYPES[t]["color"]
            fg = "white" if t != "PE" else "black"
            self.canvas.create_rectangle(x - size, y0 - size, x + size, y0 + size,
                                           fill=color, outline="#263238",
                                           width=max(1, int(self.S(2))))
            self.canvas.create_text(x, y0, text=t, fill=fg,
                                     font=("Arial", max(7, int(self.S(10))), "bold"))

    def _draw_bus(self, idx, bus):
        x1, y1, x2, y2 = self._bus_bbox(bus)
        color = bus.get("color", "#FFC107")
        self.canvas.create_rectangle(x1, y1, x2, y2,
                                       fill=color, outline="#263238",
                                       width=max(1, int(self.S(2))))
        label = bus.get("label", "Шина")
        n_out = bus.get("bus_outputs", 6)
        fg = "white" if color in ("#000000", "#1E88E5", "#E53935", "#43A047") else "black"
        self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2,
                                 text=f"{label} ({n_out})",
                                 font=("Arial", max(8, int(self.S(10))), "bold"),
                                 fill=fg)
        r = max(2, int(self.S(3)))
        cx_top = (x1 + x2) / 2
        self.canvas.create_oval(cx_top - r, y1 - r, cx_top + r, y1 + r,
                                 fill="#795548", outline="")
        if n_out > 1:
            step = (x2 - x1 - self.S(2 * BUS_PADDING)) / (n_out - 1)
            for k in range(n_out):
                cx = x1 + self.S(BUS_PADDING) + k * step
                self.canvas.create_oval(cx - r, y2 - r, cx + r, y2 + r,
                                         fill="#795548", outline="")
        if self.selected_bus == idx:
            pad = self.S(4)
            self.canvas.create_rectangle(x1 - pad, y1 - pad, x2 + pad, y2 + pad,
                                           outline="#FF6F00",
                                           width=max(2, int(self.S(2))))

    def _draw_breaker(self, idx, br):
        x1, y1, x2, y2 = self._breaker_bbox(br)
        state = br.get("state", False)
        ttype = br.get("type", "auto")
        fill = BREAKER_ON_FILL if state else BREAKER_OFF_FILL
        border = BREAKER_BORDER
        if ttype == "rcd":
            border = "#E65100"
        elif ttype == "diff":
            border = "#6A1B9A"
        elif ttype == "main":
            border = "#0277BD"
        elif ttype == "stabilizer":
            border = "#00695C"
        elif ttype == "meter":
            border = "#2E7D32"
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill,
                                       outline=border, width=max(1, int(self.S(2))))
        poles = br.get("poles", 1)
        w = x2 - x1
        cr = max(2, int(self.S(4)))
        for p in range(poles):
            cx = x1 + (p + 0.5) * (w / poles)
            self.canvas.create_oval(cx - cr, y1 - cr * 1.5, cx + cr, y1 + cr * 0.5,
                                     fill="#795548", outline="")
            self.canvas.create_oval(cx - cr, y2 - cr * 0.5, cx + cr, y2 + cr * 1.5,
                                     fill="#795548", outline="")
        nominal = br.get("nominal", "")
        char = br.get("char") or ""
        leak = br.get("leak")
        desc = br.get("desc", "")
        fs = max(8, int(self.S(11)))
        fs_small = max(6, int(self.S(8)))
        main_label = f"{char}{int(nominal)}" if char else f"{int(nominal)}А"
        y_center = (y1 + y2) / 2
        lines = [(main_label, fs, "#000", "bold")]
        if leak:
            lines.append((f"{int(leak)}мА", fs_small, "#B71C1C", "normal"))
        if desc:
            lines.append((desc, fs_small, "#333", "normal"))
        total_h = sum(l[1] + self.S(2) for l in lines)
        y0 = y_center - total_h / 2 + fs / 2
        for text, size, color, weight in lines:
            self.canvas.create_text((x1 + x2) / 2, y0, text=text,
                                     font=("Arial", int(size), weight),
                                     fill=color)
            y0 += size + self.S(2)
        if self.selected_breaker == idx:
            pad = self.S(5)
            self.canvas.create_rectangle(x1 - pad, y1 - pad, x2 + pad, y2 + pad,
                                           outline="#FF6F00",
                                           width=max(2, int(self.S(2))))

    def _draw_cable(self, idx, cable):
        pts = cable.get("points", [])
        if len(pts) < 2:
            return
        base_color = CABLE_TYPES[cable.get("type", "L1")]["color"]
        width = max(1, int(self.S(cable.get("width", self.cable_width))))
        energized = self._is_cable_energized(cable)
        if self.selected_cable == idx:
            color = CABLE_SELECTED_COLOR
        elif energized:
            color = base_color
        else:
            color = lighten_color(base_color, 0.65)
        offsets = self._cable_offsets(idx, cable)
        for i in range(len(pts) - 1):
            x1, y1 = self.S(pts[i][0]), self.S(pts[i][1])
            x2, y2 = self.S(pts[i + 1][0]), self.S(pts[i + 1][1])
            dx_off, dy_off = offsets[i]
            if abs(x2 - x1) < 1:
                x1 += dx_off
                x2 += dx_off
            else:
                y1 += dy_off
                y2 += dy_off
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width,
                                     capstyle=tk.ROUND, joinstyle=tk.MITER)

    def on_leave(self, event):
        if self.hover:
            self.hover.hide()
        if self.mode == "draw_cable":
            self.preview_pos = None
            self._draw_all()

    def on_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        if self.mode == "add_breaker":
            self.add_breaker_at(x / self.scale, y / self.scale)
            return
        if self.mode == "add_bus":
            self.add_bus_at(x / self.scale, y / self.scale)
            return
        if self.mode == "draw_cable":
            self.cable_points.append((x / self.scale, y / self.scale))
            self.preview_pos = None
            self._draw_all()
            return

        br_idx = self._find_breaker(x, y)
        if br_idx is not None:
            self.push_undo()
            br = self.shield["breakers"][br_idx]
            self.drag_breaker = br_idx
            self.drag_offset = (x - self.S(br["x"]), y - self._rail_y(br["rail"]))
            self.drag_start_x = x
            self._pending_toggle = True
            self.selected_breaker = br_idx
            self.selected_cable = None
            self.selected_bus = None
            self._draw_all()
            return

        bus_idx = self._find_bus(x, y)
        if bus_idx is not None:
            self.drag_bus = bus_idx
            bus = self.shield["buses"][bus_idx]
            self.drag_offset = (x - self.S(bus["x"]), y - self.S(bus["y"]))
            self.selected_bus = bus_idx
            self.selected_breaker = None
            self.selected_cable = None
            self._draw_all()
            return

        cab_idx = self._find_cable(x, y)
        if cab_idx is not None:
            self.selected_cable = cab_idx
            self.selected_breaker = None
            self.selected_bus = None
            self._draw_all()
            return

        self.selected_breaker = None
        self.selected_cable = None
        self.selected_bus = None
        self._draw_all()

    def on_double_click(self, event):
        if self.mode == "draw_cable":
            self.finish_cable()

    def add_breaker_at(self, x, y):
        best_rail = 0
        best_dist = 1e9
        for i in range(self.shield["rails"]):
            d = abs(y - (self.shield["rail_y_start"] + i * self.shield["rail_spacing"]))
            if d < best_dist:
                best_dist = d
                best_rail = i
        dlg = BreakerPickDialog(self, self.templates)
        self.wait_window(dlg)
        if not dlg.result:
            return
        tpl = dlg.result
        poles = tpl.get("poles", 1)
        mw = self.shield["module_width"]
        width = mw * poles
        gap = 10
        occupied = []
        for br in self.shield["breakers"]:
            if br["rail"] == best_rail:
                bx1, by1, bx2, by2 = self._breaker_bbox_unscaled(br)
                occupied.append((bx1, bx2))
        occupied.sort()
        candidate_x = x
        placed = False
        for _ in range(2000):
            x1 = candidate_x - width / 2
            x2 = candidate_x + width / 2
            conflict = False
            for (ox1, ox2) in occupied:
                if not (x2 + gap <= ox1 or x1 >= ox2 + gap):
                    conflict = True
                    break
            if not conflict:
                placed = True
                break
            candidate_x += 5
        if not placed:
            messagebox.showwarning("Нет места", "На этой рейке нет свободного места.")
            return
        self.push_undo()
        br = {
            "x": candidate_x,
            "rail": best_rail,
            "type": tpl.get("type", "auto"),
            "poles": poles,
            "nominal": tpl.get("nominal", 16),
            "leak": tpl.get("leak"),
            "char": tpl.get("char"),
            "desc": tpl.get("desc", ""),
            "state": False,
            "group": tpl.get("group", "auto"),
        }
        self.shield["breakers"].append(br)
        self._recalc_energized()
        self._draw_all()

    def add_bus_at(self, x, y):
        dlg = BusPickDialog(self, self.templates)
        self.wait_window(dlg)
        if not dlg.result:
            return
        tpl = dlg.result
        self.push_undo()
        n_out = tpl.get("bus_outputs", 6)
        bus = {
            "x": x,
            "y": y,
            "label": tpl.get("desc", "Шина"),
            "color": tpl.get("bus_color", "#FFC107"),
            "bus_outputs": n_out,
        }
        self.shield.setdefault("buses", []).append(bus)
        self._recalc_energized()
        self._draw_all()

    def finish_cable(self):
        if len(self.cable_points) < 2:
            self.cable_points = []
            self.preview_pos = None
            self._draw_all()
            return
        raw_start = self.cable_points[0]
        raw_end = self.cable_points[-1]
        start_ref = self._find_endpoint_ref(raw_start)
        end_ref = self._find_endpoint_ref(raw_end)
        if not self._is_source_ref(start_ref) and self._is_source_ref(end_ref):
            self.cable_points = list(reversed(self.cable_points))
            start_ref, end_ref = end_ref, start_ref
        ortho = orthogonalize(self.cable_points)
        if start_ref:
            p = self._ref_position(start_ref)
            if p:
                ortho[0] = p
        if end_ref:
            p = self._ref_position(end_ref)
            if p:
                ortho[-1] = p
        ortho = orthogonalize(ortho)
        self.push_undo()
        self.shield["cables"].append({
            "type": self.cable_type,
            "points": ortho,
            "width": self.cable_width,
            "start_ref": start_ref,
            "end_ref": end_ref,
        })
        self.cable_points = []
        self.preview_pos = None
        self._recalc_energized()
        self._draw_all()

    def on_drag(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if self.drag_breaker is not None:
            br = self.shield["breakers"][self.drag_breaker]
            if abs(x - self.drag_start_x) > 5:
                self._pending_toggle = False
            if not self._pending_toggle:
                new_x = x / self.scale
                if self._can_place_at(br, new_x):
                    br["x"] = new_x
                    for cable in self.shield["cables"]:
                        refs = [cable.get("start_ref"), cable.get("end_ref")]
                        for r in refs:
                            if r and r[0] == "breaker" and r[1] == self.drag_breaker:
                                self._rebuild_cable(cable)
                                break
                    self._recalc_energized()
                    self._draw_all()
            return
        if self.drag_bus is not None:
            bus = self.shield["buses"][self.drag_bus]
            bus["x"] = x / self.scale - self.drag_offset[0] / self.scale
            bus["y"] = y / self.scale - self.drag_offset[1] / self.scale
            for cable in self.shield["cables"]:
                refs = [cable.get("start_ref"), cable.get("end_ref")]
                for r in refs:
                    if r and r[0] == "bus" and r[1] == self.drag_bus:
                        self._rebuild_cable(cable)
                        break
            self._recalc_energized()
            self._draw_all()

    def _can_place_at(self, br, new_x):
        mw = self.shield["module_width"]
        width = mw * br.get("poles", 1)
        gap = 10
        new_x1 = new_x - width / 2
        new_x2 = new_x + width / 2
        for other in self.shield["breakers"]:
            if other is br:
                continue
            if other["rail"] != br["rail"]:
                continue
            ox1, _, ox2, _ = self._breaker_bbox_unscaled(other)
            if not (new_x2 + gap <= ox1 or new_x1 >= ox2 + gap):
                return False
        return True

    def on_release(self, event):
        if self.drag_breaker is not None:
            if self._pending_toggle:
                br = self.shield["breakers"][self.drag_breaker]
                br["state"] = not br.get("state", False)
            self._recalc_energized()
            self._draw_all()
        if self.drag_bus is not None:
            self._recalc_energized()
            self._draw_all()
        self.drag_breaker = None
        self.drag_bus = None
        self._pending_toggle = False

    def on_right_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if self.mode == "draw_cable":
            self.finish_cable()
            return
        br_idx = self._find_breaker(x, y)
        if br_idx is not None:
            self.selected_breaker = br_idx
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Редактировать устройство...",
                              command=lambda: self.edit_breaker(br_idx))
            menu.add_command(label="Удалить устройство (и кабели)",
                              command=lambda: self.delete_breaker(br_idx))
            menu.tk_popup(event.x_root, event.y_root)
            return
        bus_idx = self._find_bus(x, y)
        if bus_idx is not None:
            self.selected_bus = bus_idx
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Изменить цвет...",
                              command=lambda: self.change_bus_color(bus_idx))
            menu.add_command(label="Удалить шину",
                              command=lambda: self.delete_bus(bus_idx))
            menu.tk_popup(event.x_root, event.y_root)
            return
        cab_idx = self._find_cable(x, y)
        if cab_idx is not None:
            self.selected_cable = cab_idx
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Изменить тип кабеля...",
                              command=lambda: self.change_cable_type(cab_idx))
            menu.add_command(label="Изменить толщину кабеля...",
                              command=lambda: self.change_cable_width(cab_idx))
            menu.add_command(label="Удалить кабель",
                              command=lambda: self.delete_cable(cab_idx))
            menu.tk_popup(event.x_root, event.y_root)

    def edit_breaker(self, idx):
        br = self.shield["breakers"][idx]
        dlg = BreakerEditDialog(self, br)
        self.wait_window(dlg)
        if dlg.result:
            self.push_undo()
            br.update(dlg.result)
            self._recalc_energized()
            self._draw_all()

    def delete_breaker(self, idx):
        if not messagebox.askyesno("Удалить", "Удалить устройство и связанные кабели?"):
            return
        self.push_undo()
        new_cables = []
        for cable in self.shield["cables"]:
            refs = [cable.get("start_ref"), cable.get("end_ref")]
            if any(r and r[0] == "breaker" and r[1] == idx for r in refs):
                continue
            def shift(ref):
                if ref is None:
                    return None
                kind = ref[0]
                i = ref[1]
                rest = tuple(ref[2:]) if len(ref) > 2 else (None, 0)
                if kind == "breaker" and i > idx:
                    return (kind, i - 1) + rest
                return ref
            cable["start_ref"] = shift(cable.get("start_ref"))
            cable["end_ref"] = shift(cable.get("end_ref"))
            new_cables.append(cable)
        self.shield["cables"] = new_cables
        del self.shield["breakers"][idx]
        self.selected_breaker = None
        self._recalc_energized()
        self._draw_all()

    def delete_bus(self, idx):
        self.push_undo()
        new_cables = []
        for cable in self.shield["cables"]:
            refs = [cable.get("start_ref"), cable.get("end_ref")]
            if any(r and r[0] == "bus" and r[1] == idx for r in refs):
                continue
            def shift(ref):
                if ref is None:
                    return None
                kind = ref[0]
                i = ref[1]
                rest = tuple(ref[2:]) if len(ref) > 2 else (None, 0)
                if kind == "bus" and i > idx:
                    return (kind, i - 1) + rest
                return ref
            cable["start_ref"] = shift(cable.get("start_ref"))
            cable["end_ref"] = shift(cable.get("end_ref"))
            new_cables.append(cable)
        self.shield["cables"] = new_cables
        del self.shield["buses"][idx]
        self.selected_bus = None
        self._recalc_energized()
        self._draw_all()

    def change_bus_color(self, idx):
        bus = self.shield["buses"][idx]
        color = colorchooser.askcolor(color=bus.get("color", "#FFC107"),
                                       title="Цвет шины")[1]
        if color:
            self.push_undo()
            bus["color"] = color
            self._draw_all()

    def delete_cable(self, idx):
        self.push_undo()
        del self.shield["cables"][idx]
        self.selected_cable = None
        self._draw_all()

    def change_cable_type(self, idx):
        cable = self.shield["cables"][idx]
        dlg = CableTypeDialog(self, cable.get("type", "L1"))
        self.wait_window(dlg)
        if dlg.result:
            self.push_undo()
            cable["type"] = dlg.result
            self._recalc_energized()
            self._draw_all()

    def change_cable_width(self, idx):
        cable = self.shield["cables"][idx]
        cur = cable.get("width", self.cable_width)
        val = simpledialog.askinteger("Толщина", "Толщина (1–20):",
                                       initialvalue=cur, minvalue=1, maxvalue=20,
                                       parent=self)
        if val:
            self.push_undo()
            cable["width"] = val
            self._draw_all()

    def delete_selected(self):
        if self.selected_breaker is not None:
            self.delete_breaker(self.selected_breaker)
        elif self.selected_bus is not None:
            self.delete_bus(self.selected_bus)
        elif self.selected_cable is not None:
            self.delete_cable(self.selected_cable)

    def on_motion(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if self.mode == "draw_cable" and self.cable_points:
            self.preview_pos = (x / self.scale, y / self.scale)
            self._draw_all()
        br_idx = self._find_breaker(x, y)
        if br_idx is not None:
            br = self.shield["breakers"][br_idx]
            info = (f"{br.get('desc','')}\n"
                    f"Тип: {br.get('type','')}\n"
                    f"Полюсов: {br.get('poles',1)}\n"
                    f"Номинал: {br.get('nominal','')}А\n"
                    f"Состояние: {'ВКЛ' if br.get('state') else 'ВЫКЛ'}")
            if br.get("leak"):
                info += f"\nУтечка: {br['leak']}мА"
            self.hover.show(event.x_root + 15, event.y_root + 15, info)
            return
        bus_idx = self._find_bus(x, y)
        if bus_idx is not None:
            bus = self.shield["buses"][bus_idx]
            self.hover.show(event.x_root + 15, event.y_root + 15,
                            f"Шина: {bus.get('label', '')}\n"
                            f"Выходов: {bus.get('bus_outputs', 6)}")
            return
        cab_idx = self._find_cable(x, y)
        if cab_idx is not None:
            cable = self.shield["cables"][cab_idx]
            energized = self._is_cable_energized(cable)
            self.hover.show(event.x_root + 15, event.y_root + 15,
                            f"Кабель {cable.get('type','')}\n"
                            f"Толщина: {cable.get('width', 2)}\n"
                            f"{'Под напряжением' if energized else 'Без напряжения'}")
            return
        self.hover.hide()

    def new_shield(self):
        if not messagebox.askyesno("Новый щит", "Очистить?"):
            return
        self.push_undo()
        self.shield = {
            "rails": 3, "rail_spacing": 180, "module_width": 28,
            "rail_y_start": 200, "breakers": [], "cables": [], "buses": [],
        }
        self.rails_var.set(3)
        self.current_file = None
        self._draw_all()

    def save_shield(self):
        if not self.current_file:
            self.save_shield_as()
            return
        data = copy.deepcopy(self.shield)
        for cable in data["cables"]:
            if cable.get("start_ref"):
                cable["start_ref"] = list(cable["start_ref"])
            if cable.get("end_ref"):
                cable["end_ref"] = list(cable["end_ref"])
        save_json(self.current_file, data)
        self.app.status.config(text=f"Сохранено: {self.current_file}")

    def save_shield_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Shield", "*.json")],
            initialfile=SHIELD_FILE_DEFAULT)
        if not path:
            return
        data = copy.deepcopy(self.shield)
        for cable in data["cables"]:
            if cable.get("start_ref"):
                cable["start_ref"] = list(cable["start_ref"])
            if cable.get("end_ref"):
                cable["end_ref"] = list(cable["end_ref"])
        save_json(path, data)
        self.current_file = path
        self.app.status.config(text=f"Сохранено: {path}")

    def open_shield(self):
        path = filedialog.askopenfilename(filetypes=[("Shield", "*.json")])
        if not path:
            return
        data = load_json(path, None)
        if not data:
            return
        self.shield.clear()
        self.shield.update(data)
        self.shield.setdefault("buses", [])
        self.rails_var.set(self.shield.get("rails", 3))
        for cable in self.shield["cables"]:
            if cable.get("start_ref"):
                cable["start_ref"] = tuple(cable["start_ref"])
            if cable.get("end_ref"):
                cable["end_ref"] = tuple(cable["end_ref"])
        self.current_file = path
        self._recalc_energized()
        self._draw_all()
        self.app.status.config(text=f"Загружено: {path}")

    def open_templates(self):
        dlg = BreakerTemplatesDialog(self, self.templates)
        self.wait_window(dlg)
        self.templates = load_json(BREAKER_TEMPLATES_FILE, self.templates)


# ============================================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ============================================================
class PowerPlanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Проектирование электроснабжения")
        self.root.geometry("1700x950")

        self.templates = load_json(TEMPLATES_FILE, DEFAULT_TEMPLATES.copy())
        self.phase_colors = load_json(PHASE_COLORS_FILE, dict(DEFAULT_PHASE_COLORS))
        self.settings = load_json(SETTINGS_FILE, dict(DEFAULT_SETTINGS))

        for k, v in DEFAULT_PHASE_COLORS.items():
            if k not in self.phase_colors:
                self.phase_colors[k] = v
        for k, v in DEFAULT_SETTINGS.items():
            if k not in self.settings:
                self.settings[k] = v

        self._build_menu()
        self._build_tabs()
        self._build_status()

        self.root.bind("<Control-z>", lambda e: self.on_undo())
        self.root.bind("<Delete>", lambda e: self.on_delete())
        self.root.bind("<BackSpace>", lambda e: self.on_delete())
        self.root.bind("<Control-MouseWheel>", self.on_zoom_wheel_global)

    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Новый план дома", command=lambda: self.home_tab.new_plan())
        file_menu.add_command(label="Открыть план дома...", command=lambda: self.home_tab.open_plan())
        file_menu.add_command(label="Сохранить план дома",
                              command=lambda: self.home_tab.save_plan())
        file_menu.add_command(label="Сохранить план дома как...",
                              command=lambda: self.home_tab.save_plan_as())
        file_menu.add_separator()
        file_menu.add_command(label="Новый щит", command=lambda: self.panel_tab.new_shield())
        file_menu.add_command(label="Открыть щит...", command=lambda: self.panel_tab.open_shield())
        file_menu.add_command(label="Сохранить щит", command=lambda: self.panel_tab.save_shield())
        file_menu.add_command(label="Сохранить щит как...",
                              command=lambda: self.panel_tab.save_shield_as())
        file_menu.add_separator()
        file_menu.add_command(label="Загрузить фото (JPG/PNG)...",
                              command=lambda: self.home_tab.load_photo())
        file_menu.add_command(label="Убрать фото", command=lambda: self.home_tab.clear_photo())
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Отменить (Ctrl+Z)", command=self.on_undo)
        edit_menu.add_command(label="Удалить выделенное (Del)", command=self.on_delete)
        edit_menu.add_separator()
        edit_menu.add_command(label="Параметры расчёта дома...", command=self.edit_settings)
        edit_menu.add_command(label="Цвета фаз...", command=self.edit_phase_colors)
        edit_menu.add_command(label="Шаблоны приборов...", command=self.open_templates)
        edit_menu.add_command(label="Шаблоны автоматов...",
                              command=lambda: self.panel_tab.open_templates())
        edit_menu.add_separator()
        edit_menu.add_command(label="Переприменить шаблоны приборов",
                              command=self.reapply_templates)
        menubar.add_cascade(label="Настройки", menu=edit_menu)

        self.root.config(menu=menubar)

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.home_tab = HomePlanTab(self.notebook, self)
        self.panel_tab = PanelTab(self.notebook, self)

        self.notebook.add(self.home_tab, text="План дома")
        self.notebook.add(self.panel_tab, text="Электрощит")

    def _build_status(self):
        self.status = tk.Label(self.root, text="Готово", anchor=tk.W,
                                bg="#CFD8DC", font=("Arial", 10))
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def _active_tab(self):
        idx = self.notebook.index(self.notebook.select())
        return self.home_tab if idx == 0 else self.panel_tab

    def on_undo(self):
        self._active_tab().undo()

    def on_delete(self):
        self._active_tab().delete_selected()

    def on_zoom_wheel_global(self, event):
        tab = self._active_tab()
        if hasattr(tab, "on_zoom_wheel"):
            tab.on_zoom_wheel(event)

    def edit_settings(self):
        dlg = SettingsDialog(self.root, self.settings)
        self.root.wait_window(dlg)
        if dlg.result:
            self.settings = dlg.result
            save_json(SETTINGS_FILE, self.settings)
            self.home_tab.right_panel.refresh()

    def edit_phase_colors(self):
        dlg = PhaseColorsDialog(self.root, self.phase_colors)
        self.root.wait_window(dlg)
        if dlg.result:
            self.phase_colors = dlg.result
            save_json(PHASE_COLORS_FILE, self.phase_colors)
            self.home_tab._draw_all()
            self.home_tab.right_panel.refresh()

    def open_templates(self):
        self.home_tab.push_undo()
        dlg = TemplatesDialog(self.root, self.templates)
        self.root.wait_window(dlg)
        self.templates = load_json(TEMPLATES_FILE, self.templates)
        self.reapply_templates()

    def reapply_templates(self):
        changed, reset = reapply_templates_to_plan(self.home_tab.plan, self.templates)
        self.home_tab._draw_all()
        self.home_tab.right_panel.refresh()
        messagebox.showinfo(
            "Шаблоны применены",
            f"Обновлено приборов: {changed}\n"
            f"Сброшено в пустые розетки: {reset}")


# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = PowerPlanApp(root)
    root.mainloop()
