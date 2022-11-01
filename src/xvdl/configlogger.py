import logging
import logging.config
from pathlib import Path
import yaml

def setup_logger(config_path='configLog.yaml', default_level=logging.INFO):
    if Path(config_path).exists():
        with open(config_path, 'r') as f:
            try:
                config = yaml.safe_load(f.read())
                logging.config.dictConfig(config)
            except Exception as e:
                print(e)
                print('Error in Logging Configuration. Using default configs')
                logging.basicConfig(level=default_level)
    else:
        logging.basicConfig(level=default_level)
        print('Failed to load configuration file. Using default configs')
    
    return logging.getLogger("xvdl")