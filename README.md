# Some tools for reading bluetooth low energy gadgets.

The intent of this repository is to end up with a library and some tools
that can be used to monitor a various BLE devices.

It should be able to demonstrate automatically scaning, discovery, connection
to the devices.  Once connected, it should identify monitorable statistics
(or determine that this device has nothing of interest - and blacklist it)
and then collect those stats and output them to someplace from where they
can be graphed or archived.

included tools:

| Name | Hardware | Description |
| ---- | -------- | ----------- |
| test_ble | all | Generic attribute dumping program |
| test_owon | Owon B35T+ | Allows recording the readings from this multimeter |
| test_sensirion | Sensirion Smart Gadget | Show the current and historical temperature and humidity recorded by this device |
| test_sensirion_timebase | Sensirion Smart Gadget | Debugging tool to determine some characteristics of the device reported timestamps |

An important part of helping this to happen is a list of known GATT
properties and their contents.  To this end, there is a quick reference
text summary of some attributes in the [GATT] file.

[GATT]: ./GATT

# Installing required libraries

These tools use the python dbus libraries.  Under a Debian or Ubuntu operating
system, the required package can be installed with:

    sudo apt-get install python-dbus

# Getting Started

## bluetoothctl

The tools here communicate with the bluetooth network stack via the system
bluetoothd daemon.  This communication is done via DBUS, which is why the
dbus library is needed.

By using the standard system-wide daemon, there should be no issues
interoperating with any other users of the bluetooth services on your
system.  In fact, this also means that the tools here can use the devices
detected and connected to using any installed user interface (your desktop
environment may have installed one for you)

There is a commandline bluetooth manager (`bluetoothctl`) included with
the bluez software and the steps to use it are outlined here:

1. Start the manager

   At a shell command prompt, run `bluetoothctl` - this should have no
   requirement to run as root.  You should be presented with a "[bluetooth]#"
   prompt.

1. Power the bluetooth controller

   The default installation leaves bluetooth controllers powered off until
   they are manually powered on, so ensure that has happened:

    ```
    power on
    ```

1. Scanning for devices

   Until a device scan has been done, there are no devices known to the
   bluetooth stack:

    ```
    scan on
    ```

   The scan will run in the background and any found devices will be printed
   out.  Since this will keep running and spamming the screen (and sending
   some bluetooth request packets), it is good to turn it off once the correct
   devices have been discovered:

    ```
    scan off
    ```

1. Listing the known devices

   The bluetooth stack will remember previously seen devices, and this list
   can be shown:

    ```
    devices
    ```

1. Connecting to a device

   The device specific tools included in this repository only work on connected
   devices, so the final setup step is to do that:

    ```
    connect $MACADDR
    ```

   (Use the correct MACADDR from the `devices` list)

## test_ble

This tool provides a general-purpose characteristic download from bluetooth
devices.  While the devices list must have been populated by performing
a bluetooth scan beforehand, it will automatically connect to the
devices.

By default it only fetches "known" attributes that are in the category
"graphable".  Use the "--help" option for more details on changing this.

The tool uses a heuristic to try to exclude non BLE devices, but this can
be disabled with the "--also_nonble" option.

## test_owon

Running this tool will show the current multimeter reading for the connected
multimeters.  The output from this tool is not designed with multiple meters
in mind and if more than one are connected then all their outputs will be
shown intermingled - which may not be what you want.

## test_sensirion

Running this tool will download historical temperature and humidity
measurements and then continue by showing the real-time readings.

There is also an option to skip the real-time monitoring and exit as
soon as the download has completed.

Note that the BLE protocol used to fetch the history is not particularly
robust and while some automated attempts are made to re-request any missing
datapoints, it is still possible for that to fail - if so, this is recorded
in the output.

The output is in a format that can be easily graphed by other tools (such
as gnuplot - see [1] for an example)

[1]: plot_sensirion_data

# Low-level BLE diagnostics

Confirming your hardware and OS drivers are working.

It can be useful to confirm that everything is working using the low-level
tools, before using the tools included in this repository.

Scan for BLE devices:

    sudo hcitool -i hci1 lescan

Once a suitable device has been found, a connection can be made using the
gattool:

    sudo gatttool -i hci1 -t random -b $ADDR -I
