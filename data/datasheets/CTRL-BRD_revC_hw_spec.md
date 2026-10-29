# CTRL-BRD Hardware Specification - Revision C
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
