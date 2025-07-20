import subprocess
import re
from typing import List, Dict, Optional


class DiscordAudioController:
    """Controller for managing Discord audio streams through PulseAudio"""
    
    def __init__(self):
        self.discord_patterns = [
            r"WEBRTC VoiceEngine",
            r"Discord",
            r"discord",
            r"playStream",
            r"recStream"
        ]
    
    def _run_command(self, command: List[str]) -> Optional[str]:
        """Execute a command and return the result"""
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {' '.join(command)} - {e}")
            return None
    
    def _get_sink_inputs(self) -> List[Dict[str, str]]:
        """Get all PulseAudio sink-inputs (playback streams)"""
        output = self._run_command(["pactl", "list", "sink-inputs"])
        if not output:
            return []
        
        sinks = []
        current_sink = {}
        
        for line in output.split('\n'):
            line = line.strip()
            
            if line.startswith("Sink Input #"):
                if current_sink:
                    sinks.append(current_sink)
                sink_id = re.search(r'#(\d+)', line)
                current_sink = {
                    "id": sink_id.group(1) if sink_id else "",
                    "type": "sink-input"
                }
            
            elif "application.name" in line:
                match = re.search(r'application\.name = "([^"]*)"', line)
                if match:
                    current_sink["app_name"] = match.group(1)
            
            elif line.startswith("Mute:"):
                current_sink["muted"] = "yes" in line.lower()
            
            elif line.startswith("Volume:"):
                volume_match = re.search(r'(\d+)%', line)
                if volume_match:
                    current_sink["volume"] = int(volume_match.group(1))
        
        if current_sink:
            sinks.append(current_sink)
        
        return sinks
    
    def _get_source_outputs(self) -> List[Dict[str, str]]:
        """Get all PulseAudio source-outputs (recording streams)"""
        output = self._run_command(["pactl", "list", "source-outputs"])
        if not output:
            return []
        
        sources = []
        current_source = {}
        
        for line in output.split('\n'):
            line = line.strip()
            
            if line.startswith("Source Output #"):
                if current_source:
                    sources.append(current_source)
                source_id = re.search(r'#(\d+)', line)
                current_source = {
                    "id": source_id.group(1) if source_id else "",
                    "type": "source-output"
                }
            
            elif "application.name" in line:
                match = re.search(r'application\.name = "([^"]*)"', line)
                if match:
                    current_source["app_name"] = match.group(1)
            
            elif line.startswith("Mute:"):
                current_source["muted"] = "yes" in line.lower()
        
        if current_source:
            sources.append(current_source)
        
        return sources
    
    def _find_discord_streams(self) -> List[Dict[str, str]]:
        """Find all Discord-related streams (both playback and recording)"""
        all_streams = self._get_sink_inputs() + self._get_source_outputs()
        discord_streams = []
        
        for stream in all_streams:
            app_name = stream.get("app_name", "").lower()
            
            # Check against Discord patterns
            for pattern in self.discord_patterns:
                if pattern.lower() in app_name:
                    discord_streams.append(stream)
                    break
        
        return discord_streams
    
    def get_status(self) -> Dict:
        """Get current status of Discord streams"""
        discord_streams = self._find_discord_streams()
        
        if not discord_streams:
            return {
                "success": True,
                "found": False,
                "message": "No Discord streams found",
                "streams": []
            }
        
        streams_info = []
        for stream in discord_streams:
            stream_info = {
                "id": stream.get("id"),
                "type": "playback" if stream.get("type") == "sink-input" else "recording",
                "app_name": stream.get("app_name", "Unknown"),
                "muted": stream.get("muted", False),
                "volume": stream.get("volume", None)
            }
            streams_info.append(stream_info)
        
        return {
            "success": True,
            "found": True,
            "message": f"Found {len(discord_streams)} Discord streams",
            "streams": streams_info
        }
    
    def toggle_mute(self) -> Dict:
        """Toggle mute state for all Discord streams"""
        discord_streams = self._find_discord_streams()
        
        if not discord_streams:
            return {
                "success": False,
                "message": "No Discord streams found",
                "streams_affected": 0
            }
        
        # Determine target state based on first stream
        first_stream = discord_streams[0]
        is_currently_muted = first_stream.get("muted", False)
        target_state = "0" if is_currently_muted else "1"  # 0 = unmute, 1 = mute
        action = "unmuted" if is_currently_muted else "muted"
        
        results = []
        success_count = 0
        
        for stream in discord_streams:
            stream_id = stream.get("id")
            stream_type = stream.get("type")
            app_name = stream.get("app_name", "Unknown")
            
            if not stream_id or not stream_type:
                continue
            
            # Choose correct command based on stream type
            if stream_type == "sink-input":
                cmd = ["pactl", "set-sink-input-mute", stream_id, target_state]
                stream_desc = "playback"
            elif stream_type == "source-output":
                cmd = ["pactl", "set-source-output-mute", stream_id, target_state]
                stream_desc = "recording"
            else:
                continue
            
            result = self._run_command(cmd)
            stream_result = {
                "id": stream_id,
                "type": stream_desc,
                "app_name": app_name,
                "success": result is not None,
                "action": action
            }
            
            if result is not None:
                success_count += 1
            
            results.append(stream_result)
        
        return {
            "success": success_count > 0,
            "message": f"Successfully {action} {success_count}/{len(discord_streams)} streams",
            "action": action,
            "streams_affected": success_count,
            "total_streams": len(discord_streams),
            "results": results
        }
    
    def set_mute(self, mute: bool) -> Dict:
        """Set mute state for all Discord streams"""
        discord_streams = self._find_discord_streams()
        
        if not discord_streams:
            return {
                "success": False,
                "message": "No Discord streams found",
                "streams_affected": 0
            }
        
        target_state = "1" if mute else "0"  # 1 = mute, 0 = unmute
        action = "muted" if mute else "unmuted"
        
        results = []
        success_count = 0
        
        for stream in discord_streams:
            stream_id = stream.get("id")
            stream_type = stream.get("type")
            app_name = stream.get("app_name", "Unknown")
            
            if not stream_id or not stream_type:
                continue
            
            if stream_type == "sink-input":
                cmd = ["pactl", "set-sink-input-mute", stream_id, target_state]
                stream_desc = "playback"
            elif stream_type == "source-output":
                cmd = ["pactl", "set-source-output-mute", stream_id, target_state]
                stream_desc = "recording"
            else:
                continue
            
            result = self._run_command(cmd)
            stream_result = {
                "id": stream_id,
                "type": stream_desc,
                "app_name": app_name,
                "success": result is not None,
                "action": action
            }
            
            if result is not None:
                success_count += 1
            
            results.append(stream_result)
        
        return {
            "success": success_count > 0,
            "message": f"Successfully {action} {success_count}/{len(discord_streams)} streams",
            "action": action,
            "streams_affected": success_count,
            "total_streams": len(discord_streams),
            "results": results
        }
