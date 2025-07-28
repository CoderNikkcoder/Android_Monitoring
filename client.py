#!/usr/bin/env python3
# Simple device monitoring client - v1.0
# Created by [Your Name] - for personal use

import socket
import subprocess
import json
import platform
import shutil
import time
from random import randint  # For dummy data

# Configuration - edit these before use!
SERVER_IP = "192.168.1.100"  # Change to your server IP
PORT = 5001
CHECK_INTERVAL = 60  # seconds between reports

# Helper to convert bytes to GB (because who remembers the math?)
def bytes_to_gb(bytes_amount):
    gb = bytes_amount / (1024 ** 3)
    return round(gb, 2)  # Keep it to 2 decimal places

# Get local IP - the "talk to Google DNS" trick
def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Google DNS
            return s.getsockname()[0]
    except Exception as e:
        print(f"IP check failed: {e}")
        return "N/A"

# Battery check - Termux specific (commented out for GitHub safety)
def check_battery():
    """
    Actual Termux version:
    out = subprocess.check_output(["termux-battery-status"], timeout=5)
    return json.loads(out)
    """
    # Dummy data for public version
    return {
        "percentage": randint(20, 100),
        "status": "charging" if randint(0,1) else "discharging"
    }

# RAM usage - reading from /proc/meminfo
def get_memory_usage():
    mem_stats = {"error": "Couldn't read memory info"}
    
    try:
        with open("/proc/meminfo") as f:
            mem_data = f.read()
            
        # Extract values (this always feels like parsing magic)
        total = int(mem_data.split("MemTotal:")[1].split()[0]) * 1024
        available = int(mem_data.split("MemAvailable:")[1].split()[0]) * 1024
        
        mem_stats = {
            "total_gb": bytes_to_gb(total),
            "used_gb": bytes_to_gb(total - available),
            "percent_used": round((total - available) / total * 100, 1)
        }
        
    except Exception as e:
        print(f"Memory check failed: {e}")
    
    return mem_stats

# Storage check - basic disk usage
def check_disk_space(path="/"):
    try:
        usage = shutil.disk_usage(path)
        return {
            "total_gb": bytes_to_gb(usage.total),
            "used_gb": bytes_to_gb(usage.used),
            "free_gb": bytes_to_gb(usage.free),
            "percent_used": round(usage.used / usage.total * 100, 1)
        }
    except Exception as e:
        print(f"Disk check failed for {path}: {e}")
        return {"error": "Disk info unavailable"}

# Main reporting function
def generate_report():
    return {
        "timestamp": int(time.time()),
        "ip": get_local_ip(),
        "device": {
            "name": platform.node()[:15],  # Truncate long hostnames
            "os": platform.system(),
            "release": platform.release()
        },
        "resources": {
            "memory": get_memory_usage(),
            "storage": check_disk_space(),
            "battery": check_battery()
        },
        "location": {  # Placeholder - real version would use Termux API
            "status": "Location disabled in public version"
        }
    }

# Main loop - keeps running forever
if __name__ == "__main__":
    print(f"Starting device monitor (reporting to {SERVER_IP}:{PORT})")
    
    while True:
        try:
            # Create and send report
            report = generate_report()
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((SERVER_IP, PORT))
                sock.sendall(json.dumps(report).encode())
            
            print(f"Report sent at {time.ctime()}")
            
        except Exception as e:
            print(f"⚠️ Report failed: {type(e).__name__} - {e}")
        
        # Wait for next interval (with countdown)
        print(f"Next report in {CHECK_INTERVAL} seconds...", end="\n\n")
        time.sleep(CHECK_INTERVAL)
