import socket
import time
import logging
import struct

CRC_MISMATCH = "CRC mismatch of received package. Sleep time before receipt of the package was extended."
SOCKET_OPEN_ERROR_MSG = "Failed to open socket."
FAILED_READ = "Failed to read data from source with a maximum delay."
SOCKET_BROKEN = "Socket connection is broken."
INBOUND_MSG_SIZE = 25

# Settings
##################################
hostname = "192.168.20.65"
port = 23
sensor_name = "mains"            # sensor name that will be used for influx database, sensor column.  
measurement = "electricity"       # measurement (table) name of influx database
##################################

def modbus_rtu_crc(data):
    crc = 0xFFFF
    for pos in data:
        crc ^= pos                  # XOR byte into least sig. byte of crc       
        for i in range(8):          # Loop over each bit
            if ((crc & 1) != 0):    # If the LSB is set
                crc >>= 1           # Shift right and XOR 0xA001
                crc ^= 0xA001       
            else:                   # Else LSB is not set
                crc >>= 1           # Just shift right
    # Note, this number has low and high bytes swapped
    return crc

def swap16(i):
    return struct.unpack("<H", struct.pack(">H", i))[0]

def getData(host, port, msg):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except OSError as e:
        sock = None
        logging.exception(e.args[0])
    try:
        sock.connect((host, port))
    except OSError as e:
        sock.close()
        sock = None  
        logging.exception(e.args[0])  
    if sock is None:
        logging.error(SOCKET_OPEN_ERROR_MSG)
    else:  
        try: 
            total_sent = 0
            while total_sent < len(msg):
                sent = sock.send(msg[total_sent:])
                if sent == 0:
                    raise RuntimeError(SOCKET_BROKEN)
                total_sent += sent

            response = b''
            bytes_received = 0
            while bytes_received < INBOUND_MSG_SIZE:
                data = sock.recv(min(INBOUND_MSG_SIZE - bytes_received, 2048))
                if data == b'':
                    raise RuntimeError(SOCKET_BROKEN)
                response += data
                bytes_received += len(data)

            received_crc = struct.unpack(">H", response[23:25])[0]
            expected_crc = swap16(modbus_rtu_crc(response[0:23]))
            if received_crc != expected_crc:
                raise RuntimeError(CRC_MISMATCH)
                        
        except (OSError, TimeoutError, RuntimeError) as e:
            logging.exception(e.args[0]) 
        finally:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            sock = None

    return response

message_content = b"\x01\x04\x00\x00\x00\x0A"  # full message to PZEM-016 AC that retrieves all 10 registers.

message_crc = swap16(modbus_rtu_crc(message_content))
full_message = b''.join([message_content, struct.pack(">H", message_crc)])
response = getData(hostname, port, full_message)

voltage = struct.unpack(">H", response[3:5])[0] / 10

current_low16 = struct.unpack(">H", response[5:7])[0]
current_high16 = struct.unpack(">H", response[7:9])[0]
current = struct.unpack(">I", struct.pack(">HH", current_high16, current_low16))[0] / 1000

power_low16 = struct.unpack(">H", response[9:11])[0]
power_high16 = struct.unpack(">H", response[11:13])[0]
power = struct.unpack(">I", struct.pack(">HH", power_high16, power_low16))[0] / 10

energy_low16 = struct.unpack(">H", response[13:15])[0]
energy_high16 = struct.unpack(">H", response[15:17])[0]
energy = struct.unpack(">I", struct.pack(">HH", energy_high16, energy_low16))[0] 

frequency = struct.unpack(">H", response[17:19])[0] / 10

power_factor = struct.unpack(">H", response[19:21])[0] / 100

line = measurement + "," + "sensor=" + sensor_name + " " + "voltage=" + str(voltage) + ",current=" + str(current) + ",power=" + str(power) + ",energy=" + str(energy) + ",frequency=" + str(frequency) + ",power_factor=" + str(power_factor)
print(line)
