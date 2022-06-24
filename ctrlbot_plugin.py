# -*- coding: utf-8 -*-

import irc3
from irc3.compat import asyncio
from irc3.plugins.command import command

from vxinputlib import VXInput, TRIGGER_MAX, GamepadState
from xinputlib import XInput


POLLING_RATE = 1 / 100


async def ctrl_poll(loop, ctrl, vctrl):
    while True:
        ctrl.update()
        mask = GamepadState.axis_l
        ctrl_state = ctrl.state
        if ctrl_state.back:
            mask = GamepadState.all
        loop.call_later(1,
                        vctrl.set_state,
                        ctrl_state,
                        mask)
        await asyncio.sleep(POLLING_RATE)


async def help_reminder(bot, channel):
    while True:
        bot.privmsg(channel,
                    "Type !help to see available commands. "
                     "Type !help <command> to see help for specific command.")
        await asyncio.sleep(60 * 5)


@irc3.plugin
class Plugin:
    requires = [
        "irc3.plugins.core"
    ]

    def __init__(self, bot, loop=None, lib=None, ctrl=None, vctrl=None):
        self.bot = bot
        self.log = bot.log
        self.loop = loop if loop else asyncio.get_event_loop()
        self.config = bot.config.get(__name__, {})
        self.dll_path = self.config["dll_path"]
        self.vxinput = lib if lib else VXInput(self.dll_path)
        self.xinput = XInput("xinput9_1_0")
        self.ctrl = ctrl
        self.vctrl = vctrl
        self.button_delay = 200 / 1000

    @classmethod
    def reload(cls, old):
        return cls(old.bot, old.loop, old.lib, old.ctrl, old.vctrl)

    @irc3.event(irc3.rfc.JOIN)
    def on_joined(self, mask, channel, **kw):
        if mask.nick == self.bot.nick:
            asyncio.ensure_future(help_reminder(self.bot, channel))
            self.log.info("bot has joined channel: %s", channel)
            self.log.info("available controllers: %s", self.vxinput.get_num_empty_bus_slots())
            try:
                if self.ctrl is None:
                    self.ctrl = self.xinput.enumerate_devices()[0]
                if self.vctrl is None:
                    self.vctrl = self.vxinput.controller(2)

                asyncio.ensure_future(
                    ctrl_poll(self.loop, self.ctrl, self.vctrl)
                )
                self.log.info("initialized controller")
            except Exception:
                self.log.exception("failed to initialize controller")

    @command(permission='view')
    def aim(self, mask, target, args):
        """Set aiming direction in clock (1-12) or compass (N, E, S, W, NE, SE, SW, NW).
            %%aim <dir>
        """
        args.pop("aim")
        dir_ = args.get("<dir>")
        self.vctrl.set_rs(dir_, 100)

    def _duration(self, args):
        try:
            duration = int(args["<duration>"])
        except (ValueError, TypeError):
            duration = 200
        return max(0, min(10000, duration)) / 1000

    @command(permission='view')
    def fire(self, mask, target, args):
        """Fire guns, L for left, R for right, LR for left and right.
            %%fire (L|R|LR) [<duration>]
        """
        duration = self._duration(args)
        if "L" in args["L"]:
            self.vctrl.set_trigger_l(TRIGGER_MAX)
            self.loop.call_later(duration, self.vctrl.set_trigger_l, 0)
        if "R" in args["L"]:
            self.vctrl.set_trigger_r(TRIGGER_MAX)
            self.loop.call_later(duration, self.vctrl.set_trigger_r, 0)

    @command(permission='view')
    def button(self, mask, target, args):
        """Trigger button A, B, X, Y or combinations.
            %%button <buttons> [<duration>]
        """
        duration = self._duration(args)
        buttons = args["<buttons>"].lower()
        if "a" in buttons:
            self.vctrl.set_btn_a(True)
            self.loop.call_later(duration, self.vctrl.set_btn_a, False)
        if "b" in buttons:
            self.vctrl.set_btn_b(True)
            self.loop.call_later(duration, self.vctrl.set_btn_b, False)
        if "x" in buttons:
            self.vctrl.set_btn_x(True)
            self.loop.call_later(duration, self.vctrl.set_btn_x, False)
        if "y" in buttons:
            self.vctrl.set_btn_y(True)
            self.loop.call_later(duration, self.vctrl.set_btn_y, False)

    @command(permission='view')
    async def dpad(self, mask, target, args):
        """Trigger DPAD up, down, left, right.
            %%dpad <dir> [<count>]
        """
        try:
            count = int(args["<count>"])
        except (TypeError, ValueError):
            count = 1
        count = min(4, max(1, count))
        dpad_dir = args["<dir>"].lower()
        if "up" in dpad_dir:
            fn = self.vctrl.set_dpad_up
        elif "down" in dpad_dir:
            fn = self.vctrl.set_dpad_down
        elif "left" in dpad_dir:
            fn = self.vctrl.set_dpad_left
        elif "right" in dpad_dir:
            fn = self.vctrl.set_dpad_right
        else:
            fn = None
        if fn is not None:
            for i in range(count):
                fn(True)
                await asyncio.sleep(self.button_delay)
                self.vctrl.set_dpad_off()
                await asyncio.sleep(self.button_delay)
