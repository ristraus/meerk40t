import threading

import wx

from meerk40t.gui.icons import (
    get_default_icon_size,
    icons8_connected,
    icons8_disconnected,
)
from meerk40t.gui.mwindow import MWindow
from meerk40t.gui.wxutils import (
    StaticBoxSizer,
    TextCtrl,
    dip_size,
    wxButton,
    wxCheckBox,
    wxStaticText,
)
from meerk40t.kernel import signal_listener

_ = wx.GetTranslation

_simple_width = 500
_advanced_width = 855
_default_height = 389


class MoshiControllerPanel(wx.Panel):
    def __init__(self, *args, context=None, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        context.themes.set_window_colors(self)
        self.context = context.device
        self.SetHelpText("moshicontroller")

        self.button_device_connect = wxButton(self, wx.ID_ANY, _("Connection"))
        self.text_connection_status = TextCtrl(
            self, wx.ID_ANY, "", style=wx.TE_READONLY
        )
        self.checkbox_mock_usb = wxCheckBox(
            self, wx.ID_ANY, _("Mock USB Connection Mode")
        )
        self.text_device_index = TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY)
        self.spin_device_index = wx.SpinCtrl(self, wx.ID_ANY, "-1", min=-1)
        self.text_device_address = TextCtrl(
            self, wx.ID_ANY, "", style=wx.TE_READONLY
        )
        self.spin_device_address = wx.SpinCtrl(self, wx.ID_ANY, "-1", min=-1)
        self.text_device_bus = TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY)
        self.spin_device_bus = wx.SpinCtrl(self, wx.ID_ANY, "-1", min=-1)
        self.text_device_version = TextCtrl(
            self, wx.ID_ANY, "", style=wx.TE_READONLY
        )
        self.spin_device_version = wx.SpinCtrl(self, wx.ID_ANY, "-1", min=-1)
        self.text_byte_0 = TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY)
        self.text_byte_1 = TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY)
        self.text_desc = TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY)
        self.text_byte_2 = TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY)
        self.text_byte_3 = TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY)
        self.text_byte_4 = TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY)
        self.text_byte_5 = TextCtrl(self, wx.ID_ANY, "", style=wx.TE_READONLY)
        self.checkbox_show_usb_log = wxCheckBox(self, wx.ID_ANY, _("Show USB Log"))
        self.text_usb_log = TextCtrl(
            self, wx.ID_ANY, "", style=wx.TE_MULTILINE | wx.TE_READONLY
        )

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.on_button_start_usb, self.button_device_connect)
        self.Bind(wx.EVT_CHECKBOX, self.on_check_mock_usb, self.checkbox_mock_usb)
        self.Bind(wx.EVT_SPINCTRL, self.spin_on_device_index, self.spin_device_index)
        self.Bind(wx.EVT_TEXT_ENTER, self.spin_on_device_index, self.spin_device_index)
        self.Bind(
            wx.EVT_SPINCTRL, self.spin_on_device_address, self.spin_device_address
        )
        self.Bind(
            wx.EVT_TEXT_ENTER, self.spin_on_device_address, self.spin_device_address
        )
        self.Bind(wx.EVT_SPINCTRL, self.spin_on_device_bus, self.spin_device_bus)
        self.Bind(wx.EVT_TEXT_ENTER, self.spin_on_device_bus, self.spin_device_bus)
        self.Bind(
            wx.EVT_SPINCTRL, self.spin_on_device_version, self.spin_device_version
        )
        self.Bind(
            wx.EVT_TEXT_ENTER, self.spin_on_device_version, self.spin_device_version
        )
        self.Bind(
            wx.EVT_CHECKBOX, self.on_check_show_usb_log, self.checkbox_show_usb_log
        )
        self.last_control_state = None
        self._buffer = ""
        self._buffer_lock = threading.Lock()
        self.set_widgets()

    def __set_properties(self):
        self.SetFont(
            wx.Font(
                9,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "Segoe UI",
            )
        )
        self.button_device_connect.SetBackgroundColour(wx.Colour(102, 255, 102))
        self.button_device_connect.SetForegroundColour(wx.BLACK)
        self.button_device_connect.SetBitmap(
            icons8_disconnected.GetBitmap(
                use_theme=False, resize=get_default_icon_size(self.context)
            )
        )
        self.button_device_connect.SetFont(
            wx.Font(
                12,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "Segoe UI",
            )
        )
        self.button_device_connect.SetToolTip(
            _("Force connection/disconnection from the device.")
        )
        self.text_connection_status.SetToolTip(_("Connection status"))
        self.checkbox_mock_usb.SetToolTip(
            _(
                "DEBUG. Without a K40 connected continue to process things as if there was one."
            )
        )
        self.text_device_index.SetMinSize(dip_size(self, 55, -1))
        self.spin_device_index.SetMinSize(dip_size(self, 40, -1))
        self.spin_device_index.SetToolTip(
            _(
                "Optional: Distinguish between different lasers using the match criteria below.\n"
                "-1 match anything. 0+ match exactly that value."
            )
        )
        self.text_device_address.SetMinSize(dip_size(self, 55, -1))
        self.spin_device_address.SetMinSize(dip_size(self, 40, -1))
        self.spin_device_address.SetToolTip(
            _(
                "Optional: Distinguish between different lasers using the match criteria below.\n"
                "-1 match anything. 0+ match exactly that value."
            )
        )
        self.text_device_bus.SetMinSize(dip_size(self, 55, -1))
        self.spin_device_bus.SetMinSize(dip_size(self, 40, -1))
        self.spin_device_bus.SetToolTip(
            _(
                "Optional: Distinguish between different lasers using the match criteria below.\n"
                "-1 match anything. 0+ match exactly that value."
            )
        )
        self.text_device_version.SetMinSize(dip_size(self, 55, -1))
        self.spin_device_version.SetMinSize(dip_size(self, 40, -1))
        self.spin_device_version.SetToolTip(
            _(
                "Optional: Distinguish between different lasers using the match criteria below.\n"
                "-1 match anything. 0+ match exactly that value."
            )
        )
        self.text_byte_0.SetMinSize(dip_size(self, 77, -1))
        self.text_byte_1.SetMinSize(dip_size(self, 77, -1))
        self.text_desc.SetMinSize(dip_size(self, 75, 23))
        self.text_desc.SetToolTip(_("The meaning of Byte 1"))
        self.text_byte_2.SetMinSize(dip_size(self, 77, -1))
        self.text_byte_3.SetMinSize(dip_size(self, 77, -1))
        self.text_byte_4.SetMinSize(dip_size(self, 77, -1))
        self.text_byte_5.SetMinSize(dip_size(self, 77, -1))
        self.checkbox_show_usb_log.SetValue(1)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MoshiControllerGui.__do_layout
        sizer_24 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_show_usb_log = wx.BoxSizer(wx.HORIZONTAL)
        packet_count = StaticBoxSizer(self, wx.ID_ANY, _("Packet Info"), wx.VERTICAL)
        byte_data_status = StaticBoxSizer(
            self, wx.ID_ANY, _("Byte Data Status"), wx.HORIZONTAL
        )
        byte5sizer = wx.BoxSizer(wx.VERTICAL)
        byte4sizer = wx.BoxSizer(wx.VERTICAL)
        byte3sizer = wx.BoxSizer(wx.VERTICAL)
        byte2sizer = wx.BoxSizer(wx.VERTICAL)
        byte1sizer = wx.BoxSizer(wx.VERTICAL)
        byte0sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_usb_settings = StaticBoxSizer(
            self, wx.ID_ANY, _("USB Settings"), wx.VERTICAL
        )
        sizer_23 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_12 = StaticBoxSizer(self, wx.ID_ANY, _("Chip Version"), wx.HORIZONTAL)
        sizer_11 = StaticBoxSizer(self, wx.ID_ANY, _("Device Bus:"), wx.HORIZONTAL)
        sizer_10 = StaticBoxSizer(self, wx.ID_ANY, _("Device Address:"), wx.HORIZONTAL)
        sizer_3 = StaticBoxSizer(self, wx.ID_ANY, _("Device Index:"), wx.HORIZONTAL)
        sizer_usb_connect = StaticBoxSizer(
            self, wx.ID_ANY, _("USB Connection"), wx.VERTICAL
        )
        sizer_usb_connect.Add(self.button_device_connect, 0, wx.EXPAND, 0)
        sizer_usb_connect.Add(self.text_connection_status, 0, wx.EXPAND, 0)
        sizer_1.Add(sizer_usb_connect, 0, wx.EXPAND, 0)
        sizer_usb_settings.Add(self.checkbox_mock_usb, 0, 0, 0)
        sizer_3.Add(self.text_device_index, 0, 0, 0)
        sizer_3.Add(self.spin_device_index, 0, 0, 0)
        sizer_23.Add(sizer_3, 0, wx.EXPAND, 0)
        sizer_10.Add(self.text_device_address, 0, 0, 0)
        sizer_10.Add(self.spin_device_address, 0, 0, 0)
        sizer_23.Add(sizer_10, 0, wx.EXPAND, 0)
        sizer_11.Add(self.text_device_bus, 0, 0, 0)
        sizer_11.Add(self.spin_device_bus, 0, 0, 0)
        sizer_23.Add(sizer_11, 0, wx.EXPAND, 0)
        sizer_12.Add(self.text_device_version, 0, 0, 0)
        sizer_12.Add(self.spin_device_version, 0, 0, 0)
        sizer_23.Add(sizer_12, 0, wx.EXPAND, 0)
        sizer_usb_settings.Add(sizer_23, 1, wx.EXPAND, 0)
        sizer_1.Add(sizer_usb_settings, 0, wx.EXPAND, 0)
        byte0sizer.Add(self.text_byte_0, 0, 0, 0)
        label_1 = wxStaticText(self, wx.ID_ANY, _("Byte 0"))
        byte0sizer.Add(label_1, 0, 0, 0)
        byte_data_status.Add(byte0sizer, 1, wx.EXPAND, 0)
        byte1sizer.Add(self.text_byte_1, 0, 0, 0)
        label_2 = wxStaticText(self, wx.ID_ANY, _("Byte 1"))
        byte1sizer.Add(label_2, 0, 0, 0)
        byte1sizer.Add(self.text_desc, 0, 0, 0)
        byte_data_status.Add(byte1sizer, 1, wx.EXPAND, 0)
        byte2sizer.Add(self.text_byte_2, 0, 0, 0)
        label_3 = wxStaticText(self, wx.ID_ANY, _("Byte 2"))
        byte2sizer.Add(label_3, 0, 0, 0)
        byte_data_status.Add(byte2sizer, 1, wx.EXPAND, 0)
        byte3sizer.Add(self.text_byte_3, 0, 0, 0)
        label_4 = wxStaticText(self, wx.ID_ANY, _("Byte 3"))
        byte3sizer.Add(label_4, 0, 0, 0)
        byte_data_status.Add(byte3sizer, 1, wx.EXPAND, 0)
        byte4sizer.Add(self.text_byte_4, 0, 0, 0)
        label_5 = wxStaticText(self, wx.ID_ANY, _("Byte 4"))
        byte4sizer.Add(label_5, 0, 0, 0)
        byte_data_status.Add(byte4sizer, 1, wx.EXPAND, 0)
        byte5sizer.Add(self.text_byte_5, 0, 0, 0)
        label_18 = wxStaticText(self, wx.ID_ANY, _("Byte 5"))
        byte5sizer.Add(label_18, 0, 0, 0)
        byte_data_status.Add(byte5sizer, 1, wx.EXPAND, 0)
        packet_count.Add(byte_data_status, 0, wx.EXPAND, 0)
        sizer_1.Add(packet_count, 0, 0, 0)
        label_6 = wxStaticText(self, wx.ID_ANY, "")
        sizer_show_usb_log.Add(label_6, 10, wx.EXPAND, 0)
        sizer_show_usb_log.Add(self.checkbox_show_usb_log, 0, 0, 0)
        sizer_1.Add(sizer_show_usb_log, 1, wx.EXPAND, 0)
        sizer_24.Add(sizer_1, 1, 0, 0)
        sizer_24.Add(self.text_usb_log, 2, wx.EXPAND, 0)
        self.SetSizer(sizer_24)
        self.Layout()
        # end wxGlade

    def pane_show(self):
        self._channel_watch = f"{self.context.safe_label}/usb"
        self.context.channel(self._channel_watch, buffer_size=500).watch(
            self.update_text
        )
        self.context.listen("pipe;status", self.update_status)
        self.context.listen("pipe;usb_status", self.on_connection_status_change)
        self.context.listen("pipe;state", self.on_connection_state_change)
        self.context.listen("active", self.on_active_change)

    def pane_hide(self):
        self.context.channel(self._channel_watch).unwatch(self.update_text)
        self.context.unlisten("pipe;status", self.update_status)
        self.context.unlisten("pipe;usb_status", self.on_connection_status_change)
        self.context.unlisten("pipe;state", self.on_connection_state_change)
        self.context.unlisten("active", self.on_active_change)

    def on_active_change(self, origin, active):
        # self.Close()
        pass

    def update_text(self, text):
        with self._buffer_lock:
            self._buffer += f"{text}\n"
        self.context.signal("moshi_controller_update")

    @signal_listener("moshi_controller_update")
    def update_text_gui(self, origin, *args):
        with self._buffer_lock:
            buffer = self._buffer
            self._buffer = ""
        self.text_usb_log.AppendText(buffer)

    def set_widgets(self):
        self.context.setting(bool, "show_usb_log", False)
        self.context.setting(int, "usb_index", -1)
        self.context.setting(int, "usb_bus", -1)
        self.context.setting(int, "usb_address", -1)
        self.context.setting(int, "usb_version", -1)
        self.context.setting(bool, "mock", False)

        self.checkbox_show_usb_log.SetValue(self.context.show_usb_log)
        self.checkbox_mock_usb.SetValue(self.context.mock)
        self.spin_device_index.SetValue(self.context.usb_index)
        self.spin_device_bus.SetValue(self.context.usb_bus)
        self.spin_device_address.SetValue(self.context.usb_address)
        self.spin_device_version.SetValue(self.context.usb_version)

        self.on_check_show_usb_log()

    def device_execute(self, control_name):
        def menu_element(event=None):
            self.context.execute(control_name)

        return menu_element

    def update_status(self, origin, status_data, code_string):
        if status_data is not None:
            if isinstance(status_data, int):
                self.text_desc.SetValue(str(status_data))
                self.text_desc.SetValue(code_string)
            else:
                if len(status_data) == 6:
                    self.text_byte_0.SetValue(str(status_data[0]))
                    self.text_byte_1.SetValue(str(status_data[1]))
                    self.text_byte_2.SetValue(str(status_data[2]))
                    self.text_byte_3.SetValue(str(status_data[3]))
                    self.text_byte_4.SetValue(str(status_data[4]))
                    self.text_byte_5.SetValue(str(status_data[5]))
                    self.text_desc.SetValue(code_string)

    def on_connection_status_change(self, origin, status):
        self.text_connection_status.SetValue(str(status))

    def on_connection_state_change(self, origin, state):
        if state == "STATE_CONNECTION_FAILED" or state == "STATE_DRIVER_NO_BACKEND":
            self.button_device_connect.SetBackgroundColour("#dfdf00")
            origin, usb_status = self.context.last_signal("pipe;usb_status")
            if usb_status is not None:
                self.button_device_connect.SetLabel(str(usb_status[0]))
            self.button_device_connect.SetBitmap(
                icons8_disconnected.GetBitmap(
                    use_theme=False, resize=get_default_icon_size(self.context)
                )
            )
            self.button_device_connect.Enable()
        elif state == "STATE_UNINITIALIZED" or state == "STATE_USB_DISCONNECTED":
            self.button_device_connect.SetBackgroundColour("#ffff00")
            self.button_device_connect.SetLabel(_("Connect"))
            self.button_device_connect.SetBitmap(
                icons8_connected.GetBitmap(
                    use_theme=False, resize=get_default_icon_size(self.context)
                )
            )
            self.button_device_connect.Enable()
        elif state == "STATE_USB_SET_DISCONNECTING":
            self.button_device_connect.SetBackgroundColour("#ffff00")
            self.button_device_connect.SetLabel(_("Disconnecting..."))
            self.button_device_connect.SetBitmap(
                icons8_disconnected.GetBitmap(
                    use_theme=False, resize=get_default_icon_size(self.context)
                )
            )
            self.button_device_connect.Disable()
        elif state == "STATE_USB_CONNECTED" or state == "STATE_CONNECTED":
            self.button_device_connect.SetBackgroundColour("#00ff00")
            self.button_device_connect.SetLabel(_("Disconnect"))
            self.button_device_connect.SetBitmap(
                icons8_connected.GetBitmap(
                    use_theme=False, resize=get_default_icon_size(self.context)
                )
            )
            self.button_device_connect.Enable()
        elif state == "STATE_CONNECTING":
            self.button_device_connect.SetBackgroundColour("#ffff00")
            self.button_device_connect.SetLabel(_("Connecting..."))
            self.button_device_connect.SetBitmap(
                icons8_connected.GetBitmap(
                    use_theme=False, resize=get_default_icon_size(self.context)
                )
            )
            self.button_device_connect.Disable()

    def on_button_start_usb(self, event=None):  # wxGlade: Controller.<event_handler>
        origin, state = self.context.last_signal("pipe;state")
        if state is not None and isinstance(state, tuple):
            state = state[0]
        if state in (
            "STATE_USB_DISCONNECTED",
            "STATE_UNINITIALIZED",
            "STATE_CONNECTION_FAILED",
            "STATE_DRIVER_MOCK",
            None,
        ):
            try:
                self.context("usb_connect\n")
            except ConnectionRefusedError:
                dlg = wx.MessageDialog(
                    None,
                    _("Connection Refused. See USB Log for detailed information."),
                    _("Manual Connection"),
                    wx.OK | wx.ICON_WARNING,
                )
                result = dlg.ShowModal()
                dlg.Destroy()
        elif state in ("STATE_CONNECTED", "STATE_USB_CONNECTED"):
            self.context("usb_disconnect\n")

    def spin_on_device_index(self, event=None):
        self.context.usb_index = int(self.spin_device_index.GetValue())

    def spin_on_device_address(self, event=None):
        self.context.usb_address = int(self.spin_device_address.GetValue())

    def spin_on_device_bus(self, event=None):
        self.context.usb_bus = int(self.spin_device_bus.GetValue())

    def spin_on_device_version(self, event=None):
        self.context.usb_version = int(self.spin_device_version.GetValue())

    def on_check_mock_usb(self, event=None):
        self.context.mock = self.checkbox_mock_usb.GetValue()

    def on_button_start_controller(self, event=None):
        print("Event handler 'on_button_start_controller' not implemented!")
        event.Skip()

    def on_check_show_usb_log(self, event=None):
        on = self.checkbox_show_usb_log.GetValue()
        self.text_usb_log.Show(on)
        self.context.show_usb_log = bool(on)
        if on:
            self.GetParent().SetSize((_advanced_width, _default_height))
        else:
            self.GetParent().SetSize((_simple_width, _default_height))


class MoshiControllerGui(MWindow):
    def __init__(self, *args, **kwds):
        super().__init__(_advanced_width, _default_height, *args, **kwds)

        # ==========
        # MENU BAR
        # ==========
        from platform import system as _sys

        if _sys() != "Darwin":
            self.MoshiController_menubar = wx.MenuBar()
            self.create_menu(self.MoshiController_menubar.Append)
            self.SetMenuBar(self.MoshiController_menubar)
        # ==========
        # MENUBAR END
        # ==========

        self.panel = MoshiControllerPanel(self, wx.ID_ANY, context=self.context)
        self.sizer.Add(self.panel, 1, wx.EXPAND, 0)
        self.add_module_delegate(self.panel)
        _icon = wx.NullIcon
        _icon.CopyFromBitmap(icons8_connected.GetBitmap())
        self.SetIcon(_icon)
        self.SetTitle(_("Moshiboard-Controller"))
        self.restore_aspect()

    def create_menu(self, append):
        wxglade_tmp_menu = wx.Menu()
        item = wxglade_tmp_menu.Append(
            wx.ID_ANY, _("Reset USB"), _("Reset USB connection")
        )
        self.Bind(wx.EVT_MENU, self.on_menu_usb_reset, id=item.GetId())
        item = wxglade_tmp_menu.Append(
            wx.ID_ANY, _("Release USB"), _("Release USB resources")
        )
        self.Bind(wx.EVT_MENU, self.on_menu_usb_release, id=item.GetId())
        append(wxglade_tmp_menu, _("Tools"))
        wxglade_tmp_menu = wx.Menu()
        item = wxglade_tmp_menu.Append(wx.ID_ANY, _("Stop"), _("Sends Stop command"))
        self.Bind(wx.EVT_MENU, self.on_menu_stop, id=item.GetId())
        item = wxglade_tmp_menu.Append(
            wx.ID_ANY, _("Free Motor"), _("Sends Free Motor (Unlock Rail) command")
        )
        self.Bind(wx.EVT_MENU, self.on_menu_freemotor, id=item.GetId())
        append(wxglade_tmp_menu, _("Commands"))
        wxglade_tmp_menu = wx.Menu()
        item = wxglade_tmp_menu.Append(
            wx.ID_ANY, _("BufferView"), _("Views the Controller Buffer")
        )
        self.Bind(wx.EVT_MENU, self.on_menu_bufferview, id=item.GetId())
        append(wxglade_tmp_menu, _("Views"))
        self.SetMenuBar(self.MoshiController_menubar)

    def restore(self, *args, **kwargs):
        self.panel.set_widgets()

    def window_open(self):
        self.panel.pane_show()

    def window_close(self):
        self.panel.pane_hide()

    def window_preserve(self):
        return False

    def on_menu_usb_reset(self, event):
        try:
            self.context("usb_reset\n")
        except AttributeError:
            pass

    def on_menu_usb_release(self, event):
        try:
            self.context("usb_release\n")
        except AttributeError:
            pass

    def on_menu_pause(self, event=None):
        try:
            self.context("pause\n")
        except AttributeError:
            pass

    def on_menu_stop(self, event=None):
        try:
            self.context("estop\n")
        except AttributeError:
            pass

    def on_menu_bufferview(self, event=None):
        self.context("window open BufferView\n")

    def on_menu_freemotor(self, event):  # wxGlade: MoshiControllerGui.<event_handler>
        try:
            self.context("unlock\n")
        except AttributeError:
            pass

    @staticmethod
    def submenu():
        # Hint for translation: _("Device-Control"), _("Controller")
        return "Device-Control", "Controller"

    @staticmethod
    def helptext():
        return _("Display the device controller window")
