from flask import Flask, request, jsonify, send_from_directory
from blockchain import Blockchain
from time import time
import hashlib
import os

app = Flask(__name__)
bc = Blockchain()

@app.route("/join", methods=["POST"])
def join():
    data = request.get_json()
    device_id = data.get("device_id")
    firmware_hash = data.get("firmware_hash")
    
    if not device_id or not firmware_hash:
        return jsonify({"error": "Missing required fields"}), 400
    
    # Check if device is already in the chain
    for block in bc.chain:
        block_data = block.get("data")
        if isinstance(block_data, dict) and block_data.get("device_id") == device_id:
            # If firmware hash matches
            if block_data.get("firmware_hash") == firmware_hash:
                return jsonify({
                    "status": block_data.get("status", "pending"),
                    "message": "Device already registered",
                    "block_index": block["index"]
                })
    
    # Device not found — create new pending block
    data["status"] = "pending"
    new_block = bc.create_block(bc.chain[-1]["hash"], data)
    return jsonify({
        "status": "registered (pending)",
        "block_index": new_block["index"],
        "message": "New device registered"
    })

@app.route("/approve/<int:index>", methods=["POST"])
def approve(index):
    try:
        print(f"Approval request received for block index: {index}")
        print(f"Current chain length: {len(bc.chain)}")
        
        if index < 0 or index >= len(bc.chain):
            print(f"Invalid block index: {index}")
            return jsonify({"error": f"Invalid block index: {index}"}), 404
        
        block = bc.chain[index]
        print(f"Block data: {block}")
        
        if not isinstance(block.get('data'), dict):
            print(f"Block data is not a dictionary: {type(block.get('data'))}")
            return jsonify({"error": "Block has no device data"}), 400
        
        if 'device_id' not in block['data']:
            print("Block data missing device_id")
            return jsonify({"error": "Block data missing device_id"}), 400
        
        # Update the block status
        old_status = block['data'].get('status', 'unknown')
        block['data']['status'] = "approved"
        print(f"Status updated from '{old_status}' to 'approved'")
        
        return jsonify({
            "status": "approved", 
            "block": block,
            "message": "Device approved successfully"
        })
        
    except Exception as e:
        print(f"Error in approve function: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route("/chain", methods=["GET"])
def chain():
    return jsonify({
        "length": len(bc.chain),
        "chain": bc.chain
    })

@app.route("/")
def index():
    return send_from_directory('.', 'dashboard_pro.html')

@app.route("/dashboard")
def dashboard():
    return send_from_directory('.', 'dashboard_pro.html')

# Add CORS headers for external access
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

@app.route("/add_test_device", methods=["POST"])
def add_test_device():
    """Add a test device for debugging purposes"""
    test_data = {
        "device_id": f"TEST_DEVICE_{len(bc.chain)}",
        "firmware_hash": f"test_hash_{hashlib.md5(str(time()).encode()).hexdigest()[:8]}",
        "status": "pending"
    }
    
    new_block = bc.create_block(bc.chain[-1]["hash"], test_data)
    return jsonify({
        "status": "test device added",
        "block": new_block
    })

if __name__ == '__main__':
    print("Starting LightChain IoT Dashboard...")
    print(f"Dashboard will be available at: http://0.0.0.0:5000")
    print(f"Local access: http://localhost:5000")
    
    # Add a test device on startup for debugging
    test_data = {
        "device_id": "TEST_DEVICE_001",
        "firmware_hash": "abc123def456",
        "status": "pending"
    }
    bc.create_block(bc.chain[-1]["hash"], test_data)
    print("Added test device for debugging")
    
    # Get local IP for network access
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"Network access: http://{local_ip}:5000")
    except:
        pass
    
    app.run(host="0.0.0.0", port=5000, debug=True)
