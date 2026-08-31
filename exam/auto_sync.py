import time
import os
import sys

def run_sync():
    os.system("python sync_direct.py")

if __name__ == '__main__':
    print("🔄 سرویس همگام‌سازی خودکار شروع شد...")
    print("⏳ هر ۳۰ ثانیه یکبار چک میکنه...")
    
    while True:
        run_sync()
        time.sleep(30)  # هر ۳۰ ثانیه یکبار
