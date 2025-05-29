import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import ImageGrab
import random
import csv
import os
from collections import Counter

INCH_TO_MM = 25.4

class CutOptimizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("1D Cut Optimizer")
        self.root.geometry("1400x800")

        self.stock_length_mm_var = tk.StringVar(value="2438.4")
        self.stock_length_ft_var = tk.StringVar(value="8")
        self.stock_length_in_var = tk.StringVar(value="0")
        self.kerf_var = tk.StringVar(value="4.5")
        self.price_per_pound_var = tk.StringVar(value="4.00")
        self.stock_weight_lb_var = tk.StringVar(value="6.5")
        self.stock_weight_kg_var = tk.StringVar()
        self.weight_per_foot_var = tk.StringVar()
        self.stock_cost_var = tk.StringVar()

        self.parts = []

        self.stock_length_ft_var.trace_add("write", lambda *args: self.calculate_weight_per_foot())
        self.stock_length_in_var.trace_add("write", lambda *args: self.calculate_weight_per_foot())
        self.stock_weight_lb_var.trace_add("write", lambda *args: self.calculate_weight_per_foot())
        self.price_per_pound_var.trace_add("write", lambda *args: self.calculate_stock_cost())

        self.calculate_weight_per_foot()
        self.calculate_stock_cost()

        control_frame = tk.Frame(root)
        control_frame.pack(side="top", anchor="nw", fill="x")

        self.save_btn = tk.Button(control_frame, text="Take a Screenshot", font=("Arial", 11, "bold"), bg="#eef")
        self.save_btn.pack_forget()
        tk.Button(control_frame, text="Import CSV", command=self.import_csv).pack(side="left")
        tk.Button(control_frame, text="Export CSV", command=self.export_csv).pack(side="left")

        main_frame = tk.Frame(root)
        main_frame.pack(fill="x")

        upper_frame = tk.Frame(main_frame)
        upper_frame.pack(fill="x", padx=10, pady=10)

        kerf_frame = tk.LabelFrame(upper_frame, text="Kerf", bg="#ffe")
        kerf_frame.pack(side="left", padx=10, pady=5)
        tk.Label(kerf_frame, text="Kerf (mm):", bg="#ffe", font=("Arial", 10, "bold")).pack(anchor="w")
        tk.Entry(kerf_frame, textvariable=self.kerf_var, width=6).pack(anchor="w", padx=5, pady=2)

        list_frame = tk.LabelFrame(upper_frame, text="Cutting List")
        list_frame.pack(padx=5, pady=5, side="left")
        self.list_frame = list_frame

        headers = ["Name", "Length (mm)", "Length (in)", "Quantity"]
        for i, h in enumerate(headers):
            tk.Label(list_frame, text=h, font=("Arial", 10, "bold")).grid(row=0, column=i, padx=10, pady=5)

        self.rows = []
        self.add_row()

        tk.Button(list_frame, text="Add Row", command=self.add_row).grid(row=1, column=4, padx=5)
        tk.Button(list_frame, text="Clear", command=self.clear_rows).grid(row=1, column=5)

        stock_frame = tk.LabelFrame(main_frame, text="Stock Details")
        stock_frame.pack(padx=10, pady=5, anchor="w")

        tk.Label(stock_frame, text="Stock Length (ft):").grid(row=0, column=0)
        tk.Entry(stock_frame, textvariable=self.stock_length_ft_var, width=5).grid(row=0, column=1)
        tk.Label(stock_frame, text="in:").grid(row=0, column=2)
        tk.Entry(stock_frame, textvariable=self.stock_length_in_var, width=5).grid(row=0, column=3)
        tk.Label(stock_frame, text="mm:").grid(row=0, column=4)
        tk.Entry(stock_frame, textvariable=self.stock_length_mm_var, width=8).grid(row=0, column=5)

        tk.Button(root, text="Optimize", command=self.optimize, bg="green", fg="white", font=("Arial", 12)).pack(pady=(5, 0), anchor="center")

        canvas_frame = tk.Frame(root)
        canvas_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(canvas_frame, bg="white")
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=scrollbar.set)

    def add_row(self):
        row = len(self.rows) + 1
        name_var = tk.StringVar()
        mm_var = tk.StringVar()
        in_var = tk.StringVar()
        qty_var = tk.StringVar(value="1")

        def update_inch(*_):
            try:
                mm = float(mm_var.get())
                in_val = mm / INCH_TO_MM
                in_var.set(f"{in_val:.3f}")
            except:
                pass

        def update_mm(*_):
            try:
                inch = float(in_var.get())
                mm_val = inch * INCH_TO_MM
                mm_var.set(f"{mm_val:.1f}")
            except:
                pass

        mm_var.trace_add("write", update_inch)
        in_var.trace_add("write", update_mm)

        tk.Entry(self.list_frame, textvariable=name_var, width=15, font=("Arial", 10)).grid(row=row, column=0, padx=5, pady=2)
        tk.Entry(self.list_frame, textvariable=mm_var, width=12, font=("Arial", 10)).grid(row=row, column=1, padx=5, pady=2)
        tk.Entry(self.list_frame, textvariable=in_var, width=12, font=("Arial", 10)).grid(row=row, column=2, padx=5, pady=2)
        qty_entry = tk.Entry(self.list_frame, textvariable=qty_var, width=8, font=("Arial", 10))
        qty_entry.grid(row=row, column=3, padx=5, pady=2)
        qty_entry.bind("<Return>", lambda event: self.add_row())

        self.rows.append((name_var, mm_var, in_var, qty_var))

    def clear_rows(self, add_blank=True):
        for widget in self.list_frame.grid_slaves():
            if int(widget.grid_info()["row"]) > 0:
                widget.destroy()
        self.rows.clear()
        if add_blank:
            self.add_row()

    def import_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        self.clear_rows(add_blank=False)
        with open(file_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
            if rows and rows[0][0].strip().lower() == "kerf":
                try:
                    self.kerf_var.set(rows[0][1])
                except:
                    pass
                rows = rows[2:]  # Skip kerf and headers
            for row in rows:
                if len(row) < 4:
                    continue
                self.add_row()
                self.rows[-1][0].set(row[0])
                self.rows[-1][1].set(row[1])
                self.rows[-1][2].set(row[2])
                self.rows[-1][3].set(row[3])
            


    def export_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not file_path:
            return
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Kerf", self.kerf_var.get()])
            writer.writerow(["Name", "Length (mm)", "Length (in)", "Quantity"])
            for row in self.rows:
                writer.writerow([
                    row[0].get(),
                    row[1].get(),
                    row[2].get(),
                    row[3].get()
                ])

    def calculate_weight_per_foot(self):
        try:
            ft = float(self.stock_length_ft_var.get()) + float(self.stock_length_in_var.get()) / 12
            lb = float(self.stock_weight_lb_var.get())
            self.weight_per_foot_var.set(f"{lb / ft:.3f}")
        except:
            self.weight_per_foot_var.set("?")

    def calculate_stock_cost(self):
        try:
            cost = float(self.price_per_pound_var.get()) * float(self.stock_weight_lb_var.get())
            self.stock_cost_var.set(f"${cost:.2f}")
        except:
            self.stock_cost_var.set("?")

    def save_jpeg(self):
        from PIL import ImageGrab
        import tempfile

        self.canvas.update()
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty()
        w = x + self.canvas.winfo_width()
        h = y + self.canvas.winfo_height()

        image = ImageGrab.grab(bbox=(x, y, w, h))

        preview = tk.Toplevel(self.root)
        preview.title("Preview")
        image_resized = image.copy()
        image_resized.thumbnail((1000, 800))

        from PIL import ImageTk
        img_tk = ImageTk.PhotoImage(image_resized)
        label = tk.Label(preview, image=img_tk)
        label.image = img_tk
        label.pack()

        def confirm():
            path = filedialog.asksaveasfilename(defaultextension=".jpg")
            if path:
                image.save(path)
                os.startfile(path, "print")
                messagebox.showinfo("Saved", f"Saved and sent to printer: {path}")
            preview.destroy()

        tk.Button(preview, text="Save Screenshot", font=("Arial", 11, "bold"), command=confirm).pack(pady=10)

    def optimize(self):
        try:
            parts = []
            for row in self.rows:
                try:
                    name = row[0].get()
                    length = float(row[1].get())
                    qty = int(row[3].get())
                    parts.extend([(name, length)] * qty)
                except:
                    continue

            stock_length = float(self.stock_length_mm_var.get())
            kerf = float(self.kerf_var.get())

            parts.sort(key=lambda x: -x[1])
            results = []

            for name, length in parts:
                placed = False
                for stock in results:
                    if stock['remaining'] >= length + kerf:
                        stock['cuts'].append((name, length))
                        stock['remaining'] -= (length + kerf)
                        placed = True
                        break
                if not placed:
                    results.append({"cuts": [(name, length)], "remaining": stock_length - length - kerf})

            self.display_results(results, stock_length, kerf)
            self.save_btn.pack(side="right", padx=10)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def display_results(self, results, stock_length, kerf):
        from collections import defaultdict
        self.canvas.delete("all")
        margin = 10
        bar_h = 20
        gap_between_stocks = 15
        canvas_width = self.canvas.winfo_width()
        scale = (canvas_width - 2 * margin) / stock_length

                # Group identical stock cuts
        layout_counter = Counter()
        layout_map = defaultdict(list)
        for stock in results:
            layout_key = tuple(stock["cuts"])
            layout_counter[layout_key] += 1
            layout_map[layout_key].append(stock["remaining"])

        y = margin
        for layout_key, count in layout_counter.items():
            stock_cuts = layout_key
            remaining_len = layout_map[layout_key][0]  # just use the first one for display

            x = margin
            color_map = {}
            part_counter = Counter()

            for name, length in stock_cuts:
                if name not in color_map:
                    color_map[name] = f"#{random.randint(0, 0xFFFFFF):06x}"
                color = color_map[name]
                cut_len = max(length * scale, 1)
                self.canvas.create_rectangle(x, y, x + cut_len, y + bar_h, fill=color, outline="black")
                if cut_len > 25:
                    self.canvas.create_text(x + cut_len / 2, y + bar_h / 2, text=name, fill="white", font=("Arial", 10, "bold"))
                x += cut_len + kerf * scale
                part_counter[name] += 1

            if remaining_len > 0:
                remaining_w = remaining_len * scale
                self.canvas.create_rectangle(x, y, x + remaining_w, y + bar_h, fill="lightgray", outline="black")
                if remaining_w > 40:
                    self.canvas.create_text(x + remaining_w / 2, y + bar_h / 2, text="Remaining", fill="black", font=("Arial", 10, "italic"))

            # Label with how many times this stock layout is used
            if count > 1:
                self.canvas.create_text(margin + 300, y + bar_h + 10, anchor="w", text=f"--> CUT {count} LIKE THIS", font=("Arial", 12, "italic"), fill="gray")

            summary_lines = [f"{k}: {v}" for k, v in part_counter.items()]
            summary_text = " / ".join(summary_lines)
            self.canvas.create_text(margin, y + bar_h + 10, anchor="nw", text=summary_text, font=("Arial", 12, "bold"))

            y += bar_h + 25 + gap_between_stocks

        self.canvas.config(scrollregion=(0, 0, canvas_width, y))

if __name__ == "__main__":
    root = tk.Tk()
    app = CutOptimizerApp(root)
    root.mainloop()
