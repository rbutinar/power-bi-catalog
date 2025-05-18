import os
from dotenv import load_dotenv
import yaml

class Config:
    def __init__(self, env_path: str = ".env"):
        load_dotenv(env_path)
        self.tenant_id = os.getenv("TENANT_ID")
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.pbi_workspaces = os.getenv("PBI_WORKSPACES", "").split(",")
        self.top_n_models = int(os.getenv("TOP_N_MODELS", 5))

    @classmethod
    def from_yaml(cls, yaml_path: str):
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        instance = cls()
        for key, value in data.items():
            setattr(instance, key, value)
        return instance
