# coding: utf-8
from ctypes import *
import logging

import math
import enum


log = logging.getLogger(__name__)
AXIS_MAX = 2 ** 15 - 1
AXIS_MIN = -AXIS_MAX
TRIGGER_MAX = 2 ** 7 - 1
TRIGGER_MIN = -TRIGGER_MAX
DPAD_UP = 0x01
DPAD_DOWN = 0x02
DPAD_LEFT = 0x04
DPAD_RIGHT = 0x08
DPAD_OFF = 0
SIGNATURES = {
    "GetNumEmptyBusSlots": [POINTER(c_ubyte)],
    "isControllerExists": [c_uint],
    "isControllerOwned": [c_uint],
    "PlugIn": [c_uint],
    "UnPlug": [c_uint],
    "UnPlugForce": [c_uint],
    "SetBtnA": [c_uint, c_bool],
    "SetBtnB": [c_uint, c_bool],
    "SetBtnX": [c_uint, c_bool],
    "SetBtnY": [c_uint, c_bool],
    "SetBtnStart": [c_uint, c_bool],
    "SetBtnBack": [c_uint, c_bool],
    "SetBtnLT": [c_uint, c_bool],
    "SetBtnRT": [c_uint, c_bool],
    "SetBtnLB": [c_uint, c_bool],
    "SetBtnRB": [c_uint, c_bool],
    "SetBtnGD": [c_uint, c_bool],
    "SetTriggerL": [c_uint, c_byte],
    "SetTriggerR": [c_uint, c_byte],
    "SetAxisX": [c_uint, c_short],
    "SetAxisY": [c_uint, c_short],
    "SetAxisRx": [c_uint, c_short],
    "SetAxisRy": [c_uint, c_short],
    "SetDpadLeft": [c_uint],
    "SetDpadRight": [c_uint],
    "SetDpadUp": [c_uint],
    "SetDpadDown": [c_uint],
    "SetDpadOff": [c_uint],
    "SetDpad": [c_uint, c_int],
    "GetLedNumber": [c_uint, POINTER(c_byte)],
    # "GetVibration": [c_uint, PXINPUT_VIBRATION],
}


class VrtCtrlError(Exception):
    pass


def control_setter(fn):
    def set_control(self, *values):
        if filter(None.__ne__, values):
            return getattr(self._lib, fn)(self._id, *values)
    return set_control


class GamepadState(enum.Flag):
    dpad = enum.auto()
    start = enum.auto()
    back = enum.auto()
    lt = enum.auto()
    rt = enum.auto()
    lb = enum.auto()
    rb = enum.auto()
    a = enum.auto()
    b = enum.auto()
    x = enum.auto()
    y = enum.auto()
    abxy = a | b | x | y
    buttons = abxy | dpad | start | back | lt | rt | lb | rb
    trigger_l = enum.auto()
    trigger_r = enum.auto()
    triggers = trigger_l | trigger_r
    axis_lx = enum.auto()
    axis_ly = enum.auto()
    axis_l = axis_lx | axis_ly
    axis_rx = enum.auto()
    axis_ry = enum.auto()
    axis_r = axis_ry | axis_rx
    axis = axis_l | axis_r
    all = buttons | triggers | axis


class Controller:
    set_dpad_up = control_setter("SetDpadUp")
    set_dpad_down = control_setter("SetDpadDown")
    set_dpad_left = control_setter("SetDpadLeft")
    set_dpad_right = control_setter("SetDpadRight")
    set_dpad_off = control_setter("SetDpadOff")
    set_dpad = control_setter("SetDpad")
    set_btn_a = control_setter("SetBtnA")
    set_btn_b = control_setter("SetBtnB")
    set_btn_x = control_setter("SetBtnX")
    set_btn_y = control_setter("SetBtnY")
    set_btn_start = control_setter("SetBtnStart")
    set_btn_back = control_setter("SetBtnBack")
    set_btn_lt = control_setter("SetBtnLT")
    set_btn_rt = control_setter("SetBtnRT")
    set_btn_lb = control_setter("SetBtnLB")
    set_btn_rb = control_setter("SetBtnRB")
    set_axis_lx = control_setter("SetAxisX")
    set_axis_ly = control_setter("SetAxisY")
    set_axis_rx = control_setter("SetAxisRx")
    set_axis_ry = control_setter("SetAxisRy")
    set_trigger_l = control_setter("SetTriggerL")
    set_trigger_r = control_setter("SetTriggerR")

    def __init__(self, lib, id):
        self._lib = lib
        self._id = id

    def destroy(self, force=False):
        if force:
            return self._lib.UnPlugForce(self._id) == 1
        else:
            return self._lib.UnPlug(self._id) == 1

    def set_ls(self, dir, amount=100):
        try:
            x, y = self.clock_to_xy(int(dir), amount)
        except ValueError:
            x, y = self.compass_to_xy(dir, amount)
        self.set_axis_lx(int(x))
        self.set_axis_ly(int(y))

    def set_rs(self, dir, amount=100):
        try:
            x, y = self.clock_to_xy(int(dir), amount)
        except ValueError:
            x, y = self.compass_to_xy(dir, amount)
        self.set_axis_rx(int(x))
        self.set_axis_ry(int(y))

    def compass_to_xy(self, dir, amount):
        angle_degrees = {
            "N": 0, "E": 90, "S": 180, "W": 270,
            "NE": 45, "NW": 315, "SE": 135, "SW": 225,
            "NNE": 22.5, "ENE": 67.5, "ESE": 112.5, "SSE": 157.5,
            "SSW": 202.5, "WSW": 247.5, "WNW": 292.5, "NNW": 337.5,
        }.get(dir, 0)
        angle_radians = math.radians(-90 + angle_degrees)
        x = math.cos(angle_radians) * AXIS_MAX / 100 * amount
        y = math.sin(angle_radians) * AXIS_MIN / 100 * amount
        return x, y

    def clock_to_xy(self, clock, amount):
        angle_degrees = (360.0 / 12) * (clock % 12)
        angle_radians = math.radians(-90 + angle_degrees)
        x = math.cos(angle_radians) * AXIS_MAX / 100 * amount
        y = math.sin(angle_radians) * AXIS_MIN / 100 * amount
        return x, y

    def set_state(self, state, flags=GamepadState.all):
        if GamepadState.dpad in flags:
            state_dpad = (
                (DPAD_UP if state.dpad_up else 0)
                ^ (DPAD_DOWN if state.dpad_down else 0)
                ^ (DPAD_LEFT if state.dpad_left else 0)
                ^ (DPAD_RIGHT if state.dpad_right else 0)
            )
            self.set_dpad(state_dpad)
        if GamepadState.start in flags: self.set_btn_start(state.start)
        if GamepadState.back in flags: self.set_btn_back(state.back)
        if GamepadState.lt in flags: self.set_btn_lt(state.left_thumb)
        if GamepadState.rt in flags: self.set_btn_rt(state.right_thumb)
        if GamepadState.lb in flags: self.set_btn_lb(state.left_shoulder)
        if GamepadState.rb in flags: self.set_btn_rb(state.right_shoulder)
        if GamepadState.a in flags: self.set_btn_a(state.a)
        if GamepadState.b in flags: self.set_btn_b(state.b)
        if GamepadState.x in flags: self.set_btn_x(state.x)
        if GamepadState.y in flags: self.set_btn_y(state.y)
        if GamepadState.trigger_l in flags: self.set_trigger_l(state.left_trigger)
        if GamepadState.trigger_r in flags: self.set_trigger_r(state.right_trigger)
        if GamepadState.axis_lx in flags: self.set_axis_lx(state.l_thumb_x)
        if GamepadState.axis_ly in flags: self.set_axis_ly(state.l_thumb_y)
        if GamepadState.axis_rx in flags: self.set_axis_rx(state.r_thumb_x)
        if GamepadState.axis_ry in flags: self.set_axis_ry(state.r_thumb_y)
        if GamepadState.axis_ry in flags: self.set_axis_ry(state.r_thumb_y)


class VXInput:
    def __init__(self, dll_path):
        self.dll_path = dll_path
        self._lib = cdll.LoadLibrary(dll_path)
        for k, v in SIGNATURES.items():
            fn = getattr(self._lib, k)
            fn.argtypes = v
            fn.restype = c_bool

    def vbus_exists(self):
        """
        Is virtual USB bus enabled and available

        :return:  bool
        """
        return self._lib.isVBusExists() == 1

    def get_num_empty_bus_slots(self):
        """
        Get number of empty bus slots.

        :return: number of empty bus slots.
        """
        mem = c_ubyte()
        retval = self._lib.GetNumEmptyBusSlots(byref(mem))
        if not retval:
            raise VrtCtrlError(f"GetNumEmptyBusSlots {retval!r}")
        return mem.value

    def controller_exists(self, controller_id):
        return self._lib.isControllerExists(controller_id) == 1

    def is_controller_owned(self, controller_id):
        return self._lib.isControllerOwned(controller_id) == 1

    def controller(self, controller_id, factory=Controller):
        if self.controller_exists(controller_id):
            if self.is_controller_owned(controller_id):
                return factory(self._lib, controller_id)
            else:
                raise VrtCtrlError(
                    f"controller {controller_id} exists, but we don't own it")
        else:
            if self._lib.PlugIn(controller_id):
                return factory(self._lib, controller_id)
            else:
                raise VrtCtrlError(f"failed to create controller {controller_id}")
