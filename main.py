#!/usr/bin/env python3
import os
from flask import Flask, jsonify
from flask_cors import CORS
from discord_audio_controller import DiscordAudioController
from notifypy import Notify


notification = Notify()
notification.title = "Deafen server"
notification.message = "Discord deafen server started."
notification.send()


app = Flask(__name__)
CORS(app)


discord_controller = DiscordAudioController()


@app.route("/", methods=["GET"])
def index():
    """API information endpoint"""
    return jsonify({
        "service": "Discord Audio Controller",
        "version": "1.0.0",
        "endpoints": {
            "/kill": "GET - Kill the server",
            "/status": "GET - Get current Discord audio status",
            "/toggle": "POST - Toggle mute state for Discord streams",
            "/mute": "POST - Mute all Discord streams",
            "/unmute": "POST - Unmute all Discord streams"
        }
    })

@app.route("/kill", methods=["GET"])
def kill():
    app.logger.info("Killing Discord Audio Controller Web Server...")
    os._exit(0)
    return jsonify({
        "success": True,
        "message": "Server is shutting down."
    }), 200


@app.route("/status", methods=["GET"])
def get_status():
    """Get current status of Discord audio streams"""
    try:
        result = discord_controller.get_status()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error getting status: {str(e)}"
        }), 500


@app.route("/toggle", methods=["POST"])
def toggle_mute():
    """Toggle mute state for Discord streams"""
    try:
        result = discord_controller.toggle_mute()
        status_code = 200 if result["success"] else 404
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error toggling mute: {str(e)}"
        }), 500


@app.route("/mute", methods=["POST"])
def mute_discord():
    """Mute all Discord streams"""
    try:
        result = discord_controller.set_mute(True)
        status_code = 200 if result["success"] else 404
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error muting Discord: {str(e)}"
        }), 500


@app.route("/unmute", methods=["POST"])
def unmute_discord():
    """Unmute all Discord streams"""
    try:
        result = discord_controller.set_mute(False)
        status_code = 200 if result["success"] else 404
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error unmuting Discord: {str(e)}"
        }), 500


def create_app():
    """Application factory for the Discord Audio Controller"""
    return app


if __name__ == "__main__":
    print("Starting Discord Audio Controller Web Server...")
    print("Available endpoints:")
    print("  GET  /        - API information")
    print("  GET  /kill    - Kill the server")
    print("  GET  /status  - Get Discord audio status")
    print("  POST /toggle  - Toggle Discord mute state")
    print("  POST /mute    - Mute Discord")
    print("  POST /unmute  - Unmute Discord")
    print()
    
    # Run the Flask development server
    app.run(host="0.0.0.0", port=18498, debug=True, use_reloader=False)