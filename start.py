"""
Entry script for the program.
"""

import uvicorn
import toml

from app import main, coordinator



def read_config():
    """
    Load the config from the TOML file at /config/config.toml
    :return: Dictionary with the config information.
    """
    return toml.load('config/config.toml')


"""
Entry point to run the program. Loads the config data and launches as a coordinator if this
server's IP matches the coordinator's IP. Otherwise launches as a data server.
"""
if __name__ == '__main__':
    conf = read_config()
    IP = conf['this_ip']
    PORT = conf['port']
    COORD = conf['coordinator']
    REPLICAS = conf['replicas']
    if IP == COORD:
        uvicorn.run(coordinator.app, host=IP, port=PORT)
    else:
        uvicorn.run(main.app, host=IP, port=PORT)


