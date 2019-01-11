A collection of notes on reading bluetooth low energy gadgets.

The intent is to end up with a tool that can be used to monitor a collection
of BLE devices.  It should automatically scan, discover, connect to these
devices and then, once connected, it should identify monitorable statistics
(or determine that this device has nothing of interest - and blacklist it)
and then collect those stats and output them to someplace from where they
can be graphed or archived.

An important part of allowing this to happen is a list of known GATT
properties and their contents.

Getting started:
    sudo hcitool -i hci1 lescan

    sudo gatttool -i hci1 -t random -b $ADDR -I

Tools here:

test_ble        - script to fetch attributes from BLE devices.
    Devices must have been discovered by turning bluetooth scanning on
    beforehand.  By default it only fetches "known" attributes that are
    in the category "graphable".  Use the "--help" option for more details

test_sensirion  - script to download the saved temperature log from Sensirion
    SmartGadget Temperature/Humidity sensors.

