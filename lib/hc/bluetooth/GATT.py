
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


class TypeTimestamp64us(object):
    @classmethod
    def raw2value(cls, raw):
        return TypeUint64.raw2value(raw) / 1000000.0

    @classmethod
    def value2raw(cls, value):
        return TypeUint64.value2raw(value*1000000)


class TypeSensirionFloat32(object):
    @classmethod
    def raw2value(cls, raw):
        if len(raw) == 4:
            return TypeFloat32.raw2value(raw)
        r = []
        r.append(TypeUint32.raw2value(raw[0:4]))
        del raw[0:4]
        while len(raw)>3:
            r.append(TypeFloat32.raw2value(raw[0:4]))
            del raw[0:4]
        return r

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
    '00002a19-0000-1000-8000-00805f9b34fb': { 'func': TypeUint8,
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

    # Sensirion SmartGadget
    '00001235-b38d-4985-720e-0f993a68ee41': { 'func': TypeSensirionFloat32,
        'desc': 'Humidity', 'category': 'normal',
    },
    '00002235-b38d-4985-720e-0f993a68ee41': { 'func': TypeSensirionFloat32,
        'desc': 'Temperature', 'category': 'normal',
    },
    '0000f235-b38d-4985-720e-0f993a68ee41': { 'func': TypeTimestamp64us,
        'desc': 'set_Time', 'category': 'misc',
    },
    '0000f236-b38d-4985-720e-0f993a68ee41': { 'func': TypeTimestamp64us,
        'desc': 'log_Min_Time', 'category': 'misc',
    },
    '0000f237-b38d-4985-720e-0f993a68ee41': { 'func': TypeTimestamp64us,
        'desc': 'log_Max_Time', 'category': 'misc',
    },
    '0000f238-b38d-4985-720e-0f993a68ee41': { 'func': TypeSint8,
        'desc': 'trigger_send_log', 'category': 'misc',
    },
    '0000f239-b38d-4985-720e-0f993a68ee41': { 'func': TypeUint32,
        'desc': 'logger_interval', 'category': 'misc',
    },
}


class Characteristic:
    """Representing a GATT characteristic
    """

    def __init__(self, bus, prop, path):
        # FIXME - there should only be one instance for any path, we should
        # keep a class dictionary and return refs to existing objects
        # if found

        self.path = path
        self.prop = prop

        proxy = bus.get_object('org.bluez',path)
        self.char = dbus.Interface(proxy,
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

    def read(self):
        try:
            raw = self.char.ReadValue({'none': 0})
        except dbus.exceptions.DBusException as e:
            self.prop.invalidate()
            self.exception = e
            return None
        return self.raw2value(raw)

    def write(self,value):
        try:
            raw = self.value2raw(value)
            result = self.char.WriteValue(raw,{'none':0})
        except dbus.exceptions.DBusException as e:
            self.prop.invalidate()
            self.exception = e
            return None
        return result

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
