"""
TSP — رابط گرافیکی کامل
========================
ویژگی‌ها:
  • بوم تعاملی: کلیک=شهر جدید، درگ=جابجایی شهر
  • انیمیشن مرحله‌به‌مرحله حرکت فروشنده
  • نمودار همگرایی الگوریتم‌ها (canvas داخلی — بدون matplotlib)
  • جدول مقایسه همه الگوریتم‌ها
  • داده واقعی شهرهای ایران
  • ورودی دستی، تصادفی و نمونه
  • خروجی متنی قابل کپی
"""
 
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import math
import random
import time
from tsp_solver import (
    TSPGraph, TSPResult,
    brute_force, greedy_search, a_star, local_beam_search,
    hill_climbing, simulated_annealing, genetic_algorithm
)

# ══════════════════════════════════════════════
# پالت رنگی
# ══════════════════════════════════════════════
C = {
    "bg":       "#0d0d1a",
    "panel":    "#13132b",
    "card":     "#1a1a35",
    "border":   "#2a2a50",
    "accent":   "#e94560",
    "accent2":  "#0f3460",
    "accent3":  "#16213e",
    "text":     "#e8e8f0",
    "dim":      "#7070a0",
    "green":    "#00e676",
    "yellow":   "#ffd740",
    "blue":     "#40c4ff",
    "purple":   "#ce93d8",
    "orange":   "#ffab40",
    "city":     "#ffd740",
    "start":    "#00e676",
    "edge_bg":  "#1e1e3e",
    "path":     "#e94560",
    "grid":     "#161630",
}

ALGO_META = {
    "Brute Force":        {"color": "#ff6b6b", "sym": "💪"},
    "Greedy Search":      {"color": "#ffd740", "sym": "⚡"},
    "A* Search":          {"color": "#40c4ff", "sym": "🌟"},
    "Local Beam Search":  {"color": "#ce93d8", "sym": "🔦"},
    "Hill Climbing":      {"color": "#ffab40", "sym": "⛰"},
    "Simulated Annealing":{"color": "#ff80ab", "sym": "🌡"},
    "Genetic Algorithm":  {"color": "#69ff47", "sym": "🧬"},
}

MARGIN = 45


# ══════════════════════════════════════════════
# برنامه اصلی
# ══════════════════════════════════════════════

class TSPApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🗺  فروشنده دوره‌گرد — TSP Solver")
        self.configure(bg=C["bg"])
        self.minsize(1200, 720)

        self.graph = TSPGraph()
        self.results: dict[str, TSPResult] = {}
        self.active_result: TSPResult = None
        self.anim_running = False
        self.anim_idx = 0
        self.hover_city: str = None
        self.drag_city:  str = None

        self._style()
        self._build()
        self._load_sample_data()
        self.after(100, self._redraw_map)

    # ─── ttk style ───
    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Treeview",
            background=C["card"], foreground=C["text"],
            fieldbackground=C["card"], rowheight=24,
            font=("Consolas", 9))
        s.configure("Treeview.Heading",
            background=C["accent2"], foreground=C["text"],
            font=("Consolas", 9, "bold"))
        s.map("Treeview", background=[("selected", C["accent2"])])
        s.configure("TNotebook",        background=C["bg"],    borderwidth=0)
        s.configure("TNotebook.Tab",
            background=C["card"],    foreground=C["dim"],
            padding=[12, 5],         font=("Consolas", 9))
        s.map("TNotebook.Tab",
            background=[("selected", C["accent2"])],
            foreground=[("selected", C["text"])])

    # ══════════════════════════════════════════
    # ساخت UI
    # ══════════════════════════════════════════

    def _build(self):
        # هدر
        hdr = tk.Frame(self, bg=C["accent2"], pady=6)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="🗺  مسئله فروشنده دوره‌گرد  (TSP Solver)",
                 font=("Consolas", 15, "bold"),
                 bg=C["accent2"], fg=C["text"]).pack(side=tk.LEFT, padx=16)
        tk.Label(hdr, text="7 الگوریتم هوش مصنوعی  |  رابط تعاملی  |  انیمیشن",
                 font=("Consolas", 9), bg=C["accent2"], fg=C["dim"]).pack(side=tk.RIGHT, padx=16)

        # body
        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        # ─── ستون چپ ───
        lf = tk.Frame(body, bg=C["panel"], width=270)
        lf.pack(side=tk.LEFT, fill=tk.Y, padx=(0,6))
        lf.pack_propagate(False)
        self._left_panel(lf)

        # ─── مرکز (bوم + نمودار) ───
        mid = tk.Frame(body, bg=C["bg"])
        mid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._center_panel(mid)

        # ─── ستون راست ───
        rf = tk.Frame(body, bg=C["panel"], width=290)
        rf.pack(side=tk.RIGHT, fill=tk.Y, padx=(6,0))
        rf.pack_propagate(False)
        self._right_panel(rf)

    # ─────────────────────────────────────────
    # پنل چپ
    # ─────────────────────────────────────────

    def _left_panel(self, p):
        def sec(t):
            f = tk.Frame(p, bg=C["border"], height=1)
            f.pack(fill=tk.X, padx=10, pady=(10,0))
            tk.Label(p, text=t, font=("Consolas", 9, "bold"),
                     bg=C["panel"], fg=C["accent"]).pack(anchor="w", padx=12, pady=(4,2))

        # ── شهرها ──
        sec("⚙  تنظیمات شهر")
        rf = tk.Frame(p, bg=C["panel"])
        rf.pack(fill=tk.X, padx=12, pady=2)
        tk.Label(rf, text="تعداد:", bg=C["panel"], fg=C["text"],
                 font=("Consolas",9)).pack(side=tk.LEFT)
        self.n_var = tk.IntVar(value=10)
        tk.Spinbox(rf, from_=4, to=20, textvariable=self.n_var,
                   width=5, bg=C["card"], fg=C["text"],
                   buttonbackground=C["border"],
                   font=("Consolas",9), relief="flat").pack(side=tk.LEFT, padx=6)

        self._btn(p, "🎲  شهرهای تصادفی", self._do_random)
        self._btn(p, "🏙  شهرهای ایران",   self._do_iran,  col=C["blue"])
        self._btn(p, "🗑  پاک کردن",       self._do_clear, col="#444")

        # ── ورودی دستی ──
        sec("📥  ورودی دستی  (A B 10)")
        self.inp = scrolledtext.ScrolledText(p, height=5, width=28,
            bg=C["card"], fg=C["text"], font=("Consolas",9),
            insertbackground="white", relief="flat")
        self.inp.pack(padx=12, pady=4)
        self._btn(p, "📤  بارگذاری", self._do_load_manual)

        # ── الگوریتم ──
        sec("🤖  انتخاب الگوریتم")
        self.algo_var = tk.StringVar(value="Simulated Annealing")
        for name, meta in ALGO_META.items():
            tk.Radiobutton(p, text=f"{meta['sym']} {name}",
                           variable=self.algo_var, value=name,
                           bg=C["panel"], fg=meta["color"],
                           selectcolor=C["card"], activebackground=C["panel"],
                           activeforeground=meta["color"],
                           font=("Consolas",9)).pack(anchor="w", padx=18)

        # ── دکمه‌های اجرا ──
        sec("▶  اجرا")
        self._btn(p, "🚀  حل کن!",           self._do_solve,    col=C["accent"])
        self._btn(p, "🔁  همه الگوریتم‌ها",  self._do_solve_all, col=C["blue"])

        # ── نتیجه ──
        sec("📊  نتیجه")
        self.result_lbl = tk.Label(p, text="—", bg=C["panel"], fg=C["green"],
                                   font=("Consolas",8), justify="left",
                                   wraplength=240, anchor="w")
        self.result_lbl.pack(anchor="w", padx=12, pady=4)

    # ─────────────────────────────────────────
    # پنل مرکزی
    # ─────────────────────────────────────────

    def _center_panel(self, p):
        nb = ttk.Notebook(p)
        nb.pack(fill=tk.BOTH, expand=True)

        # تب نقشه
        map_tab = tk.Frame(nb, bg=C["bg"])
        nb.add(map_tab, text="  🗺  نقشه  ")
        self._build_map_tab(map_tab)

        # تب نمودار
        chart_tab = tk.Frame(nb, bg=C["bg"])
        nb.add(chart_tab, text="  📈  همگرایی  ")
        self._build_chart_tab(chart_tab)

        self.notebook = nb

    def _build_map_tab(self, p):
        # بوم
        cf = tk.Frame(p, bg=C["border"], bd=1)
        cf.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.canvas = tk.Canvas(cf, bg=C["bg"], highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>",       self._map_click)
        self.canvas.bind("<B1-Motion>",      self._map_drag)
        self.canvas.bind("<ButtonRelease-1>",self._map_release)
        self.canvas.bind("<Motion>",         self._map_hover)
        self.canvas.bind("<Configure>",      lambda e: self._redraw_map())

        # نوار پایین
        bar = tk.Frame(p, bg=C["panel"], pady=4)
        bar.pack(fill=tk.X)
        self._btn(bar, "▶ انیمیشن", self._anim_start, col=C["green"],  s=tk.LEFT, px=6)
        self._btn(bar, "⏹ توقف",    self._anim_stop,  col=C["accent"], s=tk.LEFT, px=4)
        tk.Label(bar, text="سرعت:", bg=C["panel"], fg=C["dim"],
                 font=("Consolas",8)).pack(side=tk.LEFT, padx=(12,0))
        self.speed_var = tk.IntVar(value=300)
        tk.Scale(bar, variable=self.speed_var, from_=50, to=1000,
                 orient=tk.HORIZONTAL, length=130, showvalue=False,
                 bg=C["panel"], fg=C["text"], troughcolor=C["card"],
                 highlightthickness=0).pack(side=tk.LEFT)
        self.status_lbl = tk.Label(bar, text="آماده", bg=C["panel"],
                                   fg=C["dim"], font=("Consolas",8))
        self.status_lbl.pack(side=tk.RIGHT, padx=10)

    def _build_chart_tab(self, p):
        tk.Label(p, text="نمودار همگرایی هزینه در طول اجرا",
                 bg=C["bg"], fg=C["dim"], font=("Consolas",9)).pack(pady=4)
        cf = tk.Frame(p, bg=C["border"], bd=1)
        cf.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.chart_canvas = tk.Canvas(cf, bg=C["bg"], highlightthickness=0)
        self.chart_canvas.pack(fill=tk.BOTH, expand=True)
        self.chart_canvas.bind("<Configure>", lambda e: self._redraw_chart())

    # ─────────────────────────────────────────
    # پنل راست
    # ─────────────────────────────────────────

    def _right_panel(self, p):
        tk.Label(p, text="📋  مقایسه الگوریتم‌ها",
                 font=("Consolas",10,"bold"),
                 bg=C["panel"], fg=C["accent"]).pack(anchor="w", padx=12, pady=(12,4))

        # جدول
        cols = ("الگوریتم","هزینه","زمان (s)","تکرار")
        self.tree = ttk.Treeview(p, columns=cols, show="headings", height=8)
        widths = [130, 70, 70, 60]
        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(padx=8, pady=4, fill=tk.X)
        self.tree.bind("<<TreeviewSelect>>", self._tree_select)

        # دکمه‌های خروجی
        bf = tk.Frame(p, bg=C["panel"])
        bf.pack(fill=tk.X, padx=8)
        self._btn(bf, "💾  ذخیره نتایج", self._save_results, col=C["accent2"], s=tk.LEFT, px=4)
        self._btn(bf, "🔄  پاک جدول",    self._clear_table,  col="#444",        s=tk.LEFT, px=4)

        # لاگ
        tk.Label(p, text="📄  لاگ اجرا",
                 font=("Consolas",10,"bold"),
                 bg=C["panel"], fg=C["accent"]).pack(anchor="w", padx=12, pady=(10,2))
        self.log = scrolledtext.ScrolledText(p, height=18, width=33,
            bg=C["card"], fg=C["green"], font=("Consolas",8),
            state="disabled", insertbackground="white", relief="flat")
        self.log.pack(padx=8, fill=tk.BOTH, expand=True, pady=(0,8))

    # ─────────────────────────────────────────
    # ویجت کمکی
    # ─────────────────────────────────────────

    def _btn(self, parent, text, cmd, col=None, s=tk.TOP, px=10):
        b = tk.Button(parent, text=text, command=cmd,
                      bg=col or C["accent2"], fg=C["text"],
                      font=("Consolas",9,"bold"), relief="flat",
                      padx=8, pady=4, cursor="hand2",
                      activebackground=C["accent"],
                      activeforeground="white")
        kw = {"padx": px, "pady": 2}
        if s == tk.TOP:
            b.pack(fill=tk.X, **kw)
        else:
            b.pack(side=s, **kw)
        return b

    # ══════════════════════════════════════════
    # مختصات
    # ══════════════════════════════════════════

    def _cw(self):  return max(self.canvas.winfo_width(),  400)
    def _ch(self):  return max(self.canvas.winfo_height(), 350)

    def _to_px(self, gx, gy):
        """مختصات گراف (0-100) → پیکسل"""
        W, H = self._cw(), self._ch()
        # بهینه محدوده مختصات برای شهرهای ایران
        xs = [v[0] for v in self.graph.coordinates.values()]
        ys = [v[1] for v in self.graph.coordinates.values()]
        if not xs:
            return MARGIN + gx/100*(W-2*MARGIN), MARGIN + gy/100*(H-2*MARGIN)
        xmin,xmax = min(xs),max(xs)
        ymin,ymax = min(ys),max(ys)
        rx = xmax-xmin or 1; ry = ymax-ymin or 1
        px = MARGIN + (gx-xmin)/rx*(W-2*MARGIN)
        py = MARGIN + (gy-ymin)/ry*(H-2*MARGIN)
        return px, py

    def _to_graph(self, px, py):
        W, H = self._cw(), self._ch()
        gx = (px - MARGIN) / (W-2*MARGIN) * 100
        gy = (py - MARGIN) / (H-2*MARGIN) * 100
        return gx, gy

    def _city_at(self, px, py, r=14):
        for c, (gx, gy) in self.graph.coordinates.items():
            cx, cy = self._to_px(gx, gy)
            if math.hypot(px-cx, py-cy) < r:
                return c
        return None

    # ══════════════════════════════════════════
    # رویدادهای بوم
    # ══════════════════════════════════════════

    def _map_click(self, e):
        city = self._city_at(e.x, e.y)
        if city:
            self.drag_city = city
        else:
            # شهر جدید اضافه کن
            gx, gy = self._to_graph(e.x, e.y)
            gx = max(2, min(98, gx)); gy = max(2, min(98, gy))
            n = len(self.graph.cities)
            name = chr(65+n) if n < 26 else f"C{n}"
            self.graph.add_city(name, gx, gy)
            self.graph.ensure_complete()
            self._redraw_map()
            self._log(f"+ شهر {name} اضافه شد")

    def _map_drag(self, e):
        if self.drag_city and self.drag_city in self.graph.coordinates:
            gx, gy = self._to_graph(e.x, e.y)
            self.graph.coordinates[self.drag_city] = (
                max(2, min(98, gx)), max(2, min(98, gy)))
            self._redraw_map()

    def _map_release(self, e):
        self.drag_city = None

    def _map_hover(self, e):
        c = self._city_at(e.x, e.y)
        if c != self.hover_city:
            self.hover_city = c
            self._redraw_map()

    # ══════════════════════════════════════════
    # ترسیم نقشه
    # ══════════════════════════════════════════

    def _redraw_map(self, tour=None, step=-1):
        cv = self.canvas
        cv.delete("all")
        W, H = self._cw(), self._ch()
        if not self.graph.cities:
            cv.create_text(W//2, H//2, text="روی بوم کلیک کنید تا شهر اضافه شود",
                           fill=C["dim"], font=("Consolas",11))
            return

        tour = tour or (self.active_result.best_tour if self.active_result else [])

        # شبکه پس‌زمینه
        for gx in range(0, W, 60):
            cv.create_line(gx, 0, gx, H, fill=C["grid"], width=1)
        for gy in range(0, H, 60):
            cv.create_line(0, gy, W, gy, fill=C["grid"], width=1)

        # یال‌های پس‌زمینه
        cities = self.graph.cities
        for i, c1 in enumerate(cities):
            if c1 not in self.graph.coordinates: continue
            for c2 in cities[i+1:]:
                if c2 not in self.graph.coordinates: continue
                p1 = self._to_px(*self.graph.coordinates[c1])
                p2 = self._to_px(*self.graph.coordinates[c2])
                cv.create_line(*p1, *p2, fill=C["edge_bg"], width=1, dash=(2,8))

        # مسیر انتخاب‌شده
        n = len(tour)
        if tour:
            limit = n if step < 0 else min(step, n)
            for i in range(limit):
                c1, c2 = tour[i], tour[(i+1) % n]
                if c1 not in self.graph.coordinates or c2 not in self.graph.coordinates:
                    continue
                p1 = self._to_px(*self.graph.coordinates[c1])
                p2 = self._to_px(*self.graph.coordinates[c2])
                # سایه درخشان
                cv.create_line(*p1, *p2, fill="#6b0020", width=6)
                # رنگ گرادیانت
                t = i / n
                r_ = int(233*(1-t) + 64*t)
                g_ = int(69*(1-t) + 196*t)
                b_ = int(96*(1-t) + 255*t)
                col = f"#{max(0,min(255,r_)):02x}{max(0,min(255,g_)):02x}{max(0,min(255,b_)):02x}"
                cv.create_line(*p1, *p2, fill=col, width=2,
                               arrow=tk.LAST, arrowshape=(12,14,5))

        # شهرها
        for city in cities:
            if city not in self.graph.coordinates: continue
            gx, gy = self.graph.coordinates[city]
            cx, cy = self._to_px(gx, gy)
            r = 11
            is_start = bool(tour and tour[0] == city)
            is_hover = city == self.hover_city
            in_path  = city in tour

            fill = C["start"] if is_start else (C["city"] if in_path else C["dim"])
            size = r+3 if is_hover else r

            if is_start:
                for halo in (r+14, r+8):
                    cv.create_oval(cx-halo,cy-halo,cx+halo,cy+halo,
                                   outline=C["start"], fill="", width=1)
            cv.create_oval(cx-size,cy-size,cx+size,cy+size,
                           fill=fill, outline="white" if is_hover else C["bg"], width=1.5)
            cv.create_text(cx, cy-size-9, text=city, fill=C["text"],
                           font=("Consolas",9,"bold"))

        # هزینه روی بوم
        if tour and step < 0:
            cost = self.graph.tour_cost(tour)
            algo = self.active_result.algorithm if self.active_result else ""
            cv.create_text(W-8, 8, anchor="ne",
                           text=f"{algo}\n💰 {cost:.2f}",
                           fill=C["accent"], font=("Consolas",10,"bold"), justify="right")

    # ══════════════════════════════════════════
    # نمودار همگرایی (Canvas داخلی)
    # ══════════════════════════════════════════

    def _redraw_chart(self):
        cv = self.chart_canvas
        cv.delete("all")
        W = max(cv.winfo_width(),  400)
        H = max(cv.winfo_height(), 300)
        ML, MR, MT, MB = 70, 20, 20, 50

        if not self.results:
            cv.create_text(W//2, H//2, text="ابتدا الگوریتم‌ها را اجرا کنید",
                           fill=C["dim"], font=("Consolas",11))
            return

        # جمع‌آوری داده
        series = {}
        for name, r in self.results.items():
            if r.cost_history:
                series[name] = r.cost_history

        if not series:
            return

        all_vals = [v for s in series.values() for v in s]
        y_min = min(all_vals) * 0.97
        y_max = max(all_vals) * 1.03
        y_rng = y_max - y_min or 1
        x_max_pts = max(len(s) for s in series.values())

        def to_px(xi, yi, x_len):
            px = ML + xi/(x_len-1 or 1) * (W-ML-MR)
            py = MT + (1-(yi-y_min)/y_rng) * (H-MT-MB)
            return px, py

        # محورها
        cv.create_line(ML, MT, ML, H-MB, fill=C["border"], width=1)
        cv.create_line(ML, H-MB, W-MR, H-MB, fill=C["border"], width=1)

        # شبکه افقی
        for i in range(5):
            y_val = y_min + i/4 * y_rng
            _, py = to_px(0, y_val, 2)
            cv.create_line(ML, py, W-MR, py, fill=C["grid"], width=1, dash=(4,6))
            cv.create_text(ML-4, py, text=f"{y_val:.0f}",
                           fill=C["dim"], font=("Consolas",8), anchor="e")

        # برچسب محورها
        cv.create_text(ML//2, (MT+H-MB)//2, text="هزینه", fill=C["dim"],
                       font=("Consolas",9), angle=90)
        cv.create_text((ML+W-MR)//2, H-MB//3, text="تکرار",
                       fill=C["dim"], font=("Consolas",9))

        # خطوط
        for name, vals in series.items():
            meta = ALGO_META.get(name, {"color": "#ffffff"})
            col = meta["color"]
            pts = [to_px(i, v, len(vals)) for i, v in enumerate(vals)]
            if len(pts) >= 2:
                flat = [c for p in pts for c in p]
                cv.create_line(*flat, fill=col, width=2, smooth=True)
            # نقطه آخر + برچسب
            if pts:
                lx, ly = pts[-1]
                cv.create_oval(lx-4,ly-4,lx+4,ly+4, fill=col, outline="")
                cv.create_text(lx+4, ly, text=f"{vals[-1]:.1f}",
                               fill=col, font=("Consolas",7), anchor="w")

        # راهنما
        lx = ML + 10
        for i, (name, meta) in enumerate(ALGO_META.items()):
            if name in series:
                ly = MT + 14 + i * 16
                cv.create_line(lx, ly, lx+18, ly, fill=meta["color"], width=2)
                cv.create_text(lx+22, ly, text=f"{meta['sym']} {name}",
                               fill=meta["color"], font=("Consolas",8), anchor="w")

    # ══════════════════════════════════════════
    # انیمیشن
    # ══════════════════════════════════════════

    def _anim_start(self):
        if not self.active_result or not self.active_result.best_tour:
            messagebox.showinfo("", "ابتدا یک الگوریتم را اجرا کنید!")
            return
        self.anim_running = True
        self.anim_idx = 0
        self.status_lbl.config(text="▶ انیمیشن...")
        self._anim_tick()

    def _anim_stop(self):
        self.anim_running = False
        self._redraw_map()
        self.status_lbl.config(text="⏹ متوقف")

    def _anim_tick(self):
        if not self.anim_running: return
        tour = self.active_result.best_tour
        if self.anim_idx <= len(tour):
            self._redraw_map(tour, self.anim_idx)
            self.anim_idx += 1
            self.after(self.speed_var.get(), self._anim_tick)
        else:
            self.anim_running = False
            self._redraw_map(tour)
            self.status_lbl.config(text="✓ انیمیشن تمام شد")

    # ══════════════════════════════════════════
    # داده
    # ══════════════════════════════════════════

    def _load_sample_data(self):
        sample = "A B 10\nA C 15\nA D 35\nB C 20\nB D 25\nC D 30"
        self.inp.delete("1.0", tk.END)
        self.inp.insert("1.0", sample)
        self._do_load_manual(quiet=True)

    def _do_load_manual(self, quiet=False):
        txt = self.inp.get("1.0", tk.END)
        self.graph = TSPGraph()
        self.graph.load_from_text(txt)
        # مختصات دایره‌ای برای شهرهای بدون مختصات
        n = len(self.graph.cities)
        for i, c in enumerate(self.graph.cities):
            if c not in self.graph.coordinates:
                ang = 2*math.pi*i/n
                self.graph.coordinates[c] = (50+38*math.cos(ang), 50+38*math.sin(ang))
        self.graph.ensure_complete()
        self._reset_results()
        self._redraw_map()
        if not quiet:
            self._log(f"✅ بارگذاری شد: {len(self.graph.cities)} شهر")

    def _do_random(self):
        n = self.n_var.get()
        self.graph = TSPGraph()
        self.graph.generate_random(n, seed=random.randint(0,99999))
        self._reset_results()
        self._redraw_map()
        self._log(f"🎲 {n} شهر تصادفی تولید شد")

    def _do_iran(self):
        self.graph = TSPGraph.iran_cities()
        self._reset_results()
        self._redraw_map()
        self._log("🏙 شهرهای واقعی ایران بارگذاری شد (۱۰ شهر)")

    def _do_clear(self):
        self.graph = TSPGraph()
        self._reset_results()
        self.canvas.delete("all")
        self._log("🗑 پاک شد")

    def _reset_results(self):
        self.results = {}
        self.active_result = None
        self._clear_table()
        self.result_lbl.config(text="—")

    # ══════════════════════════════════════════
    # حل
    # ══════════════════════════════════════════

    def _do_solve(self):
        if not self.graph.cities:
            messagebox.showwarning("خطا", "ابتدا شهرها را اضافه کنید!")
            return
        self._run(self.algo_var.get())

    def _do_solve_all(self):
        if not self.graph.cities:
            messagebox.showwarning("خطا", "ابتدا شهرها را اضافه کنید!")
            return
        queue = list(ALGO_META.keys())
        if len(self.graph.cities) > 12 and "Brute Force" in queue:
            queue.remove("Brute Force")
        for a in queue:
            self._run(a, update=False)
        if self.results:
            best = min(self.results, key=lambda k: self.results[k].best_cost)
            self.active_result = self.results[best]
            self._redraw_map()
            self._redraw_chart()
            self.notebook.select(1)   # برو تب نمودار

    FN_MAP = {
        "Brute Force":         brute_force,
        "Greedy Search":       greedy_search,
        "A* Search":           a_star,
        "Local Beam Search":   local_beam_search,
        "Hill Climbing":       hill_climbing,
        "Simulated Annealing": simulated_annealing,
        "Genetic Algorithm":   genetic_algorithm,
    }

    def _run(self, algo: str, update: bool = True):
        fn = self.FN_MAP.get(algo)
        if not fn: return
        self.status_lbl.config(text=f"⏳ {algo}...")
        self.update_idletasks()

        try:
            result = fn(self.graph)
        except Exception as ex:
            messagebox.showerror("خطا", str(ex))
            return

        self.results[algo] = result
        if update:
            self.active_result = result
            self._redraw_map()
            self._redraw_chart()

        # اطلاعات نتیجه
        self.result_lbl.config(
            text=f"الگوریتم : {algo}\n"
                 f"هزینه    : {result.best_cost:.4f}\n"
                 f"زمان     : {result.elapsed:.6f}s\n"
                 f"تکرار    : {result.iterations:,}\n"
                 f"مسیر:\n{result.tour_str}")
        self.status_lbl.config(text=f"✓ {algo} | {result.best_cost:.2f}")

        meta = ALGO_META.get(algo, {"sym":"•"})
        self._log(
            f"{meta['sym']} {algo}\n"
            f"  هزینه : {result.best_cost:.4f}\n"
            f"  زمان  : {result.elapsed:.6f}s\n"
            f"  مسیر  : {result.tour_str}\n"
        )
        self._update_table()

    # ══════════════════════════════════════════
    # جدول مقایسه
    # ══════════════════════════════════════════

    def _update_table(self):
        self._clear_table()
        sorted_r = sorted(self.results.items(), key=lambda x: x[1].best_cost)
        for i, (name, r) in enumerate(sorted_r):
            tag = "best" if i == 0 else "alt"
            self.tree.insert("", "end",
                values=(name, f"{r.best_cost:.2f}", f"{r.elapsed:.4f}", f"{r.iterations:,}"),
                tags=(tag,))
        self.tree.tag_configure("best", background=C["accent2"], foreground=C["green"])

    def _clear_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

    def _tree_select(self, _):
        sel = self.tree.selection()
        if sel:
            name = self.tree.item(sel[0])["values"][0]
            if name in self.results:
                self.active_result = self.results[name]
                self._redraw_map()

    # ══════════════════════════════════════════
    # ذخیره
    # ══════════════════════════════════════════

    def _save_results(self):
        if not self.results:
            messagebox.showinfo("", "هنوز نتیجه‌ای وجود ندارد!")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("All", "*.*")],
            initialfile="tsp_results.txt")
        if not path: return

        lines = ["TSP Results — فروشنده دوره‌گرد", "="*52, ""]
        lines.append(f"شهرها: {', '.join(self.graph.cities)}")
        lines.append(f"تعداد: {len(self.graph.cities)}\n")
        for name, r in sorted(self.results.items(), key=lambda x: x[1].best_cost):
            lines += [
                f"[{name}]",
                f"  مسیر  : {r.tour_str}",
                f"  هزینه : {r.best_cost:.4f}",
                f"  زمان  : {r.elapsed:.6f}s",
                f"  تکرار : {r.iterations:,}",
                ""
            ]
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        self._log(f"💾 ذخیره شد: {path}")
        messagebox.showinfo("✓", f"نتایج در {path} ذخیره شد")

    # ══════════════════════════════════════════
    # لاگ
    # ══════════════════════════════════════════

    def _log(self, msg: str):
        self.log.config(state="normal")
        ts = time.strftime("%H:%M:%S")
        self.log.insert(tk.END, f"[{ts}] {msg}\n")
        self.log.see(tk.END)
        self.log.config(state="disabled")


# ══════════════════════════════════════════════
# اجرا
# ══════════════════════════════════════════════

if __name__ == "__main__":
    app = TSPApp()
    app.mainloop()