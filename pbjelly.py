# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import sys
import traceback
import datetime
import json
import logging

from asyncpushbullet import AsyncPushbullet, InvalidKeyError, PushbulletError, LiveStreamListener

API_KEY = ""
EI = 1
EPBE = 2
EO = 3
logging.root.setLevel(logging.INFO)

def main():
    async def _run():
        try:
            async with AsyncPushbullet(API_KEY) as pb:
                # List devices
                devices = await pb.async_get_devices()
                for dev in devices: 
                    logging.info(f"{dev}")

                async with LiveStreamListener(pb, only_this_device_nickname='scoreboard') as lsl:
                    logging.info("Awaiting pushes forever...")
                    async for push in lsl:
                       body = push['body']
                       d = datetime.datetime.now().strftime("%Y-%m-%dT01:00:00-05:00")
                       logging.info(f"Push received: \n {d}\t {body}")
                       fj = {"capacity": 1010, "resetDate": f"{d}"}
                       sj = {"capacity": 2450, "resetDate": f"{d}"}
                       if body != 'reset filter' and body != 'reset softener':
                           f = open("filter.json", "r").read()
                           s = open("softener.json", "r").read()
                           helpText = f"""Filter Status - to reset enter 'reset filter':
{f}

Softener Status - to reset enter 'reset softener':
{s}"""
                           push = await pb.async_push_note(title="Hello", body=f"{helpText}")
                       if body == 'reset filter':
                           f = open("filter.json", "w")
                           f.write(json.dumps(fj))
                           f.close() 
                           push = await pb.async_push_note(title="Filter Reset", body=f"{json.dumps(fj)}")
                       if body == 'reset softener':
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
    sys.exit(main())
