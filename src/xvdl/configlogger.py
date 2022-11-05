import logging
import logging.config
import yaml
from pathlib import Path


def setup_logger(config_file='configLog.yaml', default_level=logging.INFO):
    """Cargamos la configuración para el logger"""
    config_path = Path(__file__).parent / config_file

    if Path(config_path).exists():

        with open(config_path, 'r') as f:
            try:
                # Cargamos los datos del archivo yaml
                config = yaml.safe_load(f.read())
                
                # Seteamos la configuración al logging
                logging.config.dictConfig(config)

            except Exception as e:
                print(e)
                print('Error in Logging Configuration. Using default configs')
                logging.basicConfig(level=default_level)

    else:
        logging.basicConfig(level=default_level)
        print('Failed to load configuration file. Using default configs')

    # Regresamos el logger con la configuración cargada.
    return logging.getLogger("xvdl")
