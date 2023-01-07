# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import sys
import traceback
import json
import logging
import requests
import math

from os.path import exists as fileExists
from asyncpushbullet import AsyncPushbullet, InvalidKeyError, PushbulletError, LiveStreamListener
from datetime import datetime, timedelta

API_KEY = ""
SL_TOKEN = ""
deviceNickname = 'scoreboard'
url = "https://api.streamlabswater.com"
EI = 1
EPBE = 2
EO = 3
logging.root.setLevel(logging.INFO)

def main():
    async def _run():
        try:
            async with AsyncPushbullet(API_KEY) as pb:
                headers = {
                    "Authorization" : f"Bearer {SL_TOKEN}"
                }
                res = requests.get(url + "/v1/locations", headers=headers)
                locationId = res.json()['locations'][0]['locationId']
    
                # List devices
                devices = await pb.async_get_devices()
                for dev in devices: 
                    logging.info(f"{dev}")
                pushDevice = await pb.async_get_device(nickname=deviceNickname)
                if pushDevice == None:
                    logging.info(f"Creating new device {deviceNickname}...")
                    pushDevice = await pb.async_new_device(deviceNickname)
                
                async with LiveStreamListener(pb, only_this_device_nickname=deviceNickname) as lsl:
                    logging.info(f"Listening for pushes to {deviceNickname} forever...")
                    async for push in lsl:
                       body = push['body']
                       d = datetime.now().strftime("%Y-%m-%dT01:00:00-05:00")
                       logging.info(f"Push received: \n {d}\t {body}")
                       fj = {"capacity": 1010, "resetDate": f"{d}"}
                       sj = {"capacity": 2450, "resetDate": f"{d}"}
                       if body.lower() != 'reset filter' and body.lower() != 'reset softener':
                           if fileExists("filter.json"):
                               with open('./filter.json', 'r') as openfile:
                                   filterObj = json.load(openfile)
                               fdate = filterObj['resetDate']
                               sinceReset1 = url + "/v1/locations/" + locationId + "/readings/water-usage?groupBy=day&startTime=" + fdate
                               res1 = requests.get(sinceReset1, headers=headers)
                               usage1 = sum(map(lambda x: float(x['volume']), res1.json()['readings']))
                               fRemaining = int(filterObj['capacity'] - (usage1*.72))
                               t1 = datetime.strptime(d, "%Y-%m-%dT01:00:00-05:00")
                               t2 = datetime.strptime(fdate, "%Y-%m-%dT01:00:00-05:00")
                               tdiff = t1 - t2
                               fdatediff = tdiff.days
                           else:
                               filterObj = "file not found"
                               fdatediff = '-1'
                               fRemaining = '-1'

                           if fileExists("softener.json"):
                               with open('./softener.json', 'r') as openfile:
                                   softenerObj = json.load(openfile)
                               sdate = softenerObj['resetDate']
                               sinceReset2 = url + "/v1/locations/" + locationId + "/readings/water-usage?groupBy=day&startTime=" + sdate
                               res2 = requests.get(sinceReset2, headers=headers)
                               usage2 = sum(map(lambda x: float(x['volume']), res2.json()['readings']))
                               sRemaining = int(softenerObj['capacity'] - (usage2*.72))
                               t1 = datetime.strptime(d, "%Y-%m-%dT01:00:00-05:00")
                               t2 = datetime.strptime(sdate, "%Y-%m-%dT01:00:00-05:00")
                               sdiff = t1 - t2
                               sdatediff = sdiff.days
                           else:
                               softenerObj = "file not found"
                               sdatediff = '-1'
                               sRemaining = '-1'
                           helpText = f"""Filter Status:
{filterObj}
{fdatediff} days since last regen
{fRemaining} gallons until next regen
to reset enter 'reset filter'

Softener Status:
{softenerObj}
{sdatediff} days since last regen
{sRemaining} gallons until next regen
to reset enter 'reset softener'"""
                           push = await pb.async_push_note(title="Hello", body=f"{helpText}")
                       if body.lower() == 'reset filter':
                           f = open("filter.json", "w")
                           f.write(json.dumps(fj))
                           f.close() 
                           push = await pb.async_push_note(title="Filter Reset", body=f"{json.dumps(fj)}")
                       if body.lower() == 'reset softener':
                           f = open("softener.json", "w")
                           f.write(json.dumps(sj))
                           f.close() 
                           push = await pb.async_push_note(title="Softener Reset", body=f"{json.dumps(sj)}")
  
        except InvalidKeyError as ke:
            logging.info(ke, file=sys.stderr)
            return EI

        except PushbulletError as pe:
            logging.info(pe, file=sys.stderr)
            return EPBE

        except Exception as ex:
            logging.info(ex, file=sys.stderr)
            traceback.print_tb(sys.exc_info()[2])
            return EO

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_run())

if __name__ == "__main__":
    if API_KEY == "":
        with open("./api_key.txt") as f:
            API_KEY = f.read().strip()
    if SL_TOKEN == "":
        with open("./streamlabs_token.txt") as f:
            SL_TOKEN = f.read().strip()
    sys.exit(main())
