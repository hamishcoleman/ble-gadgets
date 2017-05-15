
import hc.bluetooth.GATT as GATT


class TypeMeasurement(object):
    @classmethod
    def raw2value(cls, attr, raw):
        if len(raw) == 4:
            obj = Measurement()
            setattr(obj, attr, GATT.TypeFloat32.raw2value(raw))
            return obj

        index = GATT.TypeUint32.raw2value(raw[0:4])
        del raw[0:4]
        r = []
        while len(raw)>3:
            obj = Measurement()
            setattr(obj, attr, GATT.TypeFloat32.raw2value(raw[0:4]))
            obj.index = index
            r.append(obj)
            del raw[0:4]
            index += 1
        return r


class TypeHumidity(object):
    @classmethod
    def raw2value(cls, raw):
        return TypeMeasurement.raw2value('humidity',raw)


class TypeTemperature(object):
    @classmethod
    def raw2value(cls, raw):
        return TypeMeasurement.raw2value('temperature',raw)


class TypeTimestamp64ms(object):
    @classmethod
    def raw2value(cls, raw):
        return GATT.TypeUint64.raw2value(raw) / 1000.0

    @classmethod
    def value2raw(cls, value):
        return GATT.TypeUint64.value2raw(value*1000)


class TypeSensirion32interval(object):
    @classmethod
    def raw2value(cls, raw):
        return GATT.TypeUint32.raw2value(raw) / 1000.0

    @classmethod
    def value2raw(cls, value):
        return GATT.TypeUint32.value2raw(value*1000)


gatt_list = {
    # Sensirion SmartGadget
    '00001235-b38d-4985-720e-0f993a68ee41': { 'func': TypeHumidity,
        'desc': 'Humidity', 'category': 'normal',
    },
    '00002235-b38d-4985-720e-0f993a68ee41': { 'func': TypeTemperature,
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
    '0000f238-b38d-4985-720e-0f993a68ee41': { 'func': GATT.TypeSint8,
        'desc': 'trigger_send_log', 'category': 'misc',
    },
    '0000f239-b38d-4985-720e-0f993a68ee41': { 'func': TypeSensirion32interval,
        'desc': 'logger_interval', 'category': 'misc',
    },
}

GATT.Characteristic.register(gatt_list)


class Measurement:

    def __init__(self):
        self.index = None
        self.timestamp = None
        self.temperature = None
        self.humidity = None

    def __add__(self, value):
        if not isinstance(value, Measurement):
            raise TypeError

        if self.index is None:
            self.index = value.index
        if self.timestamp is None:
            self.timestamp = value.timestamp
        if self.temperature is None:
            self.temperature = value.temperature
        if self.humidity is None:
            self.humidity = value.humidity

        return self

    def __str__(self):

        # if we have no values, dont return a string!
        if self.temperature is None and self.humidity is None:
            return None

        s = ''
        if self.temperature is not None:
            s += "{:.2f}".format(self.temperature)
        else:
            s += "\N"
        s += " "
        if self.humidity is not None:
            s += "{:.2f}".format(self.humidity)
        else:
            s += "\N"

        return s

