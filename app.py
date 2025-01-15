from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import requests

app = Flask(__name__)

# Configuration
WEBHOOK_URL = "https://discord.com/api/webhooks/1329019833618006047/4rx3t6WNg1aqS2IOnADZSuwliTVMnKR9XFc8Mwy2PonGiKqwNzQ3IuwIB-g_s4mB6PK1"
MAX_MISSED_PINGS = 2  # Number of missed pings to consider server offline
PING_INTERVAL = 60  # Time in seconds between pings

# State Variables
last_ping_time = datetime.utcnow()
server_offline = False
offline_start_time = None


def send_webhook_message(content):
    """Send a message to Discord via webhook."""
    payload = {"content": content}
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"Webhook message sent successfully: {content}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send webhook message: {e}")


@app.route('/ping', methods=['GET'])
def ping():
    """Endpoint to receive pings."""
    global last_ping_time, server_offline, offline_start_time
    last_ping_time = datetime.utcnow()

    if server_offline:
        # Server is back online; calculate downtime
        downtime = datetime.utcnow() - offline_start_time
        downtime_str = str(downtime).split('.')[0]  # Remove microseconds
        send_webhook_message(f"✅ **Server Status:** Online\n🕒 **Downtime Duration:** {downtime_str}")
        server_offline = False

    return jsonify({"message": "Pong", "timestamp": last_ping_time.isoformat()})


@app.route('/check', methods=['GET'])
def check_server_status():
    """Endpoint to check if the server has missed pings."""
    global server_offline, offline_start_time
    current_time = datetime.utcnow()
    time_since_last_ping = current_time - last_ping_time

    if time_since_last_ping > timedelta(seconds=PING_INTERVAL * MAX_MISSED_PINGS):
        if not server_offline:
            # Mark server as offline and send a webhook message
            offline_start_time = datetime.utcnow()
            server_offline = True

            error_reason = (
                "🔌 **Possible Reasons:**\n"
                "1. No network connectivity.\n"
                "2. The server process was killed.\n"
                "3. Unexpected system shutdown or crash.\n\n"
                "⚠️ **Action Required:** Please investigate the server environment immediately."
            )
            send_webhook_message(
                f"❌ **Server Status:** Offline\n"
                f"📅 **Detected At:** {offline_start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                f"{error_reason}"
            )

    return jsonify({"server_offline": server_offline, "last_ping": last_ping_time.isoformat()})


@app.route('/webhook-test', methods=['POST'])
def webhook_test():
    """Endpoint to manually trigger a webhook for testing."""
    data = request.get_json()
    content = data.get("content", "Test message from /webhook-test endpoint.")
    send_webhook_message(content)
    return jsonify({"status": "Webhook sent", "content": content})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
