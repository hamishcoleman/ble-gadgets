
from gi.repository import GLib
import time

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
        """Merge this measurement with another one, taking only new values
        """
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

    def complete(self):
        """Is this measurement complete?
        """
        if self.temperature is None and self.humidity is None:
            # nothing complete
            return 0
        if self.temperature is not None and self.humidity is not None:
            # everything complete
            return 1

        # otherwise, partially complete
        return 0.5

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
            '00002a19-0000-1000-8000-00805f9b34fb': 'battery',
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

        self.callback_regular = None
        self.callback_download = None
        self.callback_download_progress = None
        self.callbacks_upstream = False
        self.callbacks_self = False

        self.prev_value = None
        self._history = {}
        self._mintime = None
        self._maxtime = None
        self._count = 0
        self._passnr = 0
        self._index = 0

        self._settime_char = char['settime']
        del char['settime']

        for char_name in char:
            setattr(self,char_name,char[char_name])

    # Ideally, settime would return success/fail of trying to write to
    # the dev - the bluez interface does that by raising exceptions
    def settime(self, now=None):
        # to ensure we get current values, invalidate the cache
        self.maxtime.cache_invalidate()
        maxtime = self.maxtime.cache_read()

        if maxtime != 0:
            # the device already thinks it knows the time,
            return None

        if now is None:
            # The device appears to truncate the time internally to 1ms,
            # but it also appears to store the data history with only
            # 1s resolution.  So we use the int() here.
            # Additionally, there appears to be a latency or rounding error, so
            # we subtract the magic number as well (see test_sensirion_timebase
            # for testing on this)
            now = time.time()
            now = int(now-0.42)

        # since the min and max will change again after setting the time,
        # invalidate the cache
        self.mintime.cache_invalidate()
        self.maxtime.cache_invalidate()
        self._settime_char.write(now)
        return now

    def _handleDataRegular(self, characteristic, value):
        # the device sends notifies once per second, so we should
        # bucket our data with that in mind - round time to 1/10 of
        # a second
        now = int(time.time()*10)/10.0
        value.timestamp = now

        if self.prev_value is None:
            # first data
            self.prev_value = value
        if self.prev_value.timestamp == now:
            # this is new data to merge with the existing sample
            self.prev_value += value
        else:
            # this is a new time period, flush the old data
            self.callback_regular(self,self.prev_value)
            self.prev_value = value

    def _handleDataDownload(self, characteristic, values):
        now = time.time()
        self._download_timeout = now + 1

        count_add = 0
        for value in values:
            timestamp = self._maxtime - self._interval * (value.index - 1)
            value.timestamp = timestamp
            if timestamp not in self._history:
                self._history[timestamp] = value
                count_add += value.complete()
            else:
                old_complete = self._history[timestamp].complete()
                self._history[timestamp] += value
                new_complete = self._history[timestamp].complete()
                count_add += new_complete - old_complete

        self._count += count_add
        self._index = values[0].index

    def _DownloadTimeout(self):
        if self._download_timeout is None:
            # download has not started, do nothing
            return True

        if self.callback_download_progress is not None:
            # send a progress report
            self.callback_download_progress(
                self,
                self._index,
                self._passnr,
                self._count,
                self._total,
            )

        now = time.time()
        if now < self._download_timeout:
            # timeout time has not arrived, do nothing
            return True

        # if we get here, the download has started, but not progressed
        # recently

        self.callback_download(self,self._history)
        return False

    def _handleData(self, characteristic, values):
        # single item values time-based regular notifies (and not downloads)
        if type(values) != type(list()):
            return self._handleDataRegular(characteristic, values)

        # this must be a download
        return self._handleDataDownload(characteristic, values)

    def _setup_callbacks(self):
        if self.callback_regular is None and self.callback_download is None:
            # neither callback type is registered, remove upstream callbacks
            self.humidity.NotifyCallback(None)
            self.temperature.NotifyCallback(None)
            self.callbacks_upstream = False
            return

        if self.callbacks_upstream:
            # we have already registered
            return

        self.humidity.NotifyCallback(self._handleData)
        self.temperature.NotifyCallback(self._handleData)
        self.callbacks_upstream = True

    def RegularCallback(self, cb):
        """Register a callback for regular per-second updates
        """
        self.callback_regular = cb
        self._setup_callbacks()

    def DownloadCallback(self, cb):
        """Register a callback for download data
        """
        self.callback_download = cb
        self._setup_callbacks()

    def DownloadProgressCallback(self, cb):
        """Register a callback getting status on the download in progress
        """
        self.callback_download_progress = cb

    def DownloadSetup(self):
        """Fetch all the values and do all the calculations for a download
        """
        now = self.settime()
        # TODO - check return value for errors?

        # Note:
        # We actually only care about the value of maxtime, but the device has
        # a curious corner case when doing its sample update:
        # - First, it increases the maxtime /and/ the mintime by interval
        # - Then, it corrects the mintime backwards by interval
        # I can only assume what the data would look like during this dump, but
        # we can error out by checking the mintime value

        prev_mintime = self._mintime
        prev_maxtime = self._maxtime

        self._mintime = self.mintime.cache_read()

        if self._mintime is None:
            # not connected?
            return None

        self._settime = now
        self._maxtime = self.maxtime.cache_read()
        self._interval = self.interval.cache_read()
        self._timespan = self._maxtime - self._mintime
        self._total = int(self._timespan / self._interval)
        self._passnr += 1
        self._download_timeout = None

        if prev_mintime is not None:
            # This is not the first pass through the download
            delta_mintime = prev_mintime - self._mintime

            if abs(delta_mintime) > (self._interval / 2):
                # the time base moved, our history is now invalid, so dont
                # try any downloads
                # FIXME - this should be a recoverable error
                print "ERROR: previous mintime {} is not current {}".format(
                    prev_mintime,
                    self._mintime,
                )
                return None

        if prev_maxtime is not None:
            # This is not the first pass through the download
            delta_maxtime = prev_maxtime - self._maxtime

            if abs(delta_maxtime) > (self._interval / 2):
                # the time base moved
                # FIXME - this should be a recoverable error
                print "ERROR: previous maxtime {} is not current {}".format(
                    prev_maxtime,
                    self._maxtime,
                )
                return None

            # Keep the timebase comparable, using force
            self._maxtime = prev_maxtime

        def runonce(func,*args):
            """A wrapper for the GLib.timeout_add that just runs once
            """
            func(*args)
            return False

        if not self.callbacks_self:
            GLib.timeout_add_seconds(0, runonce, self.humidity.StartNotify)
            GLib.timeout_add_seconds(0, runonce, self.temperature.StartNotify)
            self.callbacks_self = True

        # FIXME - dont add this twice either..
        GLib.timeout_add_seconds(1, self._DownloadTimeout)
        return True

    def DownloadGo(self):
        """Actually start the download
        """

        def runonce(func,*args):
            """A wrapper for the GLib.timeout_add that just runs once
            """
            func(*args)
            return False

        GLib.timeout_add_seconds(0, runonce, self.sendlog.write, 1)

