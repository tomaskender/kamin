from datetime import date
import os
from schedule import every, repeat, run_pending
import time
import xmlrpc.client

@repeat(every().day)
def scrape():
    now = date.today()
    server = xmlrpc.client.ServerProxy(f"http://dataloader:{os.environ['RPC_PORT']}")
    towns = server.get_tracked_towns()
    for t in towns:
        delta = now - t.last_update
        if delta.days >= os.environ['UPDATE_DAYS_INTERVAL']:
            server.update(t._id)

while True:
    run_pending()
    time.sleep(24*60*60)