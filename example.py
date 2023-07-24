import asyncio
from pprint import pprint

from pydiscovergy import Discovergy


async def main():
    discovergy = Discovergy(email="example@example.org", password="example")
    meters = await discovergy.meters()

    for meter in meters:
        if meter.full_serial_number == "1ESY1161978584":
            reading = await discovergy.meter_devices(meter.meter_id)
            pprint(reading)


asyncio.run(main())
