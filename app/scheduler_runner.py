import schedule
import time
import datetime
import subprocess
from stock_monitor import update_global_price_cache
import pytz

print("✅ Scheduler script has started running...")

# --- NEW: Run the stock list insertion script once on startup ---
try:
    print("📥 Inserting initial stock list...")
    subprocess.run(["python", "scripts/insert_stock_list.py"], check=True)
    print("✅ insert_stock_list.py completed successfully.")
except subprocess.CalledProcessError as e:
    print(f"❌ Error running insert_stock_list.py: {e}")
# ----------------------------------------------------------------

# Timezone setup
EST = pytz.timezone("US/Eastern")

def is_trading_day():
    now = datetime.datetime.now(EST)
    return now.weekday() < 5  # Monday to Friday

def run_price_update():
    if is_trading_day():
        now = datetime.datetime.now(EST).strftime("%m/%d/%Y %I:%M:%S %p")
        print(f"[{now} EST] ✅ Updating stock prices...")
        update_global_price_cache()
    else:
        print("⏳ Weekend – no update needed.")

# Schedule every 30 minutes between 9:30 AM and 4:00 PM EST
times_to_run = [
    "09:30", "10:00", "10:30", "11:00", "11:30", "12:00",
    "12:30", "13:00", "13:30", "14:00", "14:30", "15:00",
    "15:30", "16:00"
]

for t in times_to_run:
    schedule.every().day.at(t).do(run_price_update)

print("📅 Stock price update scheduler is running... (EST Time)")
print("⏳ Entering scheduling loop...")

while True:
    schedule.run_pending()
    time.sleep(1)
