
import hc.bluetooth.GATT


class TypeSensirionFloat32(object):
    @classmethod
    def raw2value(cls, raw):
        if len(raw) == 4:
            return hc.bluetooth.GATT.TypeFloat32.raw2value(raw)
        r = []
        r.append(hc.bluetooth.GATT.TypeUint32.raw2value(raw[0:4]))
        del raw[0:4]
        while len(raw)>3:
            r.append(hc.bluetooth.GATT.TypeFloat32.raw2value(raw[0:4]))
            del raw[0:4]
        return r


class TypeTimestamp64ms(object):
    @classmethod
    def raw2value(cls, raw):
        return hc.bluetooth.GATT.TypeUint64.raw2value(raw) / 1000.0

    @classmethod
    def value2raw(cls, value):
        return hc.bluetooth.GATT.TypeUint64.value2raw(value*1000)


class TypeSensirion32interval(object):
    @classmethod
    def raw2value(cls, raw):
        return hc.bluetooth.GATT.TypeUint32.raw2value(raw) / 1000.0

    @classmethod
    def value2raw(cls, value):
        return hc.bluetooth.GATT.TypeUint32.value2raw(value*1000)


gatt_list_sensirion = {
    # Sensirion SmartGadget
    '00001235-b38d-4985-720e-0f993a68ee41': { 'func': TypeSensirionFloat32,
        'desc': 'Humidity', 'category': 'normal',
    },
    '00002235-b38d-4985-720e-0f993a68ee41': { 'func': TypeSensirionFloat32,
        'desc': 'Temperature', 'category': 'normal',
    },
    '0000f235-b38d-4985-720e-0f993a68ee41': { 'func': TypeTimestamp64ms,
        'desc': 'set_Time', 'category': 'misc',
    },
    '0000f236-b38d-4985-720e-0f993a68ee41': { 'func': TypeTimestamp64ms,
        'desc': 'log_Min_Time', 'category': 'misc',
    },
    '0000f237-b38d-4985-720e-0f993a68ee41': { 'func': TypeTimestamp64ms,
        'desc': 'log_Max_Time', 'category': 'misc',
    },
    '0000f238-b38d-4985-720e-0f993a68ee41': { 'func': hc.bluetooth.GATT.TypeSint8,
        'desc': 'trigger_send_log', 'category': 'misc',
    },
    '0000f239-b38d-4985-720e-0f993a68ee41': { 'func': TypeSensirion32interval,
        'desc': 'logger_interval', 'category': 'misc',
    },
}

hc.bluetooth.GATT.Characteristic.register(gatt_list_sensirion)


