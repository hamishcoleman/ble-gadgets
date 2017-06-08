
import struct
import dbus


class TypeSint8(object):
    @classmethod
    def raw2value(cls, raw):
        return struct.unpack('b',bytearray(raw))[0]

    @classmethod
    def value2raw(cls, value):
        return struct.pack('b',value)


class TypeUint8(object):
    @classmethod
    def raw2value(cls, raw):
        return struct.unpack('B',bytearray(raw))[0]

    @classmethod
    def value2raw(cls, value):
        return struct.pack('B',value)


class TypeUint32(object):
    @classmethod
    def raw2value(cls, raw):
        return struct.unpack('<I',bytearray(raw))[0]

    @classmethod
    def value2raw(cls, value):
        return struct.pack('<I',value)


class TypeFloat32(object):
    @classmethod
    def raw2value(cls, raw):
        return struct.unpack('<f',bytearray(raw))[0]

    @classmethod
    def value2raw(cls, value):
        return struct.pack('<f',value)


class TypeUint64(object):
    @classmethod
    def raw2value(cls, raw):
        return struct.unpack('<Q',bytearray(raw))[0]

    @classmethod
    def value2raw(cls, value):
        return struct.pack('<Q',value)


class TypeUtf8s(object):
    @classmethod
    def raw2value(cls, raw):
        return bytearray(raw).decode('utf8')

    @classmethod
    def value2raw(cls, value):
        return value.encode('utf8')


class TypeHexDigits(object):
    @classmethod
    def raw2value(cls, raw):
        s = ''
        for ch in raw[::-1]:
            s += format(ch,'02x')
        return s


class TypeHexDump(object):
    @classmethod
    def raw2value(cls, raw):
        s = ''
        h = ''
        for ch in raw:
            if ch in range(0x20,0x7e):
                s += chr(ch)
            else:
                s += ' '
            h += format(ch,'02x') + ','
        return h+' '+s


class TypePercentUint8(object):
    @classmethod
    def raw2value(cls, raw):
        return TypeUint8.raw2value(raw) / 100.0

    @classmethod
    def value2raw(cls, value):
        return TypeUint8.value2raw(value*100)


gatt_list = {
    # Standard things
    '00002a00-0000-1000-8000-00805f9b34fb': { 'func': TypeUtf8s,
        'desc': 'device_name', 'category': 'string',
    },
    '00002a05-0000-1000-8000-00805f9b34fb': { 'func': TypeHexDump,
        'desc': 'service_changed', 'category': 'misc',
    },
    #'00002a06-0000-1000-8000-00805f9b34fb': { 'func': TypeSint8,
    #    'desc': 'alert_level', 'category': 'writable', # TODO - handle writes
    #},
    '00002a07-0000-1000-8000-00805f9b34fb': { 'func': TypeSint8,
        'desc': 'tx_power_level', 'category': 'normal',
    },
    '00002a19-0000-1000-8000-00805f9b34fb': { 'func': TypePercentUint8,
        'desc': 'Battery', 'category': 'normal',
    },
    '00002a23-0000-1000-8000-00805f9b34fb': { 'func': TypeHexDigits,
        'desc': 'system_id', 'category': 'id',
    },
    '00002a24-0000-1000-8000-00805f9b34fb': { 'func': TypeUtf8s,
        'desc': 'model_number', 'category': 'string',
    },
    '00002a25-0000-1000-8000-00805f9b34fb': { 'func': TypeUtf8s,
        'desc': 'serial_number', 'category': 'string',
    },
    '00002a26-0000-1000-8000-00805f9b34fb': { 'func': TypeUtf8s,
        'desc': 'firmware_revision', 'category': 'string',
    },
    '00002a27-0000-1000-8000-00805f9b34fb': { 'func': TypeUtf8s,
        'desc': 'hardware_revision', 'category': 'string',
    },
    '00002a28-0000-1000-8000-00805f9b34fb': { 'func': TypeUtf8s,
        'desc': 'software_revision', 'category': 'string',
    },
    '00002a29-0000-1000-8000-00805f9b34fb': { 'func': TypeUtf8s,
        'desc': 'manufacturer_name', 'category': 'string',
    },
}


class Characteristic:
    """Representing a GATT characteristic
    """

    @classmethod
    def register(cls, list):
        """Register new GATT characteristic types
        """
        gatt_list.update(list)


    def __init__(self, bus, prop, path):
        # FIXME - there should only be one instance for any path, we should
        # keep a class dictionary and return refs to existing objects
        # if found

        self.cache = None
        self.signal = None
        self.callback = None

        self.path = path
        self.prop = prop

        self.proxy = bus.get_object('org.bluez',path)
        self.char = dbus.Interface(self.proxy,
                              dbus_interface="org.bluez.GattCharacteristic1")

        # properties that will not change
        self.uuid = self.prop.Get(self.path, 'org.bluez.GattCharacteristic1','UUID')

        if self.uuid in gatt_list:
            self.entry = gatt_list[self.uuid]
            self.known = True
        else:
            self.entry = {
                'func': TypeHexDump,
                'desc': 'UUID:'+self.uuid,
                'category': 'unknown',
            }
            self.known = False

        self.desc = self.entry['desc']
        self.category = self.entry['category']
        self.exception = None

    def raw2value(self,raw):
        """Given the raw read results, convert it to a meaningful object
        """
        return self.entry['func'].raw2value(raw)

    def value2raw(self,value):
        """Convert the meaningful value into a raw object bytestring
        """
        return self.entry['func'].value2raw(value)

#
# TODO - why am I messing around with catching the exceptions here?

    def read(self):
        self.exception = None
        try:
            raw = self.char.ReadValue({'none': 0})
        except dbus.exceptions.DBusException as e:
            self.prop.invalidate()
            self.exception = e
            return None
        return self.raw2value(raw)

    def write(self,value):
        self.cache_invalidate()
        self.exception = None
        try:
            raw = self.value2raw(value)
            result = self.char.WriteValue(raw,{'none':0})
        except dbus.exceptions.DBusException as e:
            self.prop.invalidate()
            self.exception = e
            return None
        return result

    def cache_invalidate(self):
        self.cache = None

    def cache_read(self):
        if self.cache is None:
            self.cache = self.read()
        return self.cache

    def StartNotify(self):
        return self.char.StartNotify()

    def StopNotify(self):
        return self.char.StopNotify()

    def device_path(self):
        """Follow the pointers in the objects to find the parent device
        """
        service_path = self.prop.Get(self.path, 'org.bluez.GattCharacteristic1','Service')
        device_path = self.prop.Get(service_path, 'org.bluez.GattService1','Device')
        return device_path

    def NotifyCallback(self,callback):
        """Set a callback function that will recieve new values
        """
        if callback is None:
            # clear out our junk
            self.signal.remove()
            self.signal = None
            self.callback = None
            #self.StopNotify()
            return

        if self.signal is not None:
            raise ValueError
        if self.callback is not None:
            raise ValueError

        def wrapper(*args,**kwargs):
            if args[0] != 'org.bluez.GattCharacteristic1':
                # will this ever happen?
                raise ValueError
            if 'Value' not in args[1]:
                # it will call us with "Notifying=True" (and probably false)
                return
            values = self.raw2value(args[1]['Value'])
            self.callback(self,values)

        self.callback = callback
        self.signal = self.proxy.connect_to_signal('PropertiesChanged',wrapper)
        #self.StartNotify()
