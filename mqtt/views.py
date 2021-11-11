import paho.mqtt.client as mqtt

def on_log(client, userdata,level, buf):
    print("Log :- ", buf)
    print("Userdata :- ", userdata)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("flip/eggoz/#")
    # client.subscribe("flip/eggoz/863958048424746")
    # client.subscribe("flip/eggoz/863958048443779")

def on_publish(client, userdata, mid):
    print("In on_pub callback mid= ", mid)

def on_message(client, userdata, msg):
    # if(msg.topic=="homeauto/sensors/humidity"):
    print(str(msg.topic) + ":" + str(msg.payload))
    # print(msg.payload)

    # if(msg.topic=="flip/eggoz/863958048424746"):
    #     print("863958048424746 = "+str(msg.payload))
    # if(msg.topic=="flip/eggoz/863958048443779"):
    #     print("863958048443779 = "+str(msg.payload))


# client = mqtt.Client(client_id="FYYcB9")
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_log = on_log
# client.username_pw_set("iDTewh","57d54a")

client.connect("platform.myflip.io", 1883, 60, )
# client.connect("13.234.89.193", 1883, 60,)

# client.username_pw_set("xxxxx","abcd")



while 1:
    client.loop(10)
    # client.publish("flip/eggoz/863958048424746",payload=data,retain= True)
