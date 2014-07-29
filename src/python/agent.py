import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import socket
import sys
import time


##  this agent reads from the solarmax inverter socket and
## publishes the data to a mqtt listener

## constants
inverter_ip = "192.168.1.90"
inverter_port = 12345

mqtt_broker_ip = "192.168.1.24"
mqtt_broker_port = 1883
mqtt_broker_url = "http://" + mqtt_broker_ip + ":" + str(mqtt_broker_port)

mqtt_topic = "/data/inverter"


IDC = "IDC"   ## DC Current
UL1 = "UL1"   ## Voltage Phase 1
TKK = "TKK"   ## inverter operating temp
IL1 = "IL1"   ## current phase 1
SYS = "SYS"   ## 4E28 = 17128
TNF = "TNF"   ## generated frequency (Hz)
UDC = "UDC"   ## DC voltage (V DC)
PAC = "PAC"   ## AC power being generated * 2 (W)
PRL = "PRL"   ## relative output (%)
KT0 = "KT0"   ## total yield (kWh)

field_map = {
    IDC : 'dc_current',
    UL1 : 'voltage_phase1',
    TKK : 'inverter_temp',
    IL1 : 'current_phase1',
    SYS : 'sys',
    TNF : 'frequency',
    UDC : 'dc_voltage',
    PAC : 'power_output',
    PRL : 'relative_ouput',
    KT0 : 'total_yield' }


req_data = "{FB;01;3E|64:IDC;UL1;TKK;IL1;SYS;TNF;UDC;PAC;PRL;KT0;SYS|0F66}"


def publish_message(topic, payload):
    """ publish the message to the mqtt broker
    --- accepts a JSON payload
    --- publishs to the """
    publish.single(topic, payload, 0,hostname=mqtt_broker_ip)
    return

def genData(s):
    """ takes a pair: <field>=<0xdata> and converts to a list
    with the name mapped using field_map and value converted to base 10 and appropriately scaled """

    t = s.split('=')
    f = t[0]

    if (f == SYS):   # remove the trailing ,0
        v = int(t[1][:t[1].find(',')],16)
    else:
        v = int(t[1],16)

    if (f == PAC ):    # PAC values are *2 for some reason
        v = v/2

    if (f == UL1 or f == UDC):  # voltage levels need to be divide by 10
        v = v/10.0

    if (f == IDC or f == TNF):  #current & frequency needs to be divided by 100
        v = v/100.0

    return [field_map[f],v]

def convert_to_json (data):
    """ convert the inverter message to JSON
    -- data: {01;FB;70|64:IDC=407;UL1=A01;TKK=2C;IL1=46D;SYS=4E28,0;TNF=1383;UDC=B7D;PAC=16A6;PRL=2B;KT0=48C;SYS=4E28,0|1A5F}
    -- return:
    """
    ## pull out the data elements into a list  and replace the code with the json field name
    ev = [genData(s) for s in  data[data.find(':')+1:data.find('|',data.find(':'))].split(';')]
    outStr = '{'
    for e in ev:
        outStr = outStr + '"' + str(e[0]) + '" : ' + str(e[1]) + ','
    outStr = outStr[:len(outStr)-1] + '}'  # remove the trailing comma then close the braces
    return outStr

def check_msg(msg):
    """ check that the message is valid """
    return msg

def publish_data (data):
    print 'publishing: ' + str(data) + '\n'
    json_data = convert_to_json(data)
    print 'published: ' + str(json_data) + '\n'
    publish_message(mqtt_topic, json_data)
    return

def connect_to_inverter():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((inverter_ip, inverter_port))
    except socket.error, msg:
        print 'Failed to create socket: Error code: ' + str(msg)
        sys.exit();
    return s

def read_data(sock, request):
    sock.send(request)
    data_received = False
    response = ""
    while not data_received:
        buf = sock.recv(1024)
        if len(buf) > 0:
            response = response + buf
            data_received = True

    response = check_msg(response)
    return response



def main():
    print "starting..."
    inv_s = connect_to_inverter()
    print "connected..."
    try:
        while True:
            data = read_data(inv_s,req_data)
            publish_data(data)
            time.sleep(10)
    except Exception as ex:
        template = "An exception of type {0} occured. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print message
    finally:
        inv_s.close()




main()
