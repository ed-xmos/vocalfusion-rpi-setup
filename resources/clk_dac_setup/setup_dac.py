#!usr/bin/python
# Copyright (c) 2018-2019, XMOS Ltd, All rights reserved

#run this on the raspberry pi to program the DAC

import smbus
import time
import sys

def setup_dac(ppm):
    samFreq = 48000
    bus = smbus.SMBus(1)
    
    # set DAC_RST_N to 0 on the I2C expander (address 0x20)
    bus.write_byte_data(0x20, 6, 0xff)
    time.sleep(0.1)
    bus.write_byte_data(0x20, 6, 0x7f)
    time.sleep(0.1)


    DEVICE_ADDRESS = 0x18
    # TLV320DAC3101 Register Addresses
    # Page 0
    DAC3101_PAGE_CTRL    = 0x00 # Register 0 - Page Control
    DAC3101_SW_RST        = 0x01 # Register 1 - Software Reset
    DAC3101_CLK_GEN_MUX  =  0x04 # Register 4 - Clock-Gen Muxing
    DAC3101_PLL_P_R      =  0x05 # Register 5 - PLL P and R Values
    DAC3101_PLL_J        =  0x06 # Register 6 - PLL J Value
    DAC3101_PLL_D_MSB    =  0x07 # Register 7 - PLL D Value (MSB)
    DAC3101_PLL_D_LSB    =  0x08 # Register 8 - PLL D Value (LSB)
    DAC3101_NDAC_VAL     =  0x0B # Register 11 - NDAC Divider Value
    DAC3101_MDAC_VAL     =  0x0C # Register 12 - MDAC Divider Value
    DAC3101_DOSR_VAL_LSB =  0x0E # Register 14 - DOSR Divider Value (LS Byte)
    DAC3101_CLKOUT_MUX   =  0x19 # Register 25 - CLKOUT MUX
    DAC3101_CLKOUT_M_VAL =  0x1A # Register 26 - CLKOUT M_VAL
    DAC3101_CODEC_IF     =  0x1B # Register 27 - CODEC Interface Control
    DAC3101_DAC_DAT_PATH =  0x3F # Register 63 - DAC Data Path Setup
    DAC3101_DAC_VOL      =  0x40 # Register 64 - DAC Vol Control
    DAC3101_DACL_VOL_D   =  0x41 # Register 65 - DAC Left Digital Vol Control
    DAC3101_DACR_VOL_D   =  0x42 # Register 66 - DAC Right Digital Vol Control
    DAC3101_GPIO1_IO     =  0x33 # Register 51 - GPIO1 In/Out Pin Control
    # Page 1
    DAC3101_HP_DRVR      =  0x1F # Register 31 - Headphone Drivers
    DAC3101_SPK_AMP      =  0x20 # Register 32 - Class-D Speaker Amp
    DAC3101_HP_DEPOP     =  0x21 # Register 33 - Headphone Driver De-pop
    DAC3101_DAC_OP_MIX   =  0x23 # Register 35 - DAC_L and DAC_R Output Mixer Routing
    DAC3101_HPL_VOL_A    =  0x24 # Register 36 - Analog Volume to HPL
    DAC3101_HPR_VOL_A    =  0x25 # Register 37 - Analog Volume to HPR
    DAC3101_SPKL_VOL_A   =  0x26 # Register 38 - Analog Volume to Left Speaker
    DAC3101_SPKR_VOL_A   =  0x27 # Register 39 - Analog Volume to Right Speaker
    DAC3101_HPL_DRVR     =  0x28 # Register 40 - Headphone Left Driver
    DAC3101_HPR_DRVR     =  0x29 # Register 41 - Headphone Right Driver
    DAC3101_SPKL_DRVR    =  0x2A # Register 42 - Left Class-D Speaker Driver
    DAC3101_SPKR_DRVR    =  0x2B # Register 43 - Right Class-D Speaker Driver

    # Wait for 1ms
    time.sleep(1)
    # Set register page to 0
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_PAGE_CTRL, 0x00) 
    # Initiate SW reset (PLL is powered off as part of reset)
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_SW_RST, 0x01) 

    # so I've got 24.576MHz in to PLL, I want 24.576MHz +- xxxPPM out

    # I will always be using fractional-N (D != 0) so we must set R = 1
    # PLL_CLKIN/P must be between 10 and 20MHz so we must set P = 2

    # PLL_CLK = CLKIN * ((RxJ.D)/P)
    # We know R = 1, P = 2.
    # PLL_CLK = CLKIN * (J.D / 2)
                
    # For 24.576MHz:
    # J = 8
    # D = 0
    # So PLL_CLK = 24.576 * (8.0/2) = 24.476 x 4 = 98.304MHz
    # Then:
    # NDAC = 4
    # MDAC = 4 (Don't care)
    # DOSR = 128 (Don't care)
    # So:
    # DAC_CLK = PLL_CLK / 4 = 24.576MHz.
    # DAC_MOD_CLK = DAC_CLK / 4 = 6.144MHz.
    # DAC_FS = DAC_MOD_CLK / 128 = 48kHz.

    ratio = ppm / 1000000.0
    pll_mul = 8.0 * (1.0 + ratio)
    J = int(pll_mul)
    D = int((pll_mul - float(J)) * 10000)

    print("J:", J, "D:", D)

    # Set PLL J Value to 8
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_PLL_J, 8);
    # Set PLL D to 0 ...
    # Set PLL D MSB Value to 0x00
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_PLL_D_MSB, D >> 8);
    # Set PLL D LSB Value to 0x00
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_PLL_D_LSB, D & 0xff);

    time.sleep(0.001);
    
    # Set PLL_CLKIN = MCLK (device pin), CODEC_CLKIN = PLL_CLK (generated on-chip)
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_CLK_GEN_MUX, (0 << 2) | 3);
    
    # Set PLL P and R values and power up.
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_PLL_P_R, 0x80 | (2 << 4) | (1) );
        

    # Set NDAC clock divider to 4 and power up.
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_NDAC_VAL, 0x84)
    # Set MDAC clock divider to 4 and power up.
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_MDAC_VAL, 0x84)
    # Set OSR clock divider to 128.
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_DOSR_VAL_LSB, 0x80)

    # Set CLKOUT Mux to DAC_CLK
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_CLKOUT_MUX, 0x4)
    # Set CLKOUT M divider to 1 and power up.
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_CLKOUT_M_VAL, 0x81)
    # Set GPIO1 output to come from CLKOUT output.
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_GPIO1_IO, 0x10)

    # Set CODEC interface mode: I2S, 24 bit, slave mode (BCLK, WCLK both inputs).
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_CODEC_IF, 0x20)
    # Set register page to 1
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_PAGE_CTRL, 0x01)
    # Program common-mode voltage to mid scale 1.65V.
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_HP_DRVR, 0x14)
    # Program headphone-specific depop settings.
    # De-pop, Power on = 800 ms, Step time = 4 ms
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_HP_DEPOP, 0x4E)
    # Program routing of DAC output to the output amplifier (headphone/lineout or speaker)
    # LDAC routed to left channel mixer amp, RDAC routed to right channel mixer amp
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_DAC_OP_MIX, 0x44)
    # Unmute and set gain of output driver
    # Unmute HPL, set gain = 0 db
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_HPL_DRVR, 0x06)
    # Unmute HPR, set gain = 0 dB
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_HPR_DRVR, 0x06)
    # Unmute Left Class-D, set gain = 12 dB
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_SPKL_DRVR, 0x0C)
    # Unmute Right Class-D, set gain = 12 dB
    # Unmute Right Class-D, set gain = 12 dB
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_SPKR_DRVR, 0x0C)
    # Power up output drivers
    # HPL and HPR powered up
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_HP_DRVR, 0xD4)
    # Power-up L and R Class-D drivers
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_SPK_AMP, 0xC6)
    # Enable HPL output analog volume, set = -9 dB
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_HPL_VOL_A, 0x92)
    # Enable HPR output analog volume, set = -9 dB
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_HPR_VOL_A, 0x92)
    # Enable Left Class-D output analog volume, set = -9 dB
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_SPKL_VOL_A, 0x92)
    # Enable Right Class-D output analog volume, set = -9 dB
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_SPKR_VOL_A, 0x92)

    time.sleep(0.1);

    # Power up DAC
    # Set register page to 0
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_PAGE_CTRL, 0x00)
    # Power up DAC channels and set digital gain
    # Powerup DAC left and right channels (soft step enabled)
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_DAC_DAT_PATH, 0xD4)
    # DAC Left gain = 0dB
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_DACL_VOL_D, 0x00)
    # DAC Right gain = 0dB
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_DACR_VOL_D, 0x00)
    # Unmute digital volume control
    # Unmute DAC left and right channels
    bus.write_byte_data(DEVICE_ADDRESS, DAC3101_DAC_VOL, 0x00)

if __name__ == "__main__":
    setup_dac(float(sys.argv[1]))
