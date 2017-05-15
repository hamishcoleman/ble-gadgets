
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

class Device:

    @classmethod
    def all(cls, bus,prop):
        """look through the available interfaces for sensirion devices
            Note that this is pretty yucky, but works for the moment
        """

        wanted = {
            '00001235-b38d-4985-720e-0f993a68ee41': 'humidity',
            '00002235-b38d-4985-720e-0f993a68ee41': 'temperature',
            '0000f235-b38d-4985-720e-0f993a68ee41': 'settime',
            '0000f236-b38d-4985-720e-0f993a68ee41': 'mintime',
            '0000f237-b38d-4985-720e-0f993a68ee41': 'maxtime',
            '0000f238-b38d-4985-720e-0f993a68ee41': 'sendlog',
            '0000f239-b38d-4985-720e-0f993a68ee41': 'interval',
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
            for char_name in ['humidity','temperature','mintime','maxtime','sendlog','interval']:
                if char_name not in devices[d]:
                    raise ValueError
            r.append(Device(bus, prop, d, devices[d]))

        return r

    def __init__(self, bus, prop, path, char):
        self.bus = bus
        self.prop = prop
        self.path = path

        self._settime = char['settime']
        del char['settime']

        for char_name in char:
            setattr(self,char_name,char[char_name])

    # FIXME - is the 'settime' characteristic readable?
    def settime(self, now=None):
        if now is None:
            # the device appears to truncate to seconds, match that here
            now = int(time.time())
        return self._settime.write(now)

