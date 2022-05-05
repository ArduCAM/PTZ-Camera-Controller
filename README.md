## Hardware Conncetion
![Alt text](https://github.com/ArduCAM/PTZ-Camera-Controller/blob/master/data/HardwareConnection.png)


## install opencv
* python3 -m pip install opencv-python
* sudo apt-get install libatlas-base-dev
* python3 -m pip install -U numpy 


## Download the source code 
```bash
git clone https://github.com/ArduCAM/PTZ-Camera-Controller.git
```

## Install libcamera
* cd PTZ-Camera-Controller
* python3 -m pip install ./libcamera-1.0.2-cp39-cp39-linux_armv7l.whl

## Add camera
* Edit the configuration file: sudo nano /boot/config.txt
* Find the line: camera_auto_detect=1, update it to:camera_auto_detect=0
* imx219 camera added: dtoverlay=imx219
* imx477 camera added: dtoverlay=imx477
* Save and reboot

## Enable i2c
* cd PTZ-Camera-Controller
* sudo chmod +x enable_i2c_vc.sh
* ./enable_i2c_vc.sh
Press Y to reboot



## Run the FocuserExample.py

* cd PTZ-Camera-Controller
* python3 FocuserExample.py


![Alt text](https://github.com/ArduCAM/PTZ-Camera-Controller/blob/master/data/Arducam%20Controller.png)


## Run the FocuserAutoFocus.py

* cd PTZ-Camera-Controller
* python3 FocuserAutoFocus.py

![Alt text](./data/Focuser%20AutoFocus.png)

### Generate autofocus configuration
``` 
The program will automatically read the autofocus file when it starts, and if it does not have it, it will go to the program that generates the autofocus configuration.
When you enter the program to generate the auto-zoom focus configuration, please fix the camera to focus on the area to be photographed.
If the result is not good, press F to re-generate the configuration.
```
```
tips:When generating the AF table, please ensure that the image is stable, and please turn off the automatic exposure and other functions
```

## Refering the link to get more information about the PTZ-Camera-Controller
http://www.arducam.com/docs/cameras-for-raspberry-pi/ptz-camera/