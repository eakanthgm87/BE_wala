import os
import json
import uuid
from datetime import datetime

class StateManager:
    """
    Tracks all deployments for easy destruction
    """

    def __init__(self):
        self.state_file = os.path.expanduser("~/.ai-deploy/state.json")
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        self.state = self.load_state()

    def save_deployment(self, project_name, deployment_data):
        """Save deployment info for later destruction"""

        if project_name not in self.state:
            self.state[project_name] = []

        self.state[project_name].append({
            'timestamp': datetime.now().isoformat(),
            'deployment_id': str(uuid.uuid4()),
            **deployment_data
        })

        self.save_state()

    def get_deployment(self, project_name, deployment_id=None):
        """Get deployment info"""

        if project_name not in self.state:
            return None

        if deployment_id:
            for d in self.state[project_name]:
                if d['deployment_id'] == deployment_id:
                    return d
        else:
            return self.state[project_name][-1]  # Latest

    def list_deployments(self, project_name=None):
        """List all deployments"""

        if project_name:
            return self.state.get(project_name, [])

        all_deployments = []
        for proj, deployments in self.state.items():
            for d in deployments:
                d['project'] = proj
                all_deployments.append(d)

        return all_deployments

    def remove_deployment(self, project_name, deployment_id=None):
        """Remove from state after destruction"""

        if deployment_id:
            self.state[project_name] = [
                d for d in self.state[project_name]
                if d['deployment_id'] != deployment_id
            ]
        else:
            self.state[project_name] = []

        self.save_state()

    def load_state(self):
        """Load state from file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}

    def save_state(self):
        """Save state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state: {e}")