
import struct

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
    '0000f239-b38d-4985-720e-0f993a68ee41': { 'func': dbus2uint32t,
        'desc': 'logger_interval', 'category': 'misc',
    },
}


