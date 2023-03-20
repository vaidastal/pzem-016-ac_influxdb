# pzem-016-ac_influxdb
Python script to parse data into InfluxDB from PZEM-016 AC meter attached to ESP8266.

PZEM-016 AC meter is attached to ESP8266 via RS485 to RS232 converter. ESP8266 is flashed with ESPLink firmware. It is important to set baud rate of ESPLink serial to 9600 in order to match PZEM-016 baud rate. 

At the top of python script file there is a brief setup: IP address of ESP8266, port number, influxDB measurement name and sensor name. After reading the data, script will output parsed data in influxDB line protocol. Adjust it as needed. Script is designed to work with Telegraf. You can test the script by simply running it on a machine that has python installed. If successful, output should be similar to:

electricity,sensor=mains voltage=235.2,current=0.748,power=133.5,energy=71764,frequency=50.0,power_factor=0.76

For more information regarding PZEM-016, see its manual.
