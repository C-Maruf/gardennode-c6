"""Single source of truth for the GardenNode-C6 rev A netlist and BOM.
Every schematic, PCB and BOM file is generated from this list."""
SYM = '/usr/share/kicad/symbols/'
ESPSYM = '/home/claude/dl/esp/symbols/Espressif.kicad_sym'

def R(ref, val, a, b, mpn, fp='Resistor_SMD:R_0603_1608Metric', mfr='Yageo', grp=None):
    return dict(ref=ref, lib=SYM+'Device.kicad_sym', sym='R', fp=fp, value=val, mfr=mfr, mpn=mpn, pins={'1': a, '2': b}, grp=grp)

def C(ref, val, a, b, mpn, fp='Capacitor_SMD:C_0603_1608Metric', mfr='Samsung Electro-Mechanics', grp=None):
    return dict(ref=ref, lib=SYM+'Device.kicad_sym', sym='C', fp=fp, value=val, mfr=mfr, mpn=mpn, pins={'1': a, '2': b}, grp=grp)

NC = None
parts = []
P = parts.append

# ---------------- USB-C input ----------------
P(dict(ref='J1', lib=SYM+'Connector.kicad_sym', sym='USB_C_Receptacle_USB2.0_16P',
       fp='Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal',
       value='USB-C 5V / programming', mfr='GCT', mpn='USB4105-GF-A',
       pins={'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'A4': 'VBUS', 'A9': 'VBUS', 'B4': 'VBUS', 'B9': 'VBUS',
             'A5': 'CC1', 'B5': 'CC2', 'A6': 'USB_DP', 'B6': 'USB_DP', 'A7': 'USB_DN', 'B7': 'USB_DN',
             'A8': NC, 'B8': NC, 'S1': 'GND'}, grp='usb'))
P(R('R1', '5.1k', 'CC1', 'GND', 'RC0603FR-075K1L', grp='usb'))
P(R('R2', '5.1k', 'CC2', 'GND', 'RC0603FR-075K1L', grp='usb'))
P(dict(ref='U3', lib=SYM+'Power_Protection.kicad_sym', sym='SP0503BAHT', fp='Package_TO_SOT_SMD:SOT-143',
       value='SP0503BAHT', mfr='Littelfuse', mpn='SP0503BAHTG',
       pins={'1': 'GND', '2': 'USB_DP', '3': 'USB_DN', '4': 'VBUS'}, grp='usb'))

# ---------------- Power input OR-ing ----------------
P(dict(ref='D1', lib=SYM+'Device.kicad_sym', sym='D_Schottky', fp='Diode_SMD:D_SMA', value='B340A',
       mfr='Diodes Inc', mpn='B340A-13-F', pins={'1': 'VIN_CHG', '2': 'VBUS'}, grp='pwr'))
P(dict(ref='D2', lib=SYM+'Device.kicad_sym', sym='D_Schottky', fp='Diode_SMD:D_SMA', value='B340A',
       mfr='Diodes Inc', mpn='B340A-13-F', pins={'1': 'VIN_CHG', '2': 'SOLAR'}, grp='pwr'))
P(dict(ref='J2', lib=SYM+'Connector_Generic.kicad_sym', sym='Conn_01x02',
       fp='TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-2-3.5-H_1x02_P3.50mm_Horizontal',
       value='SOLAR 5-9V', mfr='Phoenix Contact', mpn='1984617', pins={'1': 'SOLAR', '2': 'GND'}, grp='pwr'))
P(dict(ref='D5', lib=SYM+'Device.kicad_sym', sym='D_TVS', fp='Diode_SMD:D_SMA', value='SMAJ12A',
       mfr='Littelfuse', mpn='SMAJ12A', pins={'1': 'SOLAR', '2': 'GND'}, grp='pwr'))

# ---------------- Charger BQ24074 ----------------
P(dict(ref='U1', lib=SYM+'Battery_Management.kicad_sym', sym='BQ24074RGT',
       fp='Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm', value='BQ24074', mfr='Texas Instruments', mpn='BQ24074RGTR',
       pins={'1': 'TS', '2': 'VBAT', '3': 'VBAT', '4': 'GND', '5': 'GND', '6': 'EN1', '7': 'PGOOD_N', '8': 'GND',
             '9': 'CHG_N', '10': 'VSYS', '11': 'VSYS', '12': 'ILIM', '13': 'VIN_CHG', '14': NC, '15': NC, '16': 'ISET', '17': 'GND'}, grp='chg'))
P(C('C1', '4.7uF 25V', 'VIN_CHG', 'GND', 'CL21A475KAQNNNE', fp='Capacitor_SMD:C_0805_2012Metric', grp='chg'))
P(C('C2', '10uF 10V', 'VSYS', 'GND', 'CL21A106KPFNNNE', fp='Capacitor_SMD:C_0805_2012Metric', grp='chg'))
P(C('C3', '10uF 10V', 'VBAT', 'GND', 'CL21A106KPFNNNE', fp='Capacitor_SMD:C_0805_2012Metric', grp='chg'))
P(R('R3', '1.5k 1%', 'ISET', 'GND', 'RC0603FR-071K5L', grp='chg'))      # ICHG = 890/1500 = 0.59 A
P(R('R4', '1.13k 1%', 'ILIM', 'GND', 'RC0603FR-071K13L', grp='chg'))    # only used if EN2=1/EN1=0
P(dict(ref='TH1', lib=SYM+'Device.kicad_sym', sym='Thermistor_NTC', fp='Resistor_SMD:R_0603_1608Metric',
       value='10k NTC B3380', mfr='Murata', mpn='NCP18XH103F03RB', pins={'1': 'TS', '2': 'GND'}, grp='chg'))
P(R('R24', '10k', 'EN1', 'VSYS', 'RC0603FR-0710KL', grp='chg'))   # EN1=1, EN2=0 -> USB500 (VIN-DPM active)
P(R('R5', '100k', 'PGOOD_N', '+3V3', 'RC0603FR-07100KL', grp='chg'))
P(R('R6', '100k', 'CHG_N', '+3V3', 'RC0603FR-07100KL', grp='chg'))
P(dict(ref='BT1', lib=SYM+'Device.kicad_sym', sym='Battery_Cell', fp='Battery:BatteryHolder_Keystone_1042_1x18650',
       value='18650 holder', mfr='Keystone', mpn='1042', pins={'1': 'VBAT_RAW', '2': 'GND'}, grp='chg'))
# reverse-battery protection: P-FET, drain to cell +, source to VBAT, gate to GND.
# Correct cell: body diode conducts, Vgs = -Vbat turns the channel on (works both ways, so charging still flows).
# Reversed cell: body diode blocked and gate off -> nothing downstream sees negative voltage.
P(dict(ref='Q3', lib=SYM+'Device.kicad_sym', sym='Q_PMOS_GSD', fp='Package_TO_SOT_SMD:SOT-23', value='DMG2305UX',
       mfr='Diodes Inc', mpn='DMG2305UX-7', pins={'1': 'BAT_G', '2': 'VBAT', '3': 'VBAT_RAW'}, grp='chg'))
P(R('R25', '10k', 'BAT_G', 'GND', 'RC0603FR-0710KL', grp='chg'))

# ---------------- 3.3 V LDO ----------------
P(dict(ref='U2', lib=SYM+'Regulator_Linear.kicad_sym', sym='TLV75733PDBV', fp='Package_TO_SOT_SMD:SOT-23-5',
       value='TLV75733P', mfr='Texas Instruments', mpn='TLV75733PDBVR',
       pins={'1': 'VSYS', '2': 'GND', '3': 'VSYS', '4': NC, '5': '+3V3'}, grp='ldo'))
P(C('C4', '10uF 10V', 'VSYS', 'GND', 'CL21A106KPFNNNE', fp='Capacitor_SMD:C_0805_2012Metric', grp='ldo'))
P(C('C5', '22uF 10V', '+3V3', 'GND', 'CL21A226MPQNNNE', fp='Capacitor_SMD:C_0805_2012Metric', grp='ldo'))

# ---------------- ESP32-C6 ----------------
P(dict(ref='U4', lib=ESPSYM, sym='ESP32-C6-WROOM-1', fp='Espressif:ESP32-C6-WROOM-1',
       value='ESP32-C6-WROOM-1-N8', mfr='Espressif', mpn='ESP32-C6-WROOM-1-N8',
       pins={'1': 'GND', '2': '+3V3', '3': 'EN', '4': 'SENS_EN_N', '5': 'OW_MCU', '6': 'SDA', '7': 'SCL',
             '8': 'SOIL1', '9': 'SOIL2', '10': 'GPIO8', '11': 'VALVE_G', '12': 'LED', '13': 'USB_DN', '14': 'USB_DP',
             '15': 'BOOT', '16': 'CHG_N', '17': 'PGOOD_N', '18': 'GPIO20', '19': 'GPIO21', '20': 'GPIO22', '21': 'GPIO23',
             '22': NC, '23': NC, '24': 'RXD', '25': 'TXD', '26': 'SOL_SENSE', '27': 'VBAT_SENSE', '28': 'GND', '29': 'GND'}, grp='mcu'))
P(C('C6', '22uF 10V', '+3V3', 'GND', 'CL21A226MPQNNNE', fp='Capacitor_SMD:C_0805_2012Metric', grp='mcu'))
P(C('C7', '100nF', '+3V3', 'GND', 'CL10B104KB8NNNC', grp='mcu'))
P(R('R7', '10k', 'EN', '+3V3', 'RC0603FR-0710KL', grp='mcu'))
P(C('C8', '1uF', 'EN', 'GND', 'CL10A105KB8NNNC', grp='mcu'))
P(R('R8', '10k', 'BOOT', '+3V3', 'RC0603FR-0710KL', grp='mcu'))
P(R('R9', '10k', 'GPIO8', '+3V3', 'RC0603FR-0710KL', grp='mcu'))
P(dict(ref='SW1', lib=SYM+'Switch.kicad_sym', sym='SW_Push', fp='Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2',
       value='RESET', mfr='C&K', mpn='KMR221GLFS', pins={'1': 'EN', '2': 'GND'}, grp='mcu'))
P(dict(ref='SW2', lib=SYM+'Switch.kicad_sym', sym='SW_Push', fp='Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2',
       value='BOOT', mfr='C&K', mpn='KMR221GLFS', pins={'1': 'BOOT', '2': 'GND'}, grp='mcu'))
P(dict(ref='D4', lib=SYM+'Device.kicad_sym', sym='LED', fp='LED_SMD:LED_0603_1608Metric', value='green',
       mfr='Lite-On', mpn='LTST-C191KGKT', pins={'1': 'LED_K', '2': '+3V3'}, grp='mcu'))
P(R('R10', '1k', 'LED_K', 'LED', 'RC0603FR-071KL', grp='mcu'))   # active-low LED, off at reset
P(dict(ref='J8', lib=SYM+'Connector_Generic.kicad_sym', sym='Conn_01x04', fp='Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',
       value='UART (DNP)', mfr='Amphenol', mpn='DNP', pins={'1': '+3V3', '2': 'TXD', '3': 'RXD', '4': 'GND'}, grp='mcu'))
P(dict(ref='J9', lib=SYM+'Connector_Generic.kicad_sym', sym='Conn_01x06', fp='Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',
       value='EXPANSION (DNP)', mfr='Amphenol', mpn='DNP', pins={'1': '+3V3', '2': 'GPIO20', '3': 'GPIO21', '4': 'GPIO22', '5': 'GPIO23', '6': 'GND'}, grp='mcu'))

# ---------------- Measurement ----------------
P(R('R11', '1M 1%', 'VBAT', 'VBAT_SENSE', 'RC0603FR-071ML', grp='meas'))
P(R('R12', '1M 1%', 'VBAT_SENSE', 'GND', 'RC0603FR-071ML', grp='meas'))
P(C('C9', '100nF', 'VBAT_SENSE', 'GND', 'CL10B104KB8NNNC', grp='meas'))
P(R('R13', '1M 1%', 'SOLAR', 'SOL_SENSE', 'RC0603FR-071ML', grp='meas'))
P(R('R14', '330k 1%', 'SOL_SENSE', 'GND', 'RC0603FR-07330KL', grp='meas'))
P(C('C10', '100nF', 'SOL_SENSE', 'GND', 'CL10B104KB8NNNC', grp='meas'))

# ---------------- Switched sensor rail ----------------
P(dict(ref='Q1', lib=SYM+'Device.kicad_sym', sym='Q_PMOS_GSD', fp='Package_TO_SOT_SMD:SOT-23', value='DMG2305UX',
       mfr='Diodes Inc', mpn='DMG2305UX-7', pins={'1': 'SENS_EN_N', '2': '+3V3', '3': '3V3_SW'}, grp='sens'))
P(R('R15', '100k', 'SENS_EN_N', '+3V3', 'RC0603FR-07100KL', grp='sens'))
P(C('C11', '10uF 10V', '3V3_SW', 'GND', 'CL21A106KPFNNNE', fp='Capacitor_SMD:C_0805_2012Metric', grp='sens'))

# soil probes (capacitive v1.2/v2.0 style: VCC, AOUT, GND)
for i, (J, Rs, Cf) in enumerate([('J3', 'R16', 'C12'), ('J4', 'R17', 'C13')], start=1):
    P(dict(ref=J, lib=SYM+'Connector_Generic.kicad_sym', sym='Conn_01x03', fp='Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical',
           value=f'SOIL{i}', mfr='JST', mpn='B3B-PH-K-S(LF)(SN)', pins={'1': '3V3_SW', '2': f'SOIL{i}_EXT', '3': 'GND'}, grp='sens'))
    P(R(Rs, '1k', f'SOIL{i}_EXT', f'SOIL{i}', 'RC0603FR-071KL', grp='sens'))
    P(C(Cf, '10nF', f'SOIL{i}', 'GND', 'CL10B103KB8NNNC', grp='sens'))

# 1-Wire soil temperature (DS18B20 probe)
P(dict(ref='J5', lib=SYM+'Connector_Generic.kicad_sym', sym='Conn_01x03', fp='Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical',
       value='1-WIRE', mfr='JST', mpn='B3B-PH-K-S(LF)(SN)', pins={'1': '3V3_SW', '2': 'OW', '3': 'GND'}, grp='sens'))
P(R('R18', '4.7k', 'OW', '3V3_SW', 'RC0603FR-074K7L', grp='sens'))
P(R('R19', '100R', 'OW', 'OW_MCU', 'RC0603FR-07100RL', grp='sens'))

# Qwiic / STEMMA QT I2C (SHT4x, VEML7700, SCD4x ...)
P(dict(ref='J6', lib=SYM+'Connector_Generic_MountingPin.kicad_sym', sym='Conn_01x04_MountingPin', fp='Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal',
       value='QWIIC', mfr='JST', mpn='SM04B-SRSS-TB(LF)(SN)', pins={'1': 'GND', '2': '3V3_SW', '3': 'SDA', '4': 'SCL', 'MP': 'GND'}, grp='sens'))
P(R('R20', '4.7k', 'SDA', '3V3_SW', 'RC0603FR-074K7L', grp='sens'))
P(R('R21', '4.7k', 'SCL', '3V3_SW', 'RC0603FR-074K7L', grp='sens'))

# ---------------- Valve / pump low-side driver ----------------
P(dict(ref='J7', lib=SYM+'Connector_Generic.kicad_sym', sym='Conn_01x04',
       fp='TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-4-3.5-H_1x04_P3.50mm_Horizontal',
       value='VALVE 5-24V', mfr='Phoenix Contact', mpn='1984633',
       pins={'1': 'VEXT', '2': 'GND', '3': 'VEXT', '4': 'VALVE_D'}, grp='valve'))
P(dict(ref='Q2', lib=SYM+'Device.kicad_sym', sym='Q_NMOS_GSD', fp='Package_TO_SOT_SMD:SOT-23', value='DMN3404L',
       mfr='Diodes Inc', mpn='DMN3404L-7', pins={'1': 'VALVE_GATE', '2': 'GND', '3': 'VALVE_D'}, grp='valve'))
P(R('R22', '100R', 'VALVE_G', 'VALVE_GATE', 'RC0603FR-07100RL', grp='valve'))
P(R('R23', '100k', 'VALVE_GATE', 'GND', 'RC0603FR-07100KL', grp='valve'))
P(dict(ref='D3', lib=SYM+'Device.kicad_sym', sym='D_Schottky', fp='Diode_SMD:D_SMA', value='B340A',
       mfr='Diodes Inc', mpn='B340A-13-F', pins={'1': 'VEXT', '2': 'VALVE_D'}, grp='valve'))
P(dict(ref='D6', lib=SYM+'Device.kicad_sym', sym='D_TVS', fp='Diode_SMD:D_SMA', value='SMAJ26A',
       mfr='Littelfuse', mpn='SMAJ26A', pins={'1': 'VEXT', '2': 'GND'}, grp='valve'))
P(C('C14', '1uF 50V', 'VEXT', 'GND', 'CL21B105KBFNNNE', fp='Capacitor_SMD:C_0805_2012Metric', grp='valve'))

# ---------------- Mechanical ----------------
for i in range(1, 5):
    P(dict(ref=f'H{i}', lib=SYM+'Mechanical.kicad_sym', sym='MountingHole', fp='MountingHole:MountingHole_3.2mm_M3',
           value='M3', mfr='-', mpn='-', pins={}, grp='mech'))

POWER_NETS = ['GND', '+3V3', 'VSYS', 'VBAT', 'VBUS', 'VIN_CHG', 'SOLAR', 'VEXT', '3V3_SW']

def nets():
    n = {}
    for p in parts:
        for pin, net in p['pins'].items():
            if net: n.setdefault(net, []).append((p['ref'], pin))
    return n

if __name__ == '__main__':
    for k, v in sorted(nets().items()):
        print(f'{k:12s} {len(v):2d} ', ' '.join(f'{r}.{p}' for r, p in v))
    print(len(parts), 'parts')
