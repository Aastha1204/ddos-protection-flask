from collections import defaultdict
import time, random, threading
from notifier import send_email_alert
from database import log_alert, get_user_email

traffic_data = {"requests": {}, "alerts": []}
request_counter = defaultdict(int)

THRESHOLD = 50  # Simulated threshold
WINDOW_SECONDS = 5
lock = threading.Lock()

def monitor_packets_once():
    """Simulate receiving packets for a short time window."""
    ips = ["192.168.1.2", "192.168.1.3", "10.0.0.5", "203.0.113.10"]
    for _ in range(20):
        src = random.choice(ips)
        count = random.randint(1, 15)
        request_counter[src] += count
        # update live traffic_data snapshot
        with lock:
            traffic_data["requests"][src] = request_counter[src]
        time.sleep(0.05)

def detect_ddos():
    # find any IPs crossing threshold and create alerts
    alerts_generated = []
    with lock:
        for ip, cnt in list(request_counter.items()):
            if cnt >= THRESHOLD:
                msg = f"High request rate detected from {ip}: {cnt} requests in last window."
                print("[ALERT]", msg)
                traffic_data["alerts"].append({"ip": ip, "message": msg, "count": cnt, "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')})
                log_alert(ip, msg)
                # attempt sending email alert (if email configured)
                if get_user_email():
                    send_email_alert(msg)
                alerts_generated.append(msg)
                # reset counter for that IP
                request_counter[ip] = 0
        # clear old request counts gradually
        # keep traffic_data.requests limited
        if len(traffic_data["alerts"]) > 50:
            traffic_data["alerts"] = traffic_data["alerts"][-50:]
    return alerts_generated

def start_monitoring():
    print("[INFO] Starting simulated DDoS monitor...")
    while True:
        monitor_packets_once()
        detect_ddos()
        # reset request_counter periodically
        time.sleep(WINDOW_SECONDS)
