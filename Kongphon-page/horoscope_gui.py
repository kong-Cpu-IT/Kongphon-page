import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

DATA_FILE = Path(__file__).with_name("daily_horoscope.json")


def load_horoscope_data(path: Path):
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        messagebox.showerror("ไฟล์ไม่พบ", f"ไม่พบไฟล์ข้อมูล: {path}")
        sys.exit(1)
    except json.JSONDecodeError as exc:
        messagebox.showerror("ไฟล์ไม่ถูกต้อง", f"อ่านไฟล์ JSON ไม่สำเร็จ: {exc}")
        sys.exit(1)


def format_horoscope(entry):
    return (
        f"ราศี: {entry['sign']}\n"
        f"คำทำนาย: {entry['prediction']}\n"
        f"เลขนำโชค: {entry['lucky_number']}\n"
        f"สีมงคล: {entry['lucky_color']}\n"
        f"คำแนะนำ: {entry['advice']}\n"
    )


class HoroscopeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("โปรแกรมทำนายดวงรายวัน")
        self.root.geometry("560x520")
        self.root.resizable(False, False)

        self.data = load_horoscope_data(DATA_FILE)
        self.horoscopes = self.data.get("horoscopes", [])
        self.signs = [entry["sign"] for entry in self.horoscopes]

        self.create_widgets()

    def create_widgets(self):
        title = ttk.Label(self.root, text="ทำนายดวงรายวัน", font=(None, 18, "bold"))
        title.pack(pady=(12, 6))

        info_text = f"วันที่: {self.data.get('date', 'ไม่ระบุ')}  |  แหล่ง: {self.data.get('source', 'ไม่ระบุ')}"
        info = ttk.Label(self.root, text=info_text, font=(None, 10))
        info.pack(pady=(0, 12))

        input_frame = ttk.Frame(self.root)
        input_frame.pack(fill="x", padx=16, pady=8)

        sign_label = ttk.Label(input_frame, text="เลือกราศี:")
        sign_label.pack(side="left", padx=(0, 8))

        self.sign_var = tk.StringVar()
        self.sign_combo = ttk.Combobox(
            input_frame,
            textvariable=self.sign_var,
            values=self.signs,
            state="readonly",
            width=24,
        )
        self.sign_combo.pack(side="left", padx=(0, 8))
        if self.signs:
            self.sign_combo.current(0)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=16, pady=(0, 10))

        show_button = ttk.Button(btn_frame, text="ดูดวง", command=self.show_selected)
        show_button.pack(side="left", padx=(0, 6))

        all_button = ttk.Button(btn_frame, text="ดูทั้งหมด", command=self.show_all)
        all_button.pack(side="left")

        self.output = tk.Text(
            self.root,
            wrap="word",
            height=20,
            padx=12,
            pady=12,
            font=(None, 10),
            state="disabled",
        )
        self.output.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.show_selected()

    def show_selected(self):
        sign_name = self.sign_var.get()
        if not sign_name:
            messagebox.showwarning("เลือกก่อน", "กรุณาเลือกชื่อราศีก่อน")
            return

        entry = next((item for item in self.horoscopes if item["sign"] == sign_name), None)
        if not entry:
            messagebox.showerror("ไม่พบข้อมูล", f"ไม่พบคำทำนายสำหรับราศี {sign_name}")
            return

        self.set_output(format_horoscope(entry))

    def show_all(self):
        if not self.horoscopes:
            self.set_output("ไม่มีข้อมูลคำทำนาย")
            return

        text = ""
        for entry in self.horoscopes:
            text += format_horoscope(entry)
            text += "\n" + "-" * 60 + "\n\n"
        self.set_output(text.strip())

    def set_output(self, text):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.configure(state="disabled")


def main():
    root = tk.Tk()
    app = HoroscopeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
