
import dbus

class Cache:
    """Keep a cache of the managed objects
    """
    # Theoretically, I could listen for signals and keep a local model of
    # the properties updated with that.  But that would need an event loop
    # and (I think) more complextiy
    #
    # TODO - this is a hacky singleton, investigate python best practices

    def __init__(self, bus):
        # TODO: do we care that this hardcodes the destination on what is
        # a generic call?
        proxy = bus.get_object('org.bluez','/')

        self.manager = dbus.Interface(proxy,
                          dbus_interface="org.freedesktop.DBus.ObjectManager")
        self.valid = 0

    def _validate(self):
        """Ensure that the cache is currently valid
           This could be a more complex cache validity system, but right
           now, it can simply throw away the whole cache
        """
        if not self.valid:
            # TODO - ideally, we would detect that we have a main loop
            # running and use an async call and run the loop while waiting
            self.all_objects = self.manager.GetManagedObjects()
            self.valid = 1

    def invalidate(self):
        self.valid = 0

    def Get(self,path,interface,property):
        self._validate()
        if path not in self.all_objects:
            return None
        if interface not in self.all_objects[path]:
            return None
        if property not in self.all_objects[path][interface]:
            return None
        return self.all_objects[path][interface][property]

    def interface2paths(self,interface):
        """Return the set of all paths that have the given interface
        """
        self._validate()
        result = set()
        for path, interfaces in self.all_objects.iteritems():
            if interface in interfaces:
                result.add(path)
        return result

