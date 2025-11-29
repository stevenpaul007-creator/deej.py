# deej.py
a python version of deej, to control volume in linux.

this is almost from [https://bendiksens.net/posts/deej-sound-control-for-linux-written-in-python/]

## Permision
1. try `sudo usermod -a -G dialout $USER`  OR

2. try udev rules:
```
lsusb
Bus 009 Device 004: ID 1209:c550 Generic CH55xduino
```
add line to /etc/udev/rules.d/99-deej-py.rules
```
ATTRS{idVendor}=="1209", ATTRS{idProduct}=="c550", MODE:="0666", ENV{ID_MM_DEVICE_IGNORE}="1", ENV{ID_MM_PORT_IGNORE}="1"
```
and
```
sudo udevadm control --reload-rules
sudo udevadm trigger
```