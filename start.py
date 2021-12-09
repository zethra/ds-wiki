import uvicorn
import toml

from app import main, coordinator


IP = None
PORT = None
COORD = None
SERVERS = None


def read_config():
    return toml.load('config/config.toml')


if __name__ == '__main__':
    conf = read_config()
    IP = conf['this_ip']
    PORT = conf['port']
    COORD = conf['coordinator']
    replicas = conf['replicas']
    if IP == COORD:
        uvicorn.run(COORD.app, host=IP, port=PORT)
    else:
        uvicorn.run(main.app, host=IP, port=PORT)


