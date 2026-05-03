from configparser import ConfigParser

CONFIG_FILE = "api/conf_reader/cucm_cms_config.ini"
SECTION_SERVERS_PREFIX = "servers."
SECTION_SERVICES_PREFIX = "services."

config = ConfigParser()
config.read(CONFIG_FILE)


def get_config_sections_prefix(prefix: str) -> dict:
    configurations = {}
    for section in config.sections():
        if not section.startswith(prefix):
            continue
        configuration = {k: v for k, v in config[section].items()}
        configurations.update({section.removeprefix(prefix): configuration})
    return configurations


def get_servers():
    return get_config_sections_prefix(SECTION_SERVERS_PREFIX)


def get_services():
    return get_config_sections_prefix(SECTION_SERVICES_PREFIX)