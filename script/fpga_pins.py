import re
import requests
import tkinter as tk
from tkinter import ttk

def fetch_pinout_txt(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text

def parse_pinout(txt):
    pins = []
    for line in txt.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("L0:"):
            continue
        parts = re.split(r'\s+', line)
        if len(parts) < 6:
            continue
        pin = parts[0]
        pinname = parts[1]
        bank = parts[3]
        io_type = parts[-2]
        no_connect = parts[-1]
        pins.append({
            "pin": pin,
            "name": pinname,
            "bank": bank,
            "io_type": io_type,
            "no_connect": no_connect
        })
    return pins

def is_usable_gpio(pininfo):
    name = pininfo["name"]
    io_type = pininfo["io_type"]
    no_connect = pininfo["no_connect"]
    bad_keywords = ["VREF", "VCCAUX", "VCCINT", "VCCO", "GROUND", "GND", "CONFIG", "NO-CONNECT", "NC"]
    for kw in bad_keywords:
        if kw in name.upper():
            return False
    if io_type.upper() == "CONFIG":
        return False
    if no_connect.upper() != "NA":
        return False
    return True

def get_sorted_gpio_pins(txt):
    pins = parse_pinout(txt)
    usable = [p for p in pins if is_usable_gpio(p)]
    def pin_key(p):
        m = re.match(r'^([A-Z]+)(\d+)$', p["pin"], re.IGNORECASE)
        if m:
            letters = m.group(1)
            num = int(m.group(2))
            return (letters, num)
        else:
            return (p["pin"], 0)
    usable_sorted = sorted(usable, key=pin_key)
    return usable_sorted

def show_pins_window(pins):
    root = tk.Tk()
    root.title("Usable GPIO Pins")

    # Create a frame with scrollbar
    container = ttk.Frame(root)
    canvas = tk.Canvas(container, height=600, width=700)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scroll_frame = ttk.Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Pack widgets
    container.pack(fill="both", expand=True)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Add pin rows with checkboxes
    check_vars = []
    for p in pins:
        var = tk.BooleanVar()
        check_vars.append(var)
        text = f"{p['pin']:4s}  {p['name']:30s}  Bank {p['bank']:>2s}  I/O Type {p['io_type']:>3s}"
        row = ttk.Checkbutton(scroll_frame, text=text, variable=var)
        row.pack(anchor="w", padx=5, pady=2)

    def _on_mousewheel(event):
        if event.num == 4 or event.delta > 0:   # Linux (button 4) or Windows/Mac delta positive
            canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0: # Linux (button 5) or Windows/Mac delta negative
            canvas.yview_scroll(1, "units")

    # Windows / Mac
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    # Linux (X11)
    canvas.bind_all("<Button-4>", _on_mousewheel)
    canvas.bind_all("<Button-5>", _on_mousewheel)
    root.mainloop()

def main():
    url = "https://download.amd.com/adaptive-socs-and-fpgas/developer/adaptive-socs-and-fpgas/package-pinout-files/a7packages/xc7a100tftg256pkg.txt"
    txt = fetch_pinout_txt(url)
    usable = get_sorted_gpio_pins(txt)
    show_pins_window(usable)

if __name__ == "__main__":
    main()
