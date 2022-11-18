import json
import os
import random as rd
import sys
import time
from datetime import datetime as dt

import ibmiotf.application
import ibmiotf.device
import requests as req

# Weather Details 
api_key = "f3907e39a60a6c7384c1221a8eb634af"
city = "Chennai"
country = "IN"
url_w=f"https://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={api_key}&units=metric"

# Cloud Details for weather
org_id_w = "fdrxjb"
device_type_w = "Weather"
device_id_w = "Weather_iot"
auth_method_w = "token"
auth_token_w = "Climate_123"


# Datas Needed
default_speed_limit = 60 # km/hrs
default_horn = True # Horn can be used

hour_now = int(str(dt.now()).split()[1].split(":")[0])
today = str(dt.now().strftime("%A"))

# Location Information
location_info = {
     "school" :  {
        "school_zone" : False, # Randomize Zones
        "active_time" : [7,17] # 7 am - 5 pm
        }
        ,
    "hospitals_near_by" :{
        'hospital_zone':False}, # Randomize Zones
    "speed_limit" : default_speed_limit,
    "horn" : default_horn
    }


def get_weather_details():    
    weather_req = req.get(url = url_w)
    weather_data = weather_req.json()

    climate = weather_data['weather'][0]['main']
    humidity = weather_data['main']['humidity']
    pressure = weather_data['main']['pressure']
    temperature = weather_data['main']['temp']
    temperature_min = weather_data['main']['temp_min']
    temperature_max = weather_data['main']['temp_max']
    temperature_feel = weather_data['main']['feels_like']
    temperature_average = (temperature_max+ temperature_min)/2
    data = {'climate':climate,'humidity':humidity,'temperature_average':temperature_average}
    return data

def myonpublishcallback_w(data):
    print(f"Published Temperature  = { data['temperature_average'] }, Humidity = {data['humidity']}, Climate = {data['climate']}")

def myonpublishcallback_s(speed_horn_data):
    print()
    print(f"Speed limit  = { speed_horn_data['speed'] }")
    print(f"Horn Info = {speed_horn_data['Horn']}")
    print(f"hospital_zone = {speed_horn_data['hospital_zone']}")
    print(f"school_zone = {speed_horn_data['school_zone']}")
    print(f"Time Now (in hrs) = {speed_horn_data['time_hour']}")
    print()

# Speed Limit and Horn Process

def speed_process(climate):
    #print(climatee)
    #print(location_info)
    if climate == 'Rain':
        if location_info['hospitals_near_by']['hospital_zone']:
            location_info['horn'] = False
            location_info['speed_limit'] = 15
        elif location_info['school']['school_zone']:
            if today == "Sunday":
                location_info['horn'] = default_horn
                location_info['speed_limit'] = 25
            else:
                if location_info['school']['active_time'][0] >= hour_now  and location_info['school']['active_time'][1]<=hour_now :
                    location_info['horn'] = False
                    location_info['speed_limit'] = 15
                else:
                    location_info['horn'] = default_horn
                    location_info['speed_limit'] = 25
        else:
            location_info["horn"] = default_horn
            location_info["speed_limit"] = 20
    elif climate == 'Snow' or climate == 'Smog' or climate == 'Fog':
        location_info['speed_limit'] = 10
        if location_info['hospitals_near_by']['hospital_zone']:
            location_info['horn'] = False
            
        elif location_info['school']['school_zone']:
            if today == "Sunday":
                location_info['horn'] = default_horn
            else:
                if location_info['school']['active_time'][0] >=hour_now  and location_info['school']['active_time'][1]<=hour_now :
                    location_info['horn'] = False
                else:
                    location_info['horn'] = default_horn
        else:
            location_info["horn"] = default_horn
    else:
        if location_info['hospitals_near_by']['hospital_zone']:
            location_info['horn'] = False
            location_info['speed_limit'] = 20
        elif location_info['school']['school_zone']:
            if today == "Sunday":
                location_info['horn'] = default_horn
                location_info['speed_limit'] = default_speed_limit
            else:
                if (location_info['school']['active_time'][0] >=hour_now ) and (location_info['school']['active_time'][1]<=hour_now) :
                    location_info['horn'] = False
                    location_info['speed_limit'] = 20
                else:
                    location_info['horn'] = default_horn
                    location_info['speed_limit'] = default_speed_limit
        else:
            location_info['horn'] = default_horn
            location_info['speed_limit'] = default_speed_limit


        

# Connecting to weather cloud
try:
    deviceOptions_w = {"org" : org_id_w, 
                     "type" : device_type_w,
                     "id" : device_id_w,
                     "auth-method" : auth_method_w,
                     "auth-token" : auth_token_w
                    }
    deviceCli_w = ibmiotf.device.Client(deviceOptions_w)
except Exception as e:
    print("Caught exception connecting device {str(e)}")
    sys.exit()
deviceCli_w.connect()


# Processing
while True:
    location_info['hospitals_near_by']['hospital_zone']=rd.choice([True,False])
    location_info['school']['school_zone']=rd.choice([True,False])
    climate_status=rd.choice(["Rain","Fog","Mist","Smog","Snow"])
    print(climate_status)
    data = get_weather_details()
    speed_process(climate_status)
    horn_data = "Usage of Horn Allowed" if location_info['horn'] else "Do not use the horn frequently"
    speed_horn_data = {"hospital_zone":location_info['hospitals_near_by']['hospital_zone'],"school_zone":location_info['school']['school_zone'],"time_hour":hour_now,"speed":location_info['speed_limit'],"Horn":horn_data}
    for key in speed_horn_data:
        data[key] = speed_horn_data[key]
    success_w = deviceCli_w.publishEvent("Current Weather","json",data,qos=1,on_publish = myonpublishcallback_w(data))
    print(data)
    if not success_w :
        time.sleep(1)
    time.sleep(3)
