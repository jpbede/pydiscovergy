import asyncio
import json
from pprint import pprint

import pydiscovergy
from pydiscovergy.authentication import BasicAuth


async def main():
    dis = pydiscovergy.Discovergy(email="demo@discovergy.com", password="demos", authentication=BasicAuth())

    meters = await dis.get_meters()

    for meter in meters:
        pprint(meter)
        if meter.additional.get("fullSerialNumber") == "7ELS8135823805":
            reading = await dis.get_last_reading(meter.get_meter_id())
            pprint(reading)

asyncio.run(main())
