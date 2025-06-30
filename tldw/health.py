"""
Health check endpoints for Kubernetes readiness and liveness probes.
"""
import asyncio
import json
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Dict, Any

logger = logging.getLogger(__name__)


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check endpoints."""
    
    def do_GET(self):
        """Handle GET requests for health checks."""
        if self.path == "/health":
            self._handle_health()
        elif self.path == "/ready":
            self._handle_ready()
        else:
            self._handle_not_found()
    
    def _handle_health(self):
        """Handle liveness probe."""
        try:
            health_data = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "tldw-discord-bot"
            }
            self._send_json_response(200, health_data)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self._send_json_response(500, {"status": "unhealthy", "error": str(e)})
    
    def _handle_ready(self):
        """Handle readiness probe."""
        try:
            # Check if bot is ready (this would need to be implemented based on bot state)
            # For now, we'll assume the bot is ready if the health server is running
            ready_data = {
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "tldw-discord-bot"
            }
            self._send_json_response(200, ready_data)
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            self._send_json_response(503, {"status": "not_ready", "error": str(e)})
    
    def _handle_not_found(self):
        """Handle 404 responses."""
        self._send_json_response(404, {"error": "Not found"})
    
    def _send_json_response(self, status_code: int, data: Dict[Any, Any]):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        """Override to reduce logging noise."""
        # Only log errors, not every request
        if "404" in str(args) or "500" in str(args):
            logger.warning(f"Health check: {format % args}")


class HealthServer:
    """HTTP server for health checks."""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the health check server."""
        try:
            self.server = HTTPServer(('', self.port), HealthCheckHandler)
            self.thread = Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            logger.info(f"Health check server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start health check server: {e}")
            raise
    
    def stop(self):
        """Stop the health check server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("Health check server stopped")


# Global health server instance
health_server = HealthServer()


def start_health_server():
    """Start the health check server."""
    health_server.start()


def stop_health_server():
    """Stop the health check server."""
    health_server.stop()