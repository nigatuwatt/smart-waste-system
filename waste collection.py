"""
SMART WASTE COLLECTION SYSTEM — DEBRE BIRHAN
AI course project: Hill Climbing Search Algorithm

Requirements: Python 3.10+ (Tkinter is included with most Windows Python installs)
Run: python smart_waste_collection.py

This is an academic simulation. Locations, distances, bin levels and truck data are
sample data, not live municipal/GPS information.
"""

import csv
import json
import math
import random
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime

APP_TITLE = "Debre Birhan • Smart Waste Collection"
DATA_FILE = Path(__file__).with_name("waste_collection_data.json")

BG = "#0b1220"
PANEL = "#111c2e"
PANEL_2 = "#17253a"
BORDER = "#27364d"
TEXT = "#e8eef7"
MUTED = "#93a4bb"
GREEN = "#39d98a"
CYAN = "#4cc9f0"
ORANGE = "#ffb454"
RED = "#ff647c"
PURPLE = "#b6a1ff"

DEFAULT_POINTS = [
    {"name": "City Depot", "x": 0.50, "y": 0.82, "waste": 0, "priority": "Depot", "status": "Base"},
    {"name": "Kebele 04", "x": 0.28, "y": 0.62, "waste": 78, "priority": "High", "status": "Pending"},
    {"name": "Market Area", "x": 0.48, "y": 0.43, "waste": 92, "priority": "High", "status": "Pending"},
    {"name": "Hospital Zone", "x": 0.72, "y": 0.35, "waste": 65, "priority": "High", "status": "Pending"},
    {"name": "Residential North", "x": 0.66, "y": 0.16, "waste": 47, "priority": "Medium", "status": "Pending"},
    {"name": "School District", "x": 0.30, "y": 0.25, "waste": 58, "priority": "Medium", "status": "Pending"},
    {"name": "Bus Station", "x": 0.16, "y": 0.43, "waste": 84, "priority": "High", "status": "Pending"},
    {"name": "Residential South", "x": 0.77, "y": 0.66, "waste": 33, "priority": "Low", "status": "Pending"},
    {"name": "Industrial Area", "x": 0.88, "y": 0.48, "waste": 71, "priority": "Medium", "status": "Pending"},
    {"name": "Kebele 06", "x": 0.40, "y": 0.70, "waste": 54, "priority": "Medium", "status": "Pending"},
]
DEFAULT_TRUCKS = [
    {"name": "Truck A-01", "capacity": 1200, "fuel": 0.8},
    {"name": "Truck B-02", "capacity": 900, "fuel": 0.6},
    {"name": "Truck C-03", "capacity": 1500, "fuel": 1.0},
]


def distance(a, b):
    """Simulated road distance in km from normalized map coordinates."""
    # Multiply by 12 to give illustrative city-scale distances.
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"]) * 12


def route_distance(route, points, return_to_depot=True):
    total = sum(distance(points[route[i]], points[route[i + 1]])
                for i in range(len(route) - 1))
    if return_to_depot and len(route) > 1:
        total += distance(points[route[-1]], points[route[0]])
    return total


def hill_climbing(points, start_index=0, max_iterations=250, seed=None):
    """
    Steepest-improvement hill climbing over route neighbors.
    A neighbor is produced by swapping two collection stops.
    The depot remains at route position 0.
    Stops are treated as one collection tour; this is not a globally optimal solver.
    """
    if len(points) <= 2:
        return list(range(len(points))), list(range(len(points))), []

    rng = random.Random(seed)
    route = list(range(len(points)))
    route[0], route[start_index] = route[start_index], route[0]
    # Keep the depot first, then start from a shuffled candidate tour.
    depot = 0
    stops = [i for i in range(len(points)) if i != depot]
    rng.shuffle(stops)
    current = [depot] + stops

    def cost(r):
        return route_distance(r, points, True)

    initial = current[:]
    history = [cost(current)]
    for _ in range(max_iterations):
        current_cost = cost(current)
        best_route = current
        best_cost = current_cost
        # Explore all pairwise swaps for the current route.
        for i in range(1, len(current) - 1):
            for j in range(i + 1, len(current)):
                candidate = current[:]
                candidate[i], candidate[j] = candidate[j], candidate[i]
                candidate_cost = cost(candidate)
                if candidate_cost < best_cost - 1e-9:
                    best_route, best_cost = candidate, candidate_cost
        if best_route is current:
            break
        current = best_route
        history.append(best_cost)
    return initial, current, history


class WasteApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1280x820")
        self.root.minsize(1000, 680)
        self.points = self.load_data()
        self.trucks = DEFAULT_TRUCKS[:]
        self.route = []
        self.initial_route = []
        self.history = []
        self.iterations = 0
        self.collection_log = []
        self.selected_point = None

        self.setup_style()
        self.build_ui()
        self.refresh_all()
        self.log("System ready. Sample Debre Birhan data loaded.")

    def setup_style(self):
        self.root.configure(bg=BG)
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                        foreground=TEXT, rowheight=28, borderwidth=0)
        style.configure("Treeview.Heading", background=PANEL_2,
                        foreground=TEXT, font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#244e61")],
                  foreground=[("selected", "white")])
        style.configure("TCombobox", fieldbackground=PANEL_2, background=PANEL_2,
                        foreground=TEXT, arrowcolor=TEXT)
        style.configure("TProgressbar", troughcolor=PANEL_2, background=GREEN,
                        bordercolor=PANEL_2, lightcolor=GREEN, darkcolor=GREEN)

    def load_data(self):
        if DATA_FILE.exists():
            try:
                data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
                if isinstance(data, list) and data:
                    return data
            except (OSError, json.JSONDecodeError):
                pass
        return [p.copy() for p in DEFAULT_POINTS]

    def save_data(self):
        try:
            DATA_FILE.write_text(json.dumps(self.points, indent=2), encoding="utf-8")
            self.log(f"Saved collection points to {DATA_FILE.name}.")
        except OSError as exc:
            messagebox.showerror("Save failed", str(exc))

    def build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=22, pady=(18, 12))
        brand = tk.Frame(header, bg=BG)
        brand.pack(side="left")
        tk.Label(brand, text="♻", font=("Segoe UI Symbol", 29), bg=BG,
                 fg=GREEN).pack(side="left", padx=(0, 12))
        titlebox = tk.Frame(brand, bg=BG)
        titlebox.pack(side="left")
        tk.Label(titlebox, text="SMART WASTE COLLECTION", font=("Segoe UI", 18, "bold"),
                 bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(titlebox, text="DEBRE BIRHAN CITY  /  AI ROUTE OPTIMIZATION",
                 font=("Segoe UI", 9, "bold"), bg=BG, fg=MUTED).pack(anchor="w", pady=(3, 0))
        self.status_label = tk.Label(header, text="● SYSTEM ONLINE", font=("Segoe UI", 9, "bold"),
                                     bg=BG, fg=GREEN)
        self.status_label.pack(side="right", padx=6)

        # KPI cards
        kpis = tk.Frame(self.root, bg=BG)
        kpis.pack(fill="x", padx=22, pady=(0, 14))
        self.kpi_values = {}
        for key, label, color in [
            ("points", "COLLECTION POINTS", CYAN),
            ("waste", "AVG. WASTE LEVEL", ORANGE),
            ("distance", "OPTIMIZED DISTANCE", GREEN),
            ("improvement", "ROUTE IMPROVEMENT", PURPLE),
        ]:
            card = tk.Frame(kpis, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
            card.pack(side="left", fill="x", expand=True, padx=(0, 10))
            tk.Label(card, text=label, bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
            val = tk.Label(card, text="—", bg=PANEL, fg=color,
                           font=("Segoe UI", 21, "bold"))
            val.pack(anchor="w", padx=14, pady=(0, 12))
            self.kpi_values[key] = val

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=22, pady=(0, 14))
        left = tk.Frame(body, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))
        right = tk.Frame(body, bg=BG, width=370)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        # Map canvas
        maphead = tk.Frame(left, bg=PANEL)
        maphead.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(maphead, text="CITY COLLECTION MAP", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 11, "bold")).pack(side="left")
        tk.Label(maphead, text="SIMULATED ROAD DISTANCES", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 8)).pack(side="right")
        self.map_canvas = tk.Canvas(left, bg="#0e1a2a", highlightthickness=0, height=360)
        self.map_canvas.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self.map_canvas.bind("<Configure>", lambda _e: self.draw_map())

        legend = tk.Frame(left, bg=PANEL)
        legend.pack(fill="x", padx=16, pady=(0, 12))
        for color, text in [(GREEN, "Depot"), (RED, "High priority"), (ORANGE, "Medium"), (CYAN, "Low / other")]:
            tk.Label(legend, text="●", fg=color, bg=PANEL, font=("Segoe UI", 10)).pack(side="left")
            tk.Label(legend, text=text, fg=MUTED, bg=PANEL, font=("Segoe UI", 8)).pack(side="left", padx=(3, 13))

        # Right panel controls
        control = tk.Frame(right, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        control.pack(fill="x", pady=(0, 12))
        tk.Label(control, text="AI ROUTE PLANNER", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=15, pady=(14, 3))
        tk.Label(control, text="Hill Climbing Search", bg=PANEL, fg=GREEN,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=15, pady=(0, 12))
        self.truck_var = tk.StringVar(value=self.trucks[0]["name"])
        tk.Label(control, text="ASSIGNED TRUCK", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=15)
        ttk.Combobox(control, textvariable=self.truck_var, values=[t["name"] for t in self.trucks],
                     state="readonly").pack(fill="x", padx=15, pady=(4, 12))
        self.iter_var = tk.IntVar(value=250)
        tk.Label(control, text="SEARCH LIMIT (iterations)", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=15)
        iterrow = tk.Frame(control, bg=PANEL)
        iterrow.pack(fill="x", padx=15, pady=(4, 10))
        tk.Scale(iterrow, from_=25, to=1000, resolution=25, orient="horizontal",
                 variable=self.iter_var, bg=PANEL, fg=TEXT, troughcolor=PANEL_2,
                 highlightthickness=0, activebackground=GREEN, bd=0).pack(fill="x")
        self.optimize_btn = tk.Button(control, text="✦  OPTIMIZE COLLECTION ROUTE",
                                      command=self.optimize, bg=GREEN, fg="#082116",
                                      activebackground="#66e6a5", activeforeground="#082116",
                                      font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                                      pady=11)
        self.optimize_btn.pack(fill="x", padx=15, pady=(3, 8))
        row = tk.Frame(control, bg=PANEL)
        row.pack(fill="x", padx=15, pady=(0, 14))
        self.make_button(row, "Mark Collected", self.mark_collected, CYAN, "#06202a").pack(
            side="left", fill="x", expand=True, padx=(0, 5))
        self.make_button(row, "Reset Route", self.reset_route, PANEL_2, TEXT).pack(
            side="left", fill="x", expand=True, padx=(5, 0))

        # Collection points table
        points_panel = tk.Frame(right, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        points_panel.pack(fill="both", expand=True, pady=(0, 12))
        tk.Label(points_panel, text="COLLECTION POINTS", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=(12, 8))
        columns = ("name", "waste", "priority")
        self.tree = ttk.Treeview(points_panel, columns=columns, show="headings", height=7)
        self.tree.heading("name", text="LOCATION")
        self.tree.heading("waste", text="WASTE %")
        self.tree.heading("priority", text="PRIORITY")
        self.tree.column("name", width=145, anchor="w")
        self.tree.column("waste", width=65, anchor="center")
        self.tree.column("priority", width=78, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        actionrow = tk.Frame(points_panel, bg=PANEL)
        actionrow.pack(fill="x", padx=10, pady=(0, 10))
        self.make_button(actionrow, "+ Add", self.add_point_dialog, PANEL_2, TEXT).pack(
            side="left", fill="x", expand=True, padx=(0, 4))
        self.make_button(actionrow, "Remove", self.remove_point, "#4b2432", "#ffb3c0").pack(
            side="left", fill="x", expand=True, padx=(4, 0))

        # Bottom log and actions
        footer = tk.Frame(self.root, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        footer.pack(fill="x", padx=22, pady=(0, 18))
        foothead = tk.Frame(footer, bg=PANEL)
        foothead.pack(fill="x", padx=14, pady=(9, 3))
        tk.Label(foothead, text="ACTIVITY LOG", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        self.make_button(foothead, "Export CSV Report", self.export_csv, PANEL_2, CYAN).pack(side="right")
        self.log_box = tk.Text(footer, height=4, bg="#0b1524", fg=MUTED, insertbackground=TEXT,
                               relief="flat", font=("Consolas", 9), wrap="word")
        self.log_box.pack(fill="x", padx=14, pady=(2, 12))
        self.log_box.configure(state="disabled")

    def make_button(self, parent, text, command, bg, fg):
        return tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                         activebackground=bg, activeforeground=fg, relief="flat",
                         cursor="hand2", font=("Segoe UI", 8, "bold"), padx=8, pady=7)

    def log(self, message):
        if not hasattr(self, "log_box"):
            return
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{stamp}]  {message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def refresh_all(self):
        self.refresh_table()
        self.update_kpis()
        self.draw_map()

    def refresh_table(self):
        if not hasattr(self, "tree"):
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, p in enumerate(self.points):
            if idx == 0:
                continue
            self.tree.insert("", "end", iid=str(idx), values=(p["name"], f'{p["waste"]}%', p["priority"]))

    def update_kpis(self):
        active = [p for p in self.points if p["status"] != "Base"]
        avg = sum(p["waste"] for p in active) / max(1, len(active))
        self.kpi_values["points"].configure(text=str(len(active)))
        self.kpi_values["waste"].configure(text=f"{avg:.0f}%")
        if self.route:
            before = route_distance(self.initial_route, self.points)
            after = route_distance(self.route, self.points)
            self.kpi_values["distance"].configure(text=f"{after:.1f} km")
            improvement = max(0, (before - after) / before * 100) if before else 0
            self.kpi_values["improvement"].configure(text=f"{improvement:.1f}%")
        else:
            self.kpi_values["distance"].configure(text="—")
            self.kpi_values["improvement"].configure(text="—")

    def draw_map(self):
        if not hasattr(self, "map_canvas"):
            return
        c = self.map_canvas
        c.delete("all")
        w = max(c.winfo_width(), 420)
        h = max(c.winfo_height(), 300)
        # Subtle grid
        for x in range(20, w, 35):
            c.create_line(x, 0, x, h, fill="#14263a")
        for y in range(15, h, 35):
            c.create_line(0, y, w, y, fill="#14263a")
        pad_x, pad_y = 45, 32

        def xy(p):
            return pad_x + p["x"] * (w - 2 * pad_x), pad_y + p["y"] * (h - 2 * pad_y)

        # Decorative road-like connectors, not real roads
        coords = [xy(p) for p in self.points]
        for i in range(len(coords) - 1):
            x1, y1 = coords[i]
            x2, y2 = coords[i + 1]
            c.create_line(x1, y1, x2, y2, fill="#1b3046", width=2, dash=(3, 5))
        # Draw optimized route
        if self.route and len(self.route) > 1:
            for i in range(len(self.route) - 1):
                a = xy(self.points[self.route[i]])
                b = xy(self.points[self.route[i + 1]])
                c.create_line(a[0], a[1], b[0], b[1], fill=GREEN, width=3, arrow=tk.LAST,
                              arrowshape=(9, 11, 4))
            a, b = xy(self.points[self.route[-1]]), xy(self.points[self.route[0]])
            c.create_line(a[0], a[1], b[0], b[1], fill=GREEN, width=2, dash=(5, 4), arrow=tk.LAST)
        for i, p in enumerate(self.points):
            x, y = xy(p)
            if i == 0:
                color, r = GREEN, 8
            elif p["status"] == "Collected":
                color, r = PURPLE, 6
            elif p["priority"] == "High":
                color, r = RED, 7
            elif p["priority"] == "Medium":
                color, r = ORANGE, 6
            else:
                color, r = CYAN, 6
            c.create_oval(x-r, y-r, x+r, y+r, fill=color, outline="#e8eef7", width=1)
            label = p["name"]
            c.create_text(x, y - 14, text=label, fill=TEXT, font=("Segoe UI", 8, "bold"))
        c.create_text(12, h - 12, text="Illustrative layout • not to scale", anchor="sw",
                      fill=MUTED, font=("Segoe UI", 8))

    def optimize(self):
        if len(self.points) < 3:
            messagebox.showinfo("Need more points", "Add at least two collection points plus the depot.")
            return
        self.optimize_btn.configure(state="disabled", text="OPTIMIZING...")
        self.root.update_idletasks()
        try:
            self.initial_route, self.route, self.history = hill_climbing(
                self.points, max_iterations=self.iter_var.get())
            self.iterations = max(0, len(self.history) - 1)
            before = route_distance(self.initial_route, self.points)
            after = route_distance(self.route, self.points)
            gain = (before - after) / before * 100 if before else 0
            self.update_kpis()
            self.draw_map()
            route_names = " → ".join(self.points[i]["name"] for i in self.route)
            self.log(f"Hill climbing completed: {self.iterations} improving steps; "
                     f"{before:.2f} km → {after:.2f} km ({gain:.1f}% improvement).")
            self.log("Route: " + route_names)
            messagebox.showinfo("Optimization complete",
                                f"Algorithm: Hill Climbing\n"
                                f"Initial distance: {before:.2f} km\n"
                                f"Optimized distance: {after:.2f} km\n"
                                f"Improvement: {gain:.1f}%\n"
                                f"Improving steps: {self.iterations}\n\n"
                                "Hill climbing finds a locally improved route; it does not guarantee the global optimum.")
        finally:
            self.optimize_btn.configure(state="normal", text="✦  OPTIMIZE COLLECTION ROUTE")

    def reset_route(self):
        self.route = []
        self.initial_route = []
        self.history = []
        self.refresh_all()
        self.log("Route display reset.")

    def on_select(self, _event=None):
        selection = self.tree.selection()
        self.selected_point = int(selection[0]) if selection else None

    def add_point_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add collection point")
        dialog.configure(bg=PANEL)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        fields = {}
        for row, (label, key, default) in enumerate([
            ("Location name", "name", ""),
            ("Waste level (0–100)", "waste", "50"),
            ("Priority (High/Medium/Low)", "priority", "Medium"),
        ]):
            tk.Label(dialog, text=label, bg=PANEL, fg=TEXT, font=("Segoe UI", 9)).grid(
                row=row, column=0, sticky="w", padx=14, pady=8)
            if key == "priority":
                var = tk.StringVar(value=default)
                widget = ttk.Combobox(dialog, textvariable=var, values=["High", "Medium", "Low"],
                                      state="readonly", width=23)
                fields[key] = var
            else:
                widget = tk.Entry(dialog, bg=PANEL_2, fg=TEXT, insertbackground=TEXT,
                                  relief="flat", width=26)
                widget.insert(0, default)
                fields[key] = widget
            widget.grid(row=row, column=1, padx=14, pady=8)

        def save():
            name = fields["name"].get().strip()
            try:
                waste = int(fields["waste"].get())
            except ValueError:
                messagebox.showerror("Invalid waste level", "Enter a whole number from 0 to 100.", parent=dialog)
                return
            if not name:
                messagebox.showerror("Missing name", "Enter a location name.", parent=dialog)
                return
            if not 0 <= waste <= 100:
                messagebox.showerror("Invalid waste level", "Waste level must be 0–100.", parent=dialog)
                return
            # Place new points in a deterministic ring so the prototype remains self-contained.
            n = len(self.points)
            angle = n * 2.399963
            self.points.append({
                "name": name, "x": min(.92, max(.08, .5 + .38 * math.cos(angle))),
                "y": min(.90, max(.08, .48 + .36 * math.sin(angle))),
                "waste": waste, "priority": fields["priority"].get(), "status": "Pending"
            })
            self.route = []
            self.save_data()
            self.refresh_all()
            self.log(f"Added collection point: {name}.")
            dialog.destroy()

        self.make_button(dialog, "Save point", save, GREEN, "#082116").grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=14, pady=14)

    def remove_point(self):
        idx = self.selected_point
        if idx is None:
            messagebox.showinfo("Select a point", "Select a collection point in the table first.")
            return
        if idx == 0:
            messagebox.showwarning("Cannot remove depot", "The depot is required as the route start.")
            return
        name = self.points[idx]["name"]
        if not messagebox.askyesno("Remove point", f"Remove '{name}' from the collection plan?"):
            return
        self.points.pop(idx)
        self.route = []
        self.initial_route = []
        self.save_data()
        self.refresh_all()
        self.log(f"Removed collection point: {name}.")
        self.selected_point = None

    def mark_collected(self):
        if not self.route:
            messagebox.showinfo("No optimized route", "Optimize a route first.")
            return
        changed = []
        for idx in self.route:
            if idx != 0 and self.points[idx]["status"] != "Collected":
                self.points[idx]["status"] = "Collected"
                changed.append(self.points[idx]["name"])
        if not changed:
            messagebox.showinfo("Already collected", "All locations on this route are already marked collected.")
            return
        self.collection_log.append({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "truck": self.truck_var.get(),
            "locations": "; ".join(changed),
            "route_distance_km": round(route_distance(self.route, self.points), 2),
            "status": "Simulated collection complete"
        })
        self.save_data()
        self.refresh_all()
        self.log("Marked collected: " + ", ".join(changed))
        messagebox.showinfo("Collection updated", f"Marked {len(changed)} locations as collected.")

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            title="Save waste collection report", defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="debre_birhan_waste_report.csv")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Debre Birhan Smart Waste Collection Report"])
                writer.writerow(["Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                writer.writerow(["Selected truck", self.truck_var.get()])
                writer.writerow([])
                writer.writerow(["Location", "Waste level (%)", "Priority", "Status"])
                for p in self.points:
                    writer.writerow([p["name"], p["waste"], p["priority"], p["status"]])
                writer.writerow([])
                writer.writerow(["Optimized route"])
                if self.route:
                    writer.writerow([" -> ".join(self.points[i]["name"] for i in self.route)])
                    writer.writerow(["Distance (km)", round(route_distance(self.route, self.points), 2)])
                    writer.writerow(["Hill climbing improving steps", self.iterations])
                writer.writerow([])
                writer.writerow(["Collection activity"])
                writer.writerow(["Timestamp", "Truck", "Locations", "Distance (km)", "Status"])
                for item in self.collection_log:
                    writer.writerow([item["timestamp"], item["truck"], item["locations"],
                                     item["route_distance_km"], item["status"]])
            self.log(f"Exported report to {Path(path).name}.")
            messagebox.showinfo("Export successful", f"Report saved:\n{path}")
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))


def main():
    root = tk.Tk()
    app = WasteApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
