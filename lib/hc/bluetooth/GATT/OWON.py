
import time

import hc.bluetooth.GATT as GATT


class TypeMeasurement(object):
    @classmethod
    def raw2value(cls, raw):
        obj = MeasurementBase(raw)
        # obj.debug = True
        return obj


gatt_list = {
    '0000fff0-0000-1000-8000-00805f9b34fb': {'func': GATT.TypeHexDump,
        'desc': 'UUID', 'category': 'strings',
    },
    '0000fff1-0000-1000-8000-00805f9b34fb': {'func': GATT.TypeUtf8s,
        # "ABCDEFGHIJKLMN"
        'desc': 'unknown1', 'category': 'strings',
    },
    '0000fff2-0000-1000-8000-00805f9b34fb': {'func': GATT.TypeHexDump,
        # 23,ff,00,01,02,00
        'desc': 'unknown2', 'category': 'strings',
    },
    # '0000fff3-0000-1000-8000-00805f9b34fb': {'func': GATT.TypeHexDump,
    #     # Write uint8 button_nr, uint8 times
    #     'desc': 'press_button', 'category': 'misc',
    # },
    '0000fff4-0000-1000-8000-00805f9b34fb': {'func': TypeMeasurement,
        # Notify only
        'desc': 'measurement', 'category': 'normal',
    },
    # '0000fff5-0000-1000-8000-00805f9b34fb': {'func': GATT.TypeHexDump,
    #     # Write
    #     'desc': 'unknown5', 'category': 'strings',
    # },
}

GATT.Characteristic.register(gatt_list)


class MeasurementBase:

    def __init__(self, raw):
        self.raw = raw
        self.timestamp = None
        self.debug = False

        self.mode = (raw[0] & 0xc0) >> 6 | (raw[1] & 3) << 2
        if self.mode > 12:
            raise ValueError(
                "Unknown mode value {} in raw data".format(self.mode))

        # scale1 is for the SI suffix
        self.raw_scale1 = (raw[0] & 0x38) >> 3
        if self.raw_scale1 == 0 or self.raw_scale1 == 7:
            raise ValueError(
                "Unknown scale value {} in raw data".format(self.raw_scale1))

        # scale2 is for where the decimal point is
        self.raw_scale2 = raw[0] & 7
        if self.raw_scale2 in [4, 5, 6]:
            raise ValueError(
                "Unknown decimal place {} in raw data".format(self.raw_scale2))

        if raw[1] & 0xfc != 0xf0:
            raise ValueError("Unknwon mode bits set in raw data")

        flags = raw[2]
        self.hold       = (flags & 1) != 0
        self.delta      = (flags & 2) != 0
        self.AutoRange  = (flags & 4) != 0
        self.BatteryLow = (flags & 8) != 0
        self.Min        = (flags & 0x10) != 0
        self.Max        = (flags & 0x20) != 0
        if (flags & 0xc0) != 0:
            raise ValueError("Unknown flags bit set in raw data")

        if raw[3] != 0:
            raise ValueError("Unknown byte set in raw data")

        negative = (raw[5] & 0x80) != 0
        if (raw[5] & 0x40) != 0:
            raise ValueError("Unknown value bit set in raw data")

        self.raw_value = GATT.TypeUint16.raw2value([raw[4], raw[5] & 0x3f])
        if negative:
            self.raw_value = -self.raw_value

        # xx xx xx xx xx 3F High bits of value
        # xx xx xx xx xx 40 always 0
        # xx xx xx xx xx 80 Negative
        # xx xx xx xx FF xx Low bits of value
        # xx xx xx FF xx xx always 0
        # xx xx 01 xx xx xx Hold
        # xx xx 02 xx xx xx Delta
        # xx xx 04 xx xx xx Auto
        # xx xx 08 xx xx xx Batt-Low
        # xx xx 10 xx xx xx MIN
        # xx xx 20 xx xx xx MAX
        # xx xx C0 xx xx xx always 0
        # xx F0 xx xx xx xx always F
        # xx 0C xx xx xx xx always 0
        # x7 xx xx xx xx xx Decimal point pos (7==OL, 4-6==?)
        # 38 xx xx xx xx xx Scale flag (see table)
        # C0 03 xx xx xx xx Mode flag (swap hi/lo extract 4 bits) (see table)

        # Scale:
        # 001 nano
        # 010 micro
        # 011 milli
        # 100 No scale flag
        # 101 kilo

        # Mode:
        # 0000 Volts DC
        # 0001 Volts AC
        # 0010 Amp DC
        # 0011 Amp AC
        # 0100 Ohms
        # 0101 Farad
        # 0110 Hz
        # 0111 Percentage
        # 1000 Centigrade
        # 1001 Farenheight
        # 1010 Diode Volts
        # 1011 Ohm Beep
        # 1100 hFE

    def __str__(self):
        s = ''
        s += str(self.raw_value * self.decimal_adjust())
        suffix = self.si_suffix()
        if suffix:
            s += ' '+suffix
        # do something better with the raw_value
        # do something better with the scale
        # s+=unit

        s += ' '+self.mode_name()

        flags = []
        names = ['hold', 'delta', 'AutoRange', 'BatteryLow', 'Min', 'Max']
        for name in names:
            if getattr(self, name):
                flags.append(name)
        if flags:
            s += ' (' + ','.join(flags) + ')'

        if self.debug:
            s += " "+GATT.TypeHexDump.raw2value(self.raw)
        return s

    def mode_name(self):
        names = [
            'Volts DC', 'Volts AC', 'Amps DC', 'Amps AC', 'Ohms',
            'Farad', 'Hz', 'Percent', 'Centigrade', 'Farenheight',
            'Diode Volts', 'Ohms Beep', 'hFE'
        ]
        return names[self.mode]

    def si_suffix(self):
        # TODO - micro + utf8
        suffixes = ['?000', 'n', 'u', 'm', '', 'k', 'M']
        return suffixes[self.raw_scale1]

    def si_adjust(self):
        scale = [None, 0.000000001, 0.000001, 0.001, 1, 1000, 1000000]
        return scale[self.raw_scale1]

    def decimal_adjust(self):
        scale = [1, 0.1, 0.01, 0.001, 0, 0, 0, float('nan')]
        return scale[self.raw_scale2]

    @property
    def value(self):
        return self.raw_value * self.decimal_adjust() * self.si_adjust()


class Device:

    @classmethod
    def all(cls, bus, prop):
        """look through the available interfaces for sensirion devices
            Note that this is pretty yucky, but works for the moment
        """

        wanted = {
            '0000fff1-0000-1000-8000-00805f9b34fb': 'unknown1str',
            '0000fff2-0000-1000-8000-00805f9b34fb': 'unknown2hex',
            '0000fff3-0000-1000-8000-00805f9b34fb': 'press_button',
            '0000fff4-0000-1000-8000-00805f9b34fb': 'measurement',
            '0000fff5-0000-1000-8000-00805f9b34fb': 'unknown5',
        }
        devices = {}

        all_gatt = prop.interface2paths('org.bluez.GattCharacteristic1')
        for path in all_gatt:
            object = GATT.Characteristic(bus, prop, path)
            if object.uuid in wanted:
                name = wanted[object.uuid]
                device_path = object.device_path()
                if device_path not in devices:
                    devices[device_path] = {}
                devices[device_path][name] = object

        r = []
        for d in devices:
            # ensure that all the required characteristics have been found
            chars = [
                'unknown1str',
                'unknown2hex',
                'press_button',
                'measurement',
                'unknown5'
            ]
            for char_name in chars:
                if char_name not in devices[d]:
                    raise ValueError
            r.append(Device(bus, prop, d, devices[d]))

        return r

    def __init__(self, bus, prop, path, char):
        self.bus = bus
        self.prop = prop
        self.path = path

        self.callback_regular = None
        self.callback_download = None
        self.callbacks_upstream = False
        self.callbacks_self = False

        for char_name in char:
            setattr(self, char_name, char[char_name])

    def _handleData(self, characteristic, value):
        # the device appears to send notifies twicew per second, so we should
        # bucket our data with that in mind - rounding time to 1/10 of
        # a second
        now = int(time.time()*10)/10.0
        value.timestamp = now

        self.callback_regular(self, value)

    def _setup_callbacks(self):
        if self.callback_regular is None and self.callback_download is None:
            # neither callback type is registered, remove upstream callbacks
            self.measurement.NotifyCallback(None)
            self.callbacks_upstream = False
            return

        if self.callbacks_upstream:
            # we have already registered
            return

        self.measurement.NotifyCallback(self._handleData)
        self.callbacks_upstream = True

    def RegularCallback(self, cb):
        """Register a callback for regular per-second updates
        """
        self.callback_regular = cb
        self._setup_callbacks()
