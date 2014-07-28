solarmax-agent
==============

a simple python script which polls a solarmax inverter (mine is an SM-6000), converts the response to JSON and publishes to an mqtt broker

The values/interpretation of the data returned has been got at via trial and error - use at your own risk :)

dependencies
------------
paho-mqtt  (http://www.eclipse.org/paho/clients/python/)
