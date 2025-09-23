import re
import requests

def fetch_pinout_txt(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text

def parse_pinout(txt):
    """
    Parse lines like:
    "J13  IO_L1P_T0_D00_MOSI_14  0  14  NA NA HR NA"
    Return list of dicts with fields: pin, name, memory, bank, iotype, etc.
    """
    pins = []
    for line in txt.splitlines():
        line = line.strip()
        if not line:
            continue
        # Skip the header (e.g. L0: ...)
        if line.startswith("L0:"):
            continue
        # Some lines start with whitespace or pin names align differently
        parts = re.split(r'\s+', line)
        # We expect at least: PinName, Pin, Name, Memory (or “0”), Bank, ..., I/O Type, No-Connect, etc.
        # Based on sample, first part is pin (like "J13"), second is pin name, third maybe memory or something.
        # Let’s try to rely on columns: Pin, PinName, Memory/ByteGroup, Bank, I/O Type, etc.
        # From the sample: parts[0]=Pin, parts[1]=PinName, parts[2]=Memory, parts[3]=Bank, ..., parts[-2]=I/O Type, parts[-1]=NC/...
        if len(parts) < 6:
            continue
        pin = parts[0]
        pinname = parts[1]
        # bank is probably parts[3]
        bank = parts[3]
        # I/O Type maybe part of parts near the end
        io_type = None
        no_connect = None
        # heuristic: last two fields
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
    """
    Determine if given pin is usable as GPIO.
    Exclude if:
      - name contains VREF / VCC / VCCAUX / VCCINT / GND / etc
      - I/O Type is “CONFIG” or “NC” or something non-HR/standard
      - no_connect is not “NA” or marks NC
    """
    name = pininfo["name"]
    io_type = pininfo["io_type"]
    no_connect = pininfo["no_connect"]
    # exclude certain keywords
    bad_keywords = ["VREF", "VCCAUX", "VCCINT", "VCCO", "GROUND", "GND", "CONFIG", "NO-CONNECT", "NC"]
    for kw in bad_keywords:
        if kw in name.upper():
            return False
    # Exclude pins defined as CONFIG or I/O Type = CONFIG
    if io_type.upper() == "CONFIG":
        return False
    # Exclude if no_connect is something other than “NA”
    if no_connect.upper() != "NA":
        return False
    # Otherwise assume usable
    return True

def get_sorted_gpio_pins(txt):
    pins = parse_pinout(txt)
    usable = [p for p in pins if is_usable_gpio(p)]
    # We want to sort by pin number — the “pin” field is like “J13”, “L13”, etc.
    # We'll sort lexicographically by letter then number; if you need numeric ordering only, strip letter.
    def pin_key(p):
        # Split into leading letters and number
        m = re.match(r'^([A-Z]+)(\d+)$', p["pin"], re.IGNORECASE)
        if m:
            letters = m.group(1)
            num = int(m.group(2))
            return (letters, num)
        else:
            return (p["pin"], 0)
    usable_sorted = sorted(usable, key=pin_key)
    return usable_sorted

def main():
    url = "https://download.amd.com/adaptive-socs-and-fpgas/developer/adaptive-socs-and-fpgas/package-pinout-files/a7packages/xc7a100tftg256pkg.txt"
    txt = fetch_pinout_txt(url)
    usable = get_sorted_gpio_pins(txt)
    for p in usable:
        print(f"{p['pin']:4s}  {p['name']:30s}  Bank {p['bank']:>2s}  I/O Type {p['io_type']:>3s}")

if __name__ == "__main__":
    main()
