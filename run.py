import os
import schedule
import time
from scraper.NaverMailWorker import NaverMailWorker

if __name__ == "__main__":
    id = ""
    password = ""
    sec = 60
    mail = NaverMailWorker(id, password)

    schedule.every(sec).seconds.do(mail.run)
    while True:
        schedule.run_pending()
        time.sleep(1)
