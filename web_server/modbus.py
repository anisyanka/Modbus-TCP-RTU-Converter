import pymodbus.client as ModbusClient
from pymodbus import (
    ExceptionResponse,
    Framer,
    ModbusException,
    pymodbus_apply_logging_config,
)
from pymodbus.framer.socket_framer import ModbusSocketFramer

from time import sleep

from helpers import helper_get_my_ip
import config_reader as conf_reader

global last_bat_level
last_bat_level = 0

def modbus_connect_to_tcp_rtu_converter(debug_mode):
    ip = helper_get_my_ip()
    port = conf_reader.get_modbus_tcp_rtu_converter_port()
    timeout = conf_reader.get_modbus_slave_timeout()

    global slave_addr
    slave_addr = conf_reader.get_modbus_slave_id()

    global pwm_duty
    pwm_duty = 0

    print('Modbus TCP/RTU converter is running on {}:{}, slave addr={}, timeout={}s'.format(ip, port, slave_addr, timeout))

    # activate debugging
    if debug_mode == True:
        pymodbus_apply_logging_config("DEBUG")

    global c
    c = ModbusClient.ModbusTcpClient(
                    host=ip,
                    port=port,
                    framer=ModbusSocketFramer)

    c.connect()
    assert c.connected
    if c.connected == True:
        print('Connected to Modbus TCP/RTU client OK')
    else:
        print('Connected to Modbus TCP/RTU client FAILED')


def modbus_get_battery_level():
    global c
    global last_bat_level

    try:
        response = c.read_holding_registers(17, 1, slave=slave_addr)
    except ModbusException as exc:
        print(f"[ERR](Read battery level) --> Received ModbusException({exc}) from library")
        c.close()
        return last_bat_level

    if response.isError():
        print(f"[ERR](Read battery level) --> Received Modbus library error({response})")
        c.close()
        return last_bat_level
    elif isinstance(response, ExceptionResponse): # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
        print(f"[ERR](Read battery level) --> Received Modbus library exception ({response})")
        c.close()
        return last_bat_level
    else:
        last_bat_level = response.registers

    return last_bat_level

def modbus_focus_motor_control(level):
    global c

    if level == "upper":
        c.write_register(12, 1, slave=slave_addr)
    elif level == "lower":
        c.write_register(12, 65535, slave=slave_addr)
    else:
        print("[ERR] wrong cmd")

def modbus_light_control(level):
    global c
    global pwm_duty

    max_pwm_duty = conf_reader.get_led_pwm_max_power()

    if level == "upper":
        pwm_duty += 1
        if pwm_duty > max_pwm_duty:
            print("Led MAX power already ENABLED")
            pwm_duty = max_pwm_duty
        c.write_register(14, pwm_duty, slave=slave_addr)
    elif level == "lower":
        if pwm_duty > 0:
            pwm_duty -= 1
        else:
            print("Led MIN power already ENABLED")
        c.write_register(14, pwm_duty, slave=slave_addr)
    else:
        print("[ERR] wrong cmd")

def modbus_main_motors_control(position):
    global c

    # Swap up and left AND right and down?
    swap = conf_reader.get_swap()

    # 2  - up\down addr
    # 4  - left\right
    # 12 - focus

    # Swap INdependent functions
    if position == "STOP":
        c.write_register(33, 1, slave=slave_addr)
    else:
        # Swap dependent functions
        if swap == "no":
            if position == "up":
                c.write_register(2, 1, slave=slave_addr)
            elif position == "down":
                c.write_register(2, 65535, slave=slave_addr)
            elif position == "right":
                c.write_register(4, 1, slave=slave_addr)
            elif position == "left":
                c.write_register(4, 65535, slave=slave_addr)
            elif position == "HOME" or position == "WORK":
                if position == "WORK":
                    updown_steps = conf_reader.get_work_btn_updown_stepper_default_steps()
                    leftright_steps = conf_reader.get_work_btn_leftright_stepper_default_steps()
                    focus_steps = conf_reader.get_work_btn_focus_stepper_default_steps()
                elif position == "HOME":
                    updown_steps = conf_reader.get_home_btn_updown_stepper_default_steps()
                    leftright_steps = conf_reader.get_home_btn_leftright_stepper_default_steps()
                    focus_steps = conf_reader.get_home_btn_focus_stepper_default_steps()

                print()
                print("Steps from config:")
                print("updown_steps={}".format(updown_steps))
                print("leftright_steps={}".format(leftright_steps))
                print("focus_steps={}".format(focus_steps))
                print()

                if updown_steps != 0:
                    if updown_steps < 0:
                        updown_steps &= 0xffff
                    c.write_register(2, updown_steps, slave=slave_addr)
                    sleep(0.02)

                if leftright_steps != 0:
                    if leftright_steps < 0:
                        leftright_steps &= 0xffff
                    c.write_register(4, leftright_steps, slave=slave_addr)
                    sleep(0.02)

                if focus_steps != 0:
                    if focus_steps < 0:
                        focus_steps &= 0xffff
                    c.write_register(12, focus_steps, slave=slave_addr)
            else:
                print("[ERR] Unknown command for motors")
        elif swap == "yes":
            if position == "up":
                c.write_register(4, 65535, slave=slave_addr)
            elif position == "down":
                c.write_register(4, 1, slave=slave_addr)
            elif position == "right":
                c.write_register(2, 65535, slave=slave_addr)
            elif position == "left":
                c.write_register(2, 1, slave=slave_addr)
            elif position == "HOME" or position == "WORK":
                if position == "WORK":
                    updown_steps = conf_reader.get_work_btn_updown_stepper_default_steps()
                    leftright_steps = conf_reader.get_work_btn_leftright_stepper_default_steps()
                    focus_steps = conf_reader.get_work_btn_focus_stepper_default_steps()
                elif position == "HOME":
                    updown_steps = conf_reader.get_home_btn_updown_stepper_default_steps()
                    leftright_steps = conf_reader.get_home_btn_leftright_stepper_default_steps()
                    focus_steps = conf_reader.get_home_btn_focus_stepper_default_steps()

                print()
                print("Steps from config:")
                print("updown_steps={}".format(updown_steps))
                print("leftright_steps={}".format(leftright_steps))
                print("focus_steps={}".format(focus_steps))
                print()

                if updown_steps != 0:
                    if updown_steps < 0:
                        updown_steps &= 0xffff
                    c.write_register(4, updown_steps, slave=slave_addr)
                    sleep(0.02)

                if leftright_steps != 0:
                    if leftright_steps < 0:
                        leftright_steps &= 0xffff
                    c.write_register(2, leftright_steps, slave=slave_addr)
                    sleep(0.02)

                if focus_steps != 0:
                    if focus_steps < 0:
                        focus_steps &= 0xffff
                    c.write_register(12, focus_steps, slave=slave_addr)
            else:
                print("[ERR] Unknown command for motors")
        else:
            print("[ERR] Unknown swap value in config file")

    sleep(0.02)
