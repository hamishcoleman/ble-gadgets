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

# Installing required libraries

These tools use the python dbus libraries.  Under a Debian or Ubuntu operating
system, the required package can be installed with:

    sudo apt-get install python-dbus

# Getting Started

## bluetoothctl

## test_ble

test_ble        - script to fetch attributes from BLE devices.
    Devices must have been discovered by turning bluetooth scanning on
    beforehand.  By default it only fetches "known" attributes that are
    in the category "graphable".  Use the "--help" option for more details

## test_owon

Running this tool will show the current multimeter reading for the connected
multimeters.  The output from this tool is not designed with multiple meters
in mind and if more than one are connected then all their outputs will be
shown intermingled - which may not be what you want.

## test_sensirion

test_sensirion  - script to download the saved temperature log from Sensirion
    SmartGadget Temperature/Humidity sensors.

# Low-level BLE diagnostics

Confirming your hardware and OS drivers are working.

It can be useful to confirm that everything is working using the low-level
tools, before using the tools included in this repository.

Scan for BLE devices:

    sudo hcitool -i hci1 lescan

Once a suitable device has been found, a connection can be made using the
gattool:

    sudo gatttool -i hci1 -t random -b $ADDR -I
