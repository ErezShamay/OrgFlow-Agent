from datetime import datetime


class AgentLogger:
    def info(self, message: str):
        self._log("INFO", message)

    def warning(self, message: str):
        self._log("WARNING", message)

    def error(self, message: str):
        self._log("ERROR", message)

    def _log(self, level: str, message: str):
        timestamp = datetime.now().isoformat(timespec="seconds")
        print(f"[{timestamp}] [{level}] {message}")