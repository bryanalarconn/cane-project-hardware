# Sight-Stick — Pico Hardware Controller

**An assistive smart cane for visually impaired individuals.**

Sight-Stick is a wearable navigation device that combines ultrasonic obstacle detection with AI-powered computer vision to help visually impaired users navigate their environment safely. This repository contains the **MicroPython firmware** that runs on a Raspberry Pi Pico, controlling all sensors, motors, buttons, and communication with a companion Raspberry Pi 5.

> Senior Capstone Project by **Bryan Alarcon** & **Christian Hernandez**

---

## How It Works

The Pico acts as the device's hardware controller, managing two operating modes:

| Mode | Trigger | What It Does |
|------|---------|--------------|
| **Mode 1 — Sonar** | Single-click SW3 | HC-SR04 ultrasonic sensor measures distance; vibration motor intensity scales linearly from gentle (75 cm) to full (≤10 cm). Provides real-time haptic obstacle feedback. |
| **Mode 2 — YOLO** | Long-press SW4 | Sends `YOLO_TRIGGER` over UART to the Pi 5, which runs YOLOv8n object detection on a Camera Module 3 feed with text-to-speech audio output. |

A state machine governs the device lifecycle:

```
OFF ──long-press SW3──▶ STANDBY ──single-click SW3──▶ MODE 1 (Sonar)
                         │                                │
                         │──long-press SW4──▶ MODE 2 (YOLO)│
                         │                                │
                    long-press SW3 ◀── (from any mode) ───┘
                         │
                        OFF
```

At boot, a self-check routine tests all six peripherals (buzzer, motor, ultrasonic sensor, UART link, and both buttons) and reports PASS/WARN/FAIL for each.

---

## Hardware

| Component | Connection |
|-----------|------------|
| Raspberry Pi Pico | Main controller (MicroPython) |
| HC-SR04 Ultrasonic Sensor | TRIG → GP17, ECHO → GP16 |
| Vibration Motor (PWM) | GP15 |
| Passive Buzzer (PWM) | GP22 |
| SW3 — Main Button | GP10 (internal pull-up) |
| SW4 — YOLO Button | GP11 (internal pull-up) |
| UART to Raspberry Pi 5 | TX → GP4, RX → GP5 (115200 baud) |

### Power System

3× Samsung 30Q 18650 cells in series (3S1P) → HW-375 BMS → DROK buck converter (output set to 5.2 V) → Raspberry Pi 5 via USB-C. The Pico is powered from the Pi 5's USB port.

---

## Repository Structure

```
cane-project-hardware/
├── main.py          # State machine, main loop, UART commands
├── config.py        # Pin assignments, constants, buzzer sound definitions
├── debug.py         # Conditional debug printing (controlled by DEBUG flag)
├── selfcheck.py     # Boot-time hardware diagnostics for all peripherals
└── drivers/
    ├── __init__.py
    ├── buzzer.py    # PWM buzzer sounds (power on/off, mode start/stop, error)
    ├── button.py    # Debounced button with single-click, double-click, long-press
    ├── motor.py     # PWM vibration motor with distance-to-duty mapping
    └── ultrasonic.py # HC-SR04 distance measurement
```

---

## Getting Started

### Prerequisites

- Raspberry Pi Pico with [MicroPython](https://micropython.org/download/RPI_PICO/) firmware installed
- [Thonny IDE](https://thonny.org/) or `mpremote` for flashing files
- All hardware components wired per the pin map in `config.py`

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/bryanalarconn/cane-project-hardware.git
   ```

2. Connect the Pico to your computer via USB.

3. Copy all files to the Pico's filesystem (using Thonny or `mpremote`):
   ```bash
   mpremote connect auto fs cp -r . :
   ```

4. Reset the Pico. The firmware will run `main.py` automatically, perform the self-check, and enter the OFF state.

### Configuration

All tunable parameters are in `config.py`:

- **`DEBUG`** — Set to `False` to silence all serial output for production use
- **`NEAR` / `FAR`** — Distance thresholds (cm) for vibration intensity mapping (default: 10–75 cm)
- **`LONG_PRESS_MS`** — Hold duration for power on/off and Mode 2 toggle (default: 3000 ms)
- **`DIST_INTERVAL_MS`** — How often the ultrasonic sensor fires in Mode 1 (default: 100 ms)
- **Sound tuples** — Each buzzer sound is defined as a sequence of `(frequency_hz, duration_ms)` pairs

---

## Button Controls

| Action | From State | Result |
|--------|-----------|--------|
| Long-press SW3 | OFF | Power on → Standby |
| Single-click SW3 | Standby | Enter Mode 1 (Sonar) |
| Long-press SW4 | Standby | Enter Mode 2 (YOLO) |
| Double-click SW3 | Mode 1 | Return to Standby |
| Long-press SW4 | Mode 2 | Return to Standby |
| Long-press SW3 | Any mode | Full power off |

---

## Companion Software

The Pi 5 side runs a separate Python script (`mode2.py`) that listens for UART commands from the Pico and manages the YOLOv8n inference pipeline, Camera Module 3 capture, and text-to-speech output via a USB speaker. The Pi 5 also responds to `PING` commands during self-check with a `PONG` handshake.

---

## License

This project was developed as a senior capstone. Please contact the authors for usage or licensing inquiries.
