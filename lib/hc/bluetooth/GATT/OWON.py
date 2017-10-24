
from gi.repository import GLib
import time

import hc.bluetooth.GATT as GATT

class TypeMeasurement(object):
    @classmethod
    def raw2value(cls, raw):
        obj = MeasurementBase()
        obj.raw = raw
        return obj


gatt_list = {
    '0000fff0-0000-1000-8000-00805f9b34fb': { 'func': GATT.TypeHexDump,
        'desc': 'UUID', 'category': 'strings',
    },
    '0000fff1-0000-1000-8000-00805f9b34fb': { 'func': GATT.TypeUtf8s,
        # "ABCDEFGHIJKLMN"
        'desc': 'unknown1', 'category': 'strings',
    },
    '0000fff2-0000-1000-8000-00805f9b34fb': { 'func': GATT.TypeHexDump,
        # 23,ff,00,01,02,00
        'desc': 'unknown2', 'category': 'strings',
    },
#    '0000fff3-0000-1000-8000-00805f9b34fb': { 'func': GATT.TypeHexDump,
#        # Write uint8 button_nr, uint8 times
#        'desc': 'press_button', 'category': 'misc',
#    },
    '0000fff4-0000-1000-8000-00805f9b34fb': { 'func': TypeMeasurement,
        # Notify only
        'desc': 'measurement', 'category': 'normal',
    },
#    '0000fff5-0000-1000-8000-00805f9b34fb': { 'func': GATT.TypeHexDump,
#        # Write
#        'desc': 'unknown5', 'category': 'strings',
#    },
}

GATT.Characteristic.register(gatt_list)

class MeasurementBase:

    def __init__(self):
        self.timestamp = None
        self.raw = None

    def __str__(self):
        return GATT.TypeHexDump.raw2value(self.raw)

class Device:

    @classmethod
    def all(cls, bus,prop):
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
            object = GATT.Characteristic(bus,prop,path)
            if object.uuid in wanted:
                name = wanted[object.uuid]
                device_path = object.device_path()
                if device_path not in devices:
                    devices[device_path] = {}
                devices[device_path][name] = object

        r = []
        for d in devices:
            # ensure that all the required characteristics have been found
            for char_name in ['unknown1str','unknown2hex','press_button','measurement','unknown5']:
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
            setattr(self,char_name,char[char_name])

    def _handleData(self, characteristic, value):
        # the device appears to send notifies twicew per second, so we should
        # bucket our data with that in mind - rounding time to 1/10 of
        # a second
        now = int(time.time()*10)/10.0
        value.timestamp = now

        self.callback_regular(self,value)

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

