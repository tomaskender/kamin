from schedule import every, repeat, run_pending
import time

@repeat(every(2).weeks)
def scrape():
    print("Scraping...")
    return

while True:
    run_pending()
    time.sleep(60)