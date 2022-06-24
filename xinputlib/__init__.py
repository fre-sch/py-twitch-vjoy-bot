# coding: utf-8

import ctypes
from collections import namedtuple, OrderedDict
from enum import IntFlag
from pprint import pprint

ERROR_DEVICE_NOT_CONNECTED = 1167
ERROR_SUCCESS = 0


class Buttons(IntFlag):
    dpad_up = 0x0001
    dpad_down = 0x0002
    dpad_left = 0x0004
    dpad_right = 0x0008
    start = 0x0010
    back = 0x0020
    left_thumb = 0x0040
    right_thumb = 0x0080
    left_shoulder = 0x0100
    right_shoulder = 0x0200
    a = 0x1000
    b = 0x2000
    x = 0x4000
    y = 0x8000

    @classmethod
    def asdict(cls, value):
        value = cls(value)
        return {flag._name_: flag in value for flag in cls}


def get_bit_values(number, size=32):
    """
    Get bit values as a list for a given number
    >>> get_bit_values(1) == [0]*31 + [1]
    True
    >>> get_bit_values(0xDEADBEEF)
    [1L, 1L, 0L, 1L, 1L, 1L, 1L, 0L, 1L, 0L, 1L, 0L, 1L, 1L, 0L, 1L, 1L, 0L,
    1L, 1L, 1L, 1L, 1L, 0L, 1L, 1L, 1L, 0L, 1L, 1L, 1L, 1L]
    You may override the default word size of 32-bits to match your actual
    application.
    >>> get_bit_values(0x3, 2)
    [1L, 1L]
    >>> get_bit_values(0x3, 4)
    [0L, 0L, 1L, 1L]
    """
    return list(map(int, f"{number:b}".rjust(size, "0")))


class XInputGamepadStruct(ctypes.Structure):
    """
    See http://msdn.microsoft.com/en-gb/library/windows/desktop/ee417001%28v=vs.85%29.aspx
    """
    _fields_ = [
        ('buttons', ctypes.c_ushort),  # wButtons
        ('left_trigger', ctypes.c_ubyte),  # bLeftTrigger
        ('right_trigger', ctypes.c_ubyte),  # bLeftTrigger
        ('l_thumb_x', ctypes.c_short),  # sThumbLX
        ('l_thumb_y', ctypes.c_short),  # sThumbLY
        ('r_thumb_x', ctypes.c_short),  # sThumbRx
        ('r_thumb_y', ctypes.c_short),  # sThumbRy
    ]


class XInputStateStruct(ctypes.Structure):
    """
    See http://msdn.microsoft.com/en-gb/library/windows/desktop/ee417001%28v=vs.85%29.aspx
    """
    _fields_ = [
        ('packet_number', ctypes.c_ulong),
        ('gamepad', XInputGamepadStruct),
    ]


class XInputVibrationStruct(ctypes.Structure):
    _fields_ = [
        ("wLeftMotorSpeed", ctypes.c_ushort),
        ("wRightMotorSpeed", ctypes.c_ushort)
    ]


GamepadState = namedtuple("GamepadState", [
    "dpad_up", "dpad_down", "dpad_left", "dpad_right",
    "start", "back",
    "left_thumb", "right_thumb",
    "left_shoulder", "right_shoulder",
    "a", "b", "x", "y",
    "left_trigger", "right_trigger",
    "l_thumb_x", "l_thumb_y",
    "r_thumb_x", "r_thumb_y",
])


class XInputGamepad:
    def __init__(self, lib, device_number, normalize_axes=True):
        self._lib = lib
        self.device_number = device_number
        self._last_state = self._current_state = \
            self._lib.get_state(self.device_number)
        self.received_packets = 0
        self.missed_packets = 0
        if normalize_axes:
            self.translate = self.translate_using_data_size
        else:
            self.translate = self.translate_identity

    def update(self):
        self._last_state = self._current_state
        self._current_state = self._lib.get_state(self.device_number)

    def translate_using_data_size(self, value, data_size):
        # normalizes analog data to [0,1] for unsigned data
        #  and [-0.5,0.5] for signed data
        data_bits = 8 * data_size
        return float(value) / (2 ** data_bits - 1)

    def translate_identity(self, value, data_size=None):
        return value

    def is_connected(self):
        return self._last_state is not None

    def set_vibration(self, left, right):
        self._lib.set_vibration(self.device_number, left, right)

    @property
    def state(self):
        return GamepadState(
            left_trigger=self._current_state.gamepad.left_trigger,
            right_trigger=self._current_state.gamepad.right_trigger,
            l_thumb_x=self._current_state.gamepad.l_thumb_x,
            l_thumb_y=self._current_state.gamepad.l_thumb_y,
            r_thumb_x=self._current_state.gamepad.r_thumb_x,
            r_thumb_y=self._current_state.gamepad.r_thumb_y,
            **Buttons.asdict(self._current_state.gamepad.buttons)
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({self.device_number})"


class XInput:
    """
    Win 8 version
        xinput9_1_0

    32-bit Vista SP1
        xinput1_2,
        xinput1_1

    64-bit Vista SP1
        xinput1_3

    """

    max_devices = 4

    def __init__(self, dllname, gamepad_factory=XInputGamepad):
        self.gamepad_factory = gamepad_factory
        self.dllname = dllname
        self.dll = getattr(ctypes.windll, dllname)

        XInputSetState = self.dll.XInputSetState
        XInputSetState.argtypes = [ctypes.c_uint,
                                   ctypes.POINTER(XInputVibrationStruct)]
        XInputSetState.restype = ctypes.c_uint

    def enumerate_devices(self):
        """
        Returns the devices that are connected
        """
        return [
            device
            for device in map(self.get_device, range(self.max_devices))
            if device.is_connected()
        ]

    def get_device(self, device_number):
        return self.gamepad_factory(self, device_number)

    def get_state(self, device_number):
        state = XInputStateStruct()
        res = self.dll.XInputGetState(device_number, ctypes.byref(state))

        if res == ERROR_SUCCESS:
            return state

        if res != ERROR_DEVICE_NOT_CONNECTED:
            raise RuntimeError(
                "Unknown error %d attempting to get state of device %d" % (
                res, device_number))

        return None

    def set_vibration(self, device_number, left=0, right=0):
        """
        :param int device_number:
        :param float left: value between 0.0 and 1.0
        :param float right: value between 0.0 and 1.0
        :return:
        """
        vibration = XInputVibrationStruct(
            int(left * 65535),
            int(right * 65535)
        )
        return self.dll.XInputSetState(device_number, ctypes.byref(vibration))
