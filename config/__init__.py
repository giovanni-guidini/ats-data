from typing import Dict, List, TypeVar
from yaml import safe_load   

T = TypeVar('T')  

def load_config() -> Dict:
    # TODO: Allow for specification of config file
    # TODO: Add YAML Schema and validation to config
    with open('config/local_config.yml', 'r') as fd:
        config = safe_load(fd)
    return config

def get_config(config_obj: Dict, *path: List[str], default: T = None) -> T:
    curr = config_obj
    for key in path:
        if key not in curr:
            return default
        curr = curr[key]
    return curr

