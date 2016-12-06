
import struct
import dbus

def dbus2string(array):
    s = ''
    for ch in array:
        s += chr(ch)
    return s

def dbus2float32t(array):
    """Dbus returns us a "dbus.Array", we want the float from inside that
    """
    s = dbus2string(array)
    return (struct.unpack('<f',s))[0]

def dbus2uint32t(array):
    s = dbus2string(array)
    return (struct.unpack('<I',s))[0]

def dbus2uint64t(array):
    s = dbus2string(array)
    return (struct.unpack('<Q',s))[0]

def dbus2sint8(array):
    if array:
        return (struct.unpack('b',chr(array[0])))[0]
    else:
        return None

def dbus2uint8t(array):
    if array:
        return int(array[0])
    else:
        return None

def dbus2hexdigits(array):
    s = ''
    for ch in array[::-1]:
        s += format(ch,'02x')
    return s

def dbus2hexdump(array):
    s = ''
    h = ''
    for ch in array:
        if ch in range(0x20,0x7e):
            s += chr(ch)
        else:
            s += ' '
        h += hex(ch) + ','
    return h+' '+s


gatt_list = {
    # Standard things
    '00002a00-0000-1000-8000-00805f9b34fb': { 'func': dbus2string,
        'desc': 'device_name', 'category': 'string',
    },
    '00002a05-0000-1000-8000-00805f9b34fb': { 'func': dbus2hexdump,
        'desc': 'service_changed', 'category': 'misc',
    },
    #'00002a06-0000-1000-8000-00805f9b34fb': { 'func': dbus2sint8,
    #    'desc': 'alert_level', 'category': 'writable', # TODO - handle writes
    #},
    '00002a07-0000-1000-8000-00805f9b34fb': { 'func': dbus2sint8,
        'desc': 'tx_power_level', 'category': 'normal',
    },
    '00002a19-0000-1000-8000-00805f9b34fb': { 'func': dbus2uint8t,
        'desc': 'Battery', 'category': 'normal',
    },
    '00002a23-0000-1000-8000-00805f9b34fb': { 'func': dbus2hexdigits,
        'desc': 'system_id', 'category': 'id',
    },
    '00002a24-0000-1000-8000-00805f9b34fb': { 'func': dbus2string,
        'desc': 'model_number', 'category': 'string',
    },
    '00002a25-0000-1000-8000-00805f9b34fb': { 'func': dbus2string,
        'desc': 'serial_number', 'category': 'string',
    },
    '00002a26-0000-1000-8000-00805f9b34fb': { 'func': dbus2string,
        'desc': 'firmware_revision', 'category': 'string',
    },
    '00002a27-0000-1000-8000-00805f9b34fb': { 'func': dbus2string,
        'desc': 'hardware_revision', 'category': 'string',
    },
    '00002a28-0000-1000-8000-00805f9b34fb': { 'func': dbus2string,
        'desc': 'software_revision', 'category': 'string',
    },
    '00002a29-0000-1000-8000-00805f9b34fb': { 'func': dbus2string,
        'desc': 'manufacturer_name', 'category': 'string',
    },

    # Sensirion SmartGadget
    '00001235-b38d-4985-720e-0f993a68ee41': { 'func': dbus2float32t,
        'desc': 'Humidity', 'category': 'normal',
    },
    '00002235-b38d-4985-720e-0f993a68ee41': { 'func': dbus2float32t,
        'desc': 'Temperature', 'category': 'normal',
    },
    '0000f236-b38d-4985-720e-0f993a68ee41': { 'func': dbus2uint64t,
        'desc': 'log_Min_Time', 'category': 'misc',
    },
    '0000f237-b38d-4985-720e-0f993a68ee41': { 'func': dbus2uint64t,
        'desc': 'log_Max_Time', 'category': 'misc',
    },
    '0000f239-b38d-4985-720e-0f993a68ee41': { 'func': dbus2uint32t,
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
                'func': dbus2hexdump,
                'desc': 'UUID:'+self.uuid,
                'category': 'unknown',
            }
            self.known = False

        self.desc = self.entry['desc']
        self.category = self.entry['category']
        self.exception = None

    def convertraw(self,raw):
        """Given the raw read results, convert it to a meaningful object
        """
        return self.entry['func'](raw)

    def read(self):
        try:
            value = self.char.ReadValue({'none': 0})
        except dbus.exceptions.DBusException as e:
            self.prop.invalidate()
            self.exception = e
            return None
        return self.convertraw(value)

    def write(self,value):
        try:
            result = self.char.WriteValue(value,{'none':0})
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
