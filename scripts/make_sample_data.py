"""
Creates the sample docs in data/. All parts here are made up (AX3318, BK1210,
CTRL-BRD) so the repo doesn't ship anyone's copyrighted datasheets.
Drop your own PDFs / logs into data/ and re-run ingest.
"""
import random
from datetime import datetime, timedelta
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table

DATA = Path(__file__).resolve().parent.parent / "data"

AX3318 = """# AX3318 - 300 mA Low-Dropout Linear Regulator
Aerix Semiconductor - Datasheet Rev 1.4

## 1 Features
- Input voltage range: 2.5 V to 5.5 V
- Fixed output voltages: 1.8 V, 2.5 V, 3.3 V
- Output current up to 300 mA
- Low dropout: 180 mV typical at 300 mA
- Quiescent current: 45 uA typical
- Output accuracy: +/-1% at 25 C, +/-2% over temperature
- Stable with 1 uF ceramic output capacitor
- Active-high enable pin, internal pull-down
- Thermal shutdown and current limit
- Package: SOT-23-5

## 2 Pin Configuration (SOT-23-5, top view)
| Pin | Name | Description |
|-----|------|-------------|
| 1 | VIN | Supply input. Place a 1 uF ceramic capacitor close to the pin |
| 2 | GND | Ground |
| 3 | EN | Enable input. High = on, low = shutdown. Do not leave floating in noisy designs |
| 4 | NC | No connection |
| 5 | VOUT | Regulated output. Requires minimum 1 uF ceramic capacitor |

## 3 Absolute Maximum Ratings
Stresses beyond these ratings may cause permanent damage.
- VIN to GND: -0.3 V to 6.5 V
- EN to GND: -0.3 V to VIN + 0.3 V
- VOUT to GND: -0.3 V to 4.0 V
- Junction temperature: 150 C
- Storage temperature: -65 C to 150 C
- ESD (HBM): 2 kV

## 4 Recommended Operating Conditions
- VIN: 2.5 V to 5.5 V
- Output current: 0 to 300 mA
- Operating junction temperature: -40 C to 125 C

## 5 Electrical Characteristics
VIN = VOUT + 1 V, IOUT = 1 mA, CIN = COUT = 1 uF, TA = 25 C unless noted.

| Parameter | Conditions | Min | Typ | Max | Unit |
|-----------|-----------|-----|-----|-----|------|
| Output accuracy | IOUT = 1 mA | -1 | | 1 | % |
| Dropout voltage | IOUT = 300 mA, VOUT = 3.3 V | | 180 | 250 | mV |
| Dropout voltage | IOUT = 100 mA, VOUT = 3.3 V | | 60 | 90 | mV |
| Quiescent current | IOUT = 0 mA, EN = VIN | | 45 | 70 | uA |
| Shutdown current | EN = 0 V | | 0.1 | 1 | uA |
| Current limit | | 350 | 450 | 600 | mA |
| Line regulation | VIN = VOUT + 0.5 V to 5.5 V | | 0.02 | 0.1 | %/V |
| Load regulation | IOUT = 1 mA to 300 mA | | 0.4 | 1 | % |
| PSRR | f = 1 kHz, IOUT = 30 mA | | 65 | | dB |
| EN high threshold | | 1.2 | | | V |
| EN low threshold | | | | 0.4 | V |
| Thermal shutdown | | | 160 | | C |

## 6 Thermal Information
- Junction-to-ambient thermal resistance (theta JA), SOT-23-5: 120 C/W
- Power dissipation: PD = (VIN - VOUT) x IOUT
- Example: VIN = 5 V, VOUT = 3.3 V, IOUT = 250 mA gives PD = 0.425 W and a
  temperature rise of about 51 C above ambient.

## 7 Application Information
Input capacitor: use at least 1 uF X5R or X7R ceramic, placed within 5 mm of VIN.
Output capacitor: 1 uF to 22 uF ceramic. ESR must be below 0.5 ohm. Larger output
capacitance improves load transient response.
Enable: connect EN to VIN for always-on operation.

## 8 Layout Guidelines
- Keep input and output capacitors as close as possible to the IC
- Use a solid ground plane under the device
- Add thermal vias under the GND pin for designs above 200 mA
"""

CTRL_BRD = """# CTRL-BRD Hardware Specification - Revision C
Internal document HW-SPEC-0042, owner: hardware team

## 1 Overview
CTRL-BRD is the main controller board. It takes 5 V from the USB-C connector (J1)
and generates 3.3 V (U3, AX3318 LDO) and 1.2 V (U4, BK1210 buck) rails.
MCU: U1. UART debug header: J4.

## 2 Power Rails
| Rail | Source | Nominal | Test limits | Test point |
|------|--------|---------|-------------|------------|
| VBUS | J1 USB-C | 5.0 V | 4.75 - 5.25 V | TP5 |
| 3V3 | U3 AX3318 | 3.3 V | 3.20 - 3.40 V | TP1 |
| 1V2 | U4 BK1210 | 1.2 V | 1.164 - 1.236 V | TP2 |
| GND | | | | TP3, TP4 |

Total board current at power on (no peripherals): 250 - 400 mA, typical 310 mA.

## 3 Connectors
- J1: USB-C, power input only on rev C
- J2: 2x5 SWD programming header
- J3: sensor connector (I2C + 3V3)
- J4: UART debug header, 3 pins: TX, RX, GND. 115200 baud, 3.3 V logic
- J5: external relay output

## 4 Bring-up Procedure
1. Check for shorts: resistance from TP1 (3V3) to GND should be above 1 kOhm
2. Apply 5 V with current limit set to 500 mA on the bench supply
3. Measure 3V3 at TP1 and 1V2 at TP2
4. Flash the test firmware through J2
5. Connect a USB-UART adapter to J4 and check the boot banner

## 5 Revision History
- Rev A: first prototype
- Rev B: moved 1V2 regulator to the top side. Known issue: UART RX pull-up R12 was
  10 kOhm to 1V2 instead of 3V3, causing intermittent UART loopback failures.
- Rev C: R12 changed to 4.7 kOhm pulled up to 3V3, fixes the UART issue from rev B.
  C21 (1V2 output cap) increased from 10 uF to 22 uF to reduce ripple.

## 6 Known Issues (rev C)
- Boards from PCB lot L2408 have a slightly higher power on current (about 380 mA)
  because of a different LED part (D3). Still inside test limits.
- If 1V2 reads low (below 1.164 V), check the feedback resistors R30/R31 on U4.
"""

BK1210_PAGES = [
    ("BK1210 - 2 A Synchronous Step-Down Converter", [
        "Aerix Semiconductor. Datasheet Rev 2.0.",
        "The BK1210 is a 1.2 MHz synchronous buck converter that delivers up to 2 A "
        "of output current from a 3 V to 17 V input. The output voltage is adjustable "
        "from 0.6 V using an external resistor divider.",
        "Features: input voltage 3 V to 17 V; output current up to 2 A continuous; "
        "switching frequency 1.2 MHz fixed; feedback reference 0.6 V +/-1.5%; "
        "internal soft start 1 ms; power-good output (PGOOD, open drain); "
        "efficiency up to 94%; package SOT-563.",
    ]),
    ("Absolute maximum ratings and pinout", [
        "Absolute maximum ratings: VIN to GND -0.3 V to 18 V. SW to GND -0.3 V to VIN + 0.3 V. "
        "FB, EN, PGOOD to GND -0.3 V to 6 V. Junction temperature 150 C.",
        "Pinout (SOT-563): pin 1 FB, pin 2 EN, pin 3 VIN, pin 4 GND, pin 5 SW, pin 6 PGOOD.",
    ]),
    ("Setting the output voltage", [
        "VOUT = 0.6 V x (1 + R1 / R2), where R1 is the top resistor from VOUT to FB and "
        "R2 is the bottom resistor from FB to GND.",
        "For 1.2 V output use R1 = R2 = 100 kOhm. For 3.3 V output use R1 = 453 kOhm "
        "and R2 = 100 kOhm.",
        "Use 1% resistors. Resistor tolerance directly affects output accuracy.",
    ]),
    ("Component selection", [
        "Inductor: 2.2 uH recommended for VOUT below 1.8 V, 4.7 uH for VOUT of 3.3 V and above. "
        "Saturation current should be at least 3 A. DCR below 50 mOhm.",
        "Output capacitor: 22 uF X5R or X7R ceramic minimum. Two 22 uF in parallel reduce "
        "ripple further. Input capacitor: 10 uF ceramic close to VIN.",
        "Output ripple with 2.2 uH and 22 uF is typically 10 mV peak-to-peak at 1 A load.",
    ]),
    ("Layout", [
        "Keep the SW node area small, it is the main source of EMI. Place the input capacitor "
        "as close as possible to VIN and GND. Route the FB trace away from the inductor and SW node.",
    ]),
]

STEPS = [
    # name, unit, lo, hi, nominal, sigma
    ("power_on_current", "mA", 250.0, 400.0, 312.0, 15.0),
    ("rail_vbus", "V", 4.75, 5.25, 5.02, 0.03),
    ("rail_3v3", "V", 3.200, 3.400, 3.298, 0.012),
    ("rail_1v2", "V", 1.164, 1.236, 1.201, 0.008),
    ("ripple_1v2", "mV", 0.0, 25.0, 9.0, 2.5),
    ("flash_firmware", None, None, None, None, None),
    ("uart_loopback", None, None, None, None, None),
    ("i2c_sensor_scan", None, None, None, None, None),
    ("relay_toggle", None, None, None, None, None),
]


def make_logs(n=40, seed=11):
    rng = random.Random(seed)
    out = DATA / "test_logs"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.log"):
        f.unlink()
    t = datetime(2026, 9, 14, 8, 0, 0)
    for i in range(n):
        serial = f"CB-24-{100 + i:05d}"
        lot = "L2408" if 20 <= i < 30 else "L2406"
        rev = "B" if i < 6 else "C"   # a few old rev B boards still in the batch
        station = rng.choice(["FCT-01", "FCT-02"])
        t += timedelta(minutes=rng.randint(4, 15))
        lines = [
            "=== CTRL-BRD FUNCTIONAL TEST ===",
            f"station: {station}",
            f"board: CTRL-BRD rev {rev}",
            f"serial: {serial}",
            f"pcb_lot: {lot}",
            f"operator: {rng.choice(['jm', 'kd', 'ar'])}",
            f"start: {t:%Y-%m-%d %H:%M:%S}",
            "",
        ]
        failed = False
        ts = t
        for k, (name, unit, lo, hi, nom, sd) in enumerate(STEPS, start=1):
            ts += timedelta(seconds=rng.randint(1, 4))
            if unit:
                v = rng.gauss(nom, sd)
                if name == "power_on_current" and lot == "L2408":
                    v += 65
                if name == "rail_1v2" and serial in ("CB-24-00113", "CB-24-00131"):
                    v = 1.152 + rng.random() * 0.006  # bad feedback resistor
                if name == "ripple_1v2" and rev == "B":
                    v += 9  # 10 uF cap on rev B
                ok = lo <= v <= hi
                dec = 1 if unit in ("mA", "mV") else 3
                lines.append(f"[{ts:%H:%M:%S}] STEP {k:02d} {name:<18} {v:>8.{dec}f} {unit:<3} "
                             f"lim {lo:.{dec}f}..{hi:.{dec}f}   {'PASS' if ok else 'FAIL'}")
            else:
                ok, note = True, ""
                if name == "uart_loopback" and rev == "B" and rng.random() < 0.7:
                    ok, note = False, "(timeout after 500 ms, 0/64 bytes received)"
                if name == "i2c_sensor_scan" and serial == "CB-24-00127":
                    ok, note = False, "(no ACK at 0x44, J3 not seated?)"
                lines.append(f"[{ts:%H:%M:%S}] STEP {k:02d} {name:<18} {'-':>8} {'':<3} "
                             f"{'':<18}   {'PASS' if ok else 'FAIL'} {note}".rstrip())
            failed |= not ok
        lines += ["", f"result: {'FAIL' if failed else 'PASS'}", f"end: {ts:%Y-%m-%d %H:%M:%S}"]
        (out / f"{serial}_{t:%Y%m%d_%H%M%S}.log").write_text("\n".join(lines) + "\n")


def make_pdf():
    path = DATA / "datasheets" / "BK1210_datasheet.pdf"
    styles = getSampleStyleSheet()
    story = []
    for i, (title, paras) in enumerate(BK1210_PAGES):
        story.append(Paragraph(title, styles["Heading1"]))
        for p in paras:
            story.append(Paragraph(p, styles["BodyText"]))
            story.append(Spacer(1, 8))
        if i == 0:
            story.append(Table([["Parameter", "Value"], ["VIN", "3 - 17 V"], ["IOUT", "2 A"],
                                ["fSW", "1.2 MHz"], ["VFB", "0.6 V"]]))
        story.append(PageBreak())
    SimpleDocTemplate(str(path), pagesize=A4, title="BK1210 datasheet").build(story)


if __name__ == "__main__":
    (DATA / "datasheets").mkdir(parents=True, exist_ok=True)
    (DATA / "datasheets" / "AX3318_datasheet.md").write_text(AX3318)
    (DATA / "datasheets" / "CTRL-BRD_revC_hw_spec.md").write_text(CTRL_BRD)
    make_pdf()
    make_logs()
    print("sample data written to data/")
