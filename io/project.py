
# geofea/io/project.py
from dataclasses import dataclass, asdict
import json

@dataclass
class ProjectConfig:
    version: str = "0.1.0"
    # add fields as needed

def to_json(cfg: ProjectConfig) -> str:
    return json.dumps(asdict(cfg), indent=2)

def from_json(s: str) -> ProjectConfig:
    d = json.loads(s); return ProjectConfig(**d)
