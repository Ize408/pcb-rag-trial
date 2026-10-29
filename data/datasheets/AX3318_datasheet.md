# AX3318 - 300 mA Low-Dropout Linear Regulator
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
