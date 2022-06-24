# coding: utf-8
import os
import cmd
from vxinputlib import VXInput


class ControllerCmd(cmd.Cmd):
    prompt = "> "

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def do_btn_a(self, args):
        enabled = args == "1"
        self.controller.set_btn_a(enabled)

    def do_btn_lt(self, args):
        enabled = args == "1"
        self.controller.set_btn_lt(enabled)

    def do_axis(self, args):
        args = args.split()
        dir = args[0]
        amount = int(args[1])
        self.controller.set_ls(dir, amount)

    def do_quit(self, args):
        return True


DLLPATH = r"libs\x32\vXboxInterface.dll"
lib = VXInput(DLLPATH)
print("vbus_exists", lib.vbus_exists())
print("get_num_empty_bus_slots", lib.get_num_empty_bus_slots())
ctrl = lib.controller(2)
ControllerCmd(ctrl).cmdloop()
ctrl.destroy()
