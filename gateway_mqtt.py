#!/usr/bin/env python3
import os
import time
import json
import base64
import binascii
import subprocess
from paho.mqtt.client import Client

# ============ MQTT CONFIG ============
BROKER = "localhost"   # or use your Raspberry Pi IP, e.g., "192.168.0.108"
DATA_TOPIC = "esp/dump/data"
PROG_TOPIC = "esp/dump/progress"
CMD_TOPIC = "esp/dump/start"
BIN_PATH = "esp8266_flash.bin"

# ============ FUNCTION: Start Mosquitto ============
def ensure_mosquitto_running():
    """Check if mosquitto broker is running; start it if not."""
    try:
        result = subprocess.run(["pgrep", "-x", "mosquitto"], stdout=subprocess.PIPE)
        if result.returncode != 0:
            print("🔄 Mosquitto broker not running. Starting it...")
            subprocess.Popen(["sudo", "systemctl", "start", "mosquitto"])
            time.sleep(3)  # give it time to start
        else:
            print("✅ Mosquitto broker already running.")
    except Exception as e:
        print("⚠️ Could not verify/start mosquitto:", e)
        print("Make sure mosquitto is installed (sudo apt install mosquitto mosquitto-clients)")

# ============ FILE SETUP ============
open(BIN_PATH, "wb").close()  # clear any previous file
received = {}
total = None
from_offset = 0

# ============ CALLBACKS ============
def on_message(client, userdata, msg):
    global total, from_offset
    topic = msg.topic

    if topic == DATA_TOPIC:
        try:
            m = json.loads(msg.payload.decode())
            offset = m["offset"]
            length = m["len"]
            b64 = m["data"]
            crc = m["crc32"]

            raw = base64.b64decode(b64)
            if len(raw) != length:
                print(f"❌ Length mismatch at {offset}")
                return

            calc = binascii.crc32(raw) & 0xffffffff
            if f"{calc:08X}" != crc:
                print(f"❌ CRC mismatch at {offset}")
                return

            received[offset] = raw
            print(f"✅ Chunk {offset}-{offset+length} OK ({len(received)} chunks so far)")
        except Exception as e:
            print(f"⚠️ Error processing chunk: {e}")

    elif topic == PROG_TOPIC:
        try:
            p = json.loads(msg.payload.decode())
            if "total" in p:
                total = p["total"]
                from_offset = p.get("from", 0)
            if p.get("done"):
                with open(BIN_PATH, "r+b") as f:
                    cur = from_offset
                    while cur < from_offset + total:
                        chunk = received.get(cur)
                        if chunk is None:
                            print(f"❌ Missing chunk at {cur}")
                            return
                        f.seek(cur)
                        f.write(chunk)
                        cur += len(chunk)
                print(f"🎉 Done! Flash saved to {BIN_PATH}")
        except Exception as e:
            print(f"⚠️ Error handling progress message: {e}")

# ============ MAIN PROGRAM ============
def main():
    ensure_mosquitto_running()

    print("🚀 Connecting to MQTT broker...")
    client = Client()
    client.on_message = on_message
    client.connect(BROKER, 1883, 60)

    client.subscribe([(DATA_TOPIC, 1), (PROG_TOPIC, 1)])
    client.loop_start()

    time.sleep(2)
    print("📡 Requesting firmware dump from ESP8266...")
    cmd = json.dumps({"from": 0, "size": 0})  # ask ESP to send full flash
    client.publish(CMD_TOPIC, cmd, qos=1)

    try:
        input("🕐 Dumping... Press Enter to quit\n")
    except KeyboardInterrupt:
        pass

    client.loop_stop()
    client.disconnect()
    print("🛑 Gateway script stopped.")

if __name__ == "__main__":
    main()
