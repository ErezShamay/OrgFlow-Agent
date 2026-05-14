from datetime import datetime


class WorkflowHistory:
    def __init__(self):
        self.runs = []

    def add_run(self, run_data: dict):
        self.runs.append({
            **run_data,
            "created_at": datetime.now().isoformat()
        })

    def get_all(self):
        return self.runs