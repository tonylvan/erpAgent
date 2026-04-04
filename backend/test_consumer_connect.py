# -*- coding: utf-8 -*-
"""测试消费者连接"""

import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from rtr_consumer_fixed import RTRSyncConsumer
import asyncio

async def test():
    c = RTRSyncConsumer()
    await c.connect()
    print("CONNECTED SUCCESS!")
    await c.disconnect()

asyncio.run(test())
