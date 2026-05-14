class WorkflowStore:
    def __init__(self):
        self.store = {}

    def save(self, run_id, workflow_data):
        self.store[run_id] = workflow_data

    def get(self, run_id):
        return self.store.get(run_id)

    def delete(self, run_id):
        if run_id in self.store:
            del self.store[run_id]