# 3D Resin Printer Controller

A Python application to control DIY resin 3D printers using Arduino.

## Prerequisites

### Arduino Setup
1. Download FirmataExpress from: [https://github.com/MrYsLab/FirmataExpress](https://github.com/MrYsLab/FirmataExpress)
2. In Arduino IDE:
   - Go to Sketch > Include Library > Add .ZIP Library
   - Select the downloaded ZIP file
   - Navigate to File > Examples > FirmataExpress > FirmataExpress
   - Upload to Arduino

### Required Arduino Libraries
Install these libraries using the Library Manager (Tools > Manage Libraries...):
- NewPing (for ultrasonic sensors)
- Ultrasonic
- Servo
- DHT sensor library (by Adafruit)
- DHTStable (by Rob Tillaart)

### Python Dependencies
Required Python packages:

- PyQt6
- pymata4
- pyserial

## Installation

1. Clone this repository:

2. 
## Usage

1. Connect your Arduino board
2. Run the application:
3. 
## Features

- Multi-language support (English, Spanish, Russian, German, French, Chinese, Hindi, Japanese, Korean, Portuguese)
- Dual monitor support for projection
- Layer-by-layer printing control
- UV LED control
- Z-axis movement control
- Real-time print status monitoring

## Building from Source

To create an executable:
python build.py


## License

This work is licensed under a Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License.

You are free to:
- Share — copy and redistribute the material in any medium or format

Under the following terms:
- Attribution — You must give appropriate credit
- NonCommercial — You may not use the material for commercial purposes
- NoDerivatives — If you remix, transform, or build upon the material, you may not distribute the modified material

## Authors

- Initial work - [juakerjuan : juan fco r.l.]

## Acknowledgments

- FirmataExpress team
- PyQt6 community
