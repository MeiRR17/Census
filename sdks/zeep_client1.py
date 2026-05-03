import functools
from logging import getLogger

from requests import Session
from requests.auth import HTTPBasicAuth
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from zeep import Client, Settings
from zeep.cache import SqliteCache
from zeep.transports import Transport

from api.conf_reader import meeting_place_config as config

disable_warnings(InsecureRequestWarning)

servers_config = config.get_servers()
services_config = config.get_services()

logger = getLogger()

class Zeep(object):
    clients = {}
    services = {}

    def __init__(self, name: str, ip: str, username: str, password: str):
        self.name = name
        for service_config in services_config:
            client = self._init_client(username,
                                       password,
                                       services_config[service_config]["wsdl"])
            service = self._init_service(client,
                                         services_config[service_config]["endpoint"],
                                         ip,
                                         services_config[service_config]["binding"])
            self.clients.update({service_config: client})
            self.services.update({service_config: service})
        logger.info("started connection to %s", ip)

    @staticmethod
    def _init_client(username: str, password: str, wsdl: str):
        session = Session()
        session.verify = False
        session.auth = HTTPBasicAuth(username, password)
        settings = Settings(strict=False)
        transport = Transport(cache=SqliteCache(), session=session, timeout=20)
        return Client(wsdl=wsdl, transport=transport, settings=settings)

    @staticmethod
    def _init_service(client: Client, endpoint: str, ip: str, binding: str):
        service_url = endpoint.format(ip)
        service = client.create_service(binding, service_url)
        return service

    def close_sessions(self):
        for client in self.clients.values():
            client.transport.session.close()


class Zeeper:

    current_zeep: Zeep
    current_ip = None

    def get_current_zeep(self):
        if not self.current_zeep:
            return
        return self.current_zeep

    def initialize_zeep(self, name: str):
        for server_config in servers_config:
            if server_config == name.split()[0]:
                name = f"{server_config} {servers_config[server_config]['ip']}"
                ip = servers_config[server_config]["ip"]
                self.current_ip = ip
                username = servers_config[server_config]["username"]
                password = servers_config[server_config]["password"]
                self.current_zeep = Zeep(name=name,
                                         ip=ip,
                                         username=username,
                                         password=password)
                break


@functools.cache
def get_zeeper():
    return Zeeper()
