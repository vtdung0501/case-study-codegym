import opcua
import random
import time
server = opcua.Server()
server.set_endpoint("opc.tcp://127.0.0.1:12345")
server.register_namespace("Sensors")
object = server.get_objects_node()
tempsens = object.add_object(2,'Sensor')
temp = tempsens.add_variable(2,"Temperature",25)
press = tempsens.add_variable(2,"Pressure",500)
flow = tempsens.add_variable(2,"Flow",200)
server.register_namespace("Digital Signal")
digital_signal = object.add_object(3,"Digital Signal")
main_valve = digital_signal.add_variable(3,"Stage of main valve",False)
bulb_1 = digital_signal.add_variable(3,"Stage of bulb 1",False)
bulb_2 = digital_signal.add_variable(3,"Stage of bulb 2",False)
main_valve.set_writable()
bulb_1.set_writable()
bulb_2.set_writable()
try:
    temperature = 25.0
    pressure = 500.0
    flow_rate = 200.0
    print("Start Server")
    server.start()
    print("Server online")
    while True:
        temperature +=random.uniform(-1,1)
        temp.set_value(temperature)
        pressure +=random.uniform(-10,10)
        press.set_value(pressure)
        if main_valve.get_value() == True:
            flow_rate += random.uniform(-10,10)
            flow.set_value(flow_rate)
        else:
            flow.set_value(0)
        print(f'Temperature {temp.get_value()} °C')
        print(f"Pressure {press.get_value()} Kpa")
        print(f"Flow rate {flow.get_value()} L/min")        
        print(f"Main valve {main_valve.get_value()}")        
        print(f"Bulb 1 {bulb_1.get_value()}")        
        print(f"Bulb 2 {bulb_2.get_value()}")        

        time.sleep(1)
finally:
    server.stop()
    print("Server offline")




