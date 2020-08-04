#Import regarding dronekit
from __future__ import print_function
from dronekit import connect, VehicleMode
import time

#Import regarding XBee
from digi.xbee.devices import XBeeDevice
from digi.xbee.devices import RemoteXBeeDevice
from digi.xbee.models.address import XBee64BitAddress

#Import regarding scheduler tasks
from apscheduler.schedulers.background import BackgroundScheduler

#Import regarding logging
import logging

#define for logging
#Create and configure logger 
logging.basicConfig(filename="drone.log", 
                    format='%(asctime)s : %(levelname)s :: %(message)s', 
                    filemode='w') 

#Creating an object 
logger=logging.getLogger() 
  
#Setting the threshold of logger to WARNING. i.e only warning, error, and critical message is shown in log. 
'''
 Thresholds:
 DEBUG
 INFO
 WARNING
 ERROR
 CRITICAL 
'''
logger.setLevel(logging.WARNING) 

# define background scheduler
sched = BackgroundScheduler()

#configure for XBee
PORT = '/dev/ttyUSB0'
BAUD_RATE = 9600
DRONE_ID = "0013A200419B5208"

#Set up option parsing to get connection string
import argparse  
parser = argparse.ArgumentParser(description='Print out vehicle state information. Connects to SITL on local PC by default.')
parser.add_argument('--connect', 
                   help="vehicle connection target string. If not specified, SITL automatically started and used.")
args = parser.parse_args()

connection_string = args.connect
sitl = None


#Start SITL if no connection string specified
if not connection_string:
    import dronekit_sitl
    sitl = dronekit_sitl.start_default()
    connection_string = sitl.connection_string()


print("\nConnecting to vehicle on: %s" % connection_string)
vehicle = connect(connection_string, wait_ready=True)

def read_and_send_data():
    try:
        _location_global_relative = vehicle.location.global_relative_frame
        _location_global = vehicle.location.global_frame
    except Exception as e:
        error = {'context':'location','msg':'location not found!!'}
        logger.error(error)

    try:
        _attitude = vehicle.attitude
    except Exception as e:
        error = {'context':'attitude','msg':'attitude not found!!'}
        logger.error(error)
    
    try:
        _velocity = vehicle.velocity
    except Exception as e:
        error = {'context':'velocity','msg':'velocity not found!!'}
        logger.error(error)
    
    try:
        _heading = vehicle.heading
    except Exception as e:
        error = {'context':'heading','msg':'heading not found!!'}
        logger.error(error)
        
    try:
        _groundspeed = vehicle.groundspeed
    except Exception as e:
        error = {'context':'groundspeed','msg':'groundspeed not found!!'}
        logger.error(error)

    try:    
        _airspeed = vehicle.airspeed
    except Exception as e:
        error = {'context':'airspeed','msg':'airspeed not found!!'}
        logger.error(error)
        
    try:
        _mode = vehicle.mode.name
    except Exception as e:
        error = {'context':'mode','msg':'flight mode not found!!'}
        logger.error(error)
        
    try:
        _is_arm = vehicle.armed
    except Exception as e:
        error = {'context':'arm','msg':'arm status not found!!'}
        logger.error(error)
    
    try:
        _ekf_ok = vehicle.ekf_ok
    except Exception as e:
        error = {'context':'ekf','msg':'ekf status not found!!'}
        logger.error(error)
    
    try:
        _status = vehicle.system_status.state
    except Exception as e:
        error = {'context':'status','msg':'vehicle status not found!!'}
        logger.error(error)
        
    try:
        _gps = vehicle.gps_0
    except Exception as e:
        error = {'context':'gps','msg':'gps status not found!!'}
        logger.error(error)

    try:    
        _battery = vehicle.battery
    except Exception as e:
        error = {'context':'battery','msg':'battery status not found!!'}
        logger.error(error)

    try:    
        _lidar = vehicle.rangefinder.distance
    except Exception as e:
        error = {'context':'lidar','msg':'lidar data not found!!'}
        logger.error(error)
        

    print("Alt:",_location.alt)
    print("Sat:",_gps.satellites_visible)
    print("Hdop:",_gps.eph)
    print("fix:",_gps.fix_type)
    print("Head:",_heading)
    print("GS:",_groundspeed)
    print("AS",_airspeed)
    print("mode:",_mode)
    print("Arm:",_is_arm)
    print("EKF:",_ekf_ok)
    print("Status:",_status)
    print("lidar:",_lidar)
    print("Volt:",_battery.voltage)
    print("\r\n ")
    
    data = {}

    data['lat'] = _location_global_relative.lat
    data['lng'] = _location_global_relative.lon
    data['altr'] = _location_global_relative.alt
    data['alt'] = _location_global.alt
    data['roll'] = _attitude.roll
    data['pitch'] = _attitude.pitch
    data['yaw'] = _attitude.yaw
    data['numSat'] = _gps.satellites_visible
    data['hdop'] = _gps.eph
    data['fix'] = _gps.fix_type
    data['head'] = _heading
    data['gs'] = _groundspeed
    data['as'] = _airspeed
    data['mode'] = _mode
    data['arm'] = _is_arm
    data['ekf'] = _ekf_ok
    data['status'] = _status
    data['lidar'] = _lidar
    data['volt'] = _battery.voltage

    data = str(data)
    n = 70 # chunk length
    chunks = []

    for i in range(0, len(data), n):
        chunks.append(data[i:i+n] )

    START_DATA = "$st@"
    try:
        my_device.send_data(remote_device , START_DATA)
    except Exception as e:
        error = {'context':'XBee','msg':'Start string not sent!!'}
        logging.error(error)

    for i in range(len(chunks)):
        DATA_TO_SEND = chunks[i]
        try:
            my_device.send_data(remote_device , DATA_TO_SEND)
        except Exception as e:
            error = {'context':'XBee','msg':'Drone status not sent!!'}
            logging.error(error)

    END_DATA = "$ed@"
    try:
        my_device.send_data(remote_device,END_DATA)
    except Exception as e:
            error = {'context':'XBee','msg':'End string not sent!!'}
            logging.error(error)


my_device = XBeeDevice(PORT, BAUD_RATE)
my_device.open()
remote_device = RemoteXBeeDevice(my_device, XBee64BitAddress.from_hex_string(DRONE_ID))

sched.add_job(read_and_send_data, 'interval', seconds=1)
sched.start()


input()
sched.shutdown()
my_device.close()
