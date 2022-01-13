import logging

from .main import Environment, FileLoader, Template, TemplateLoader
from .nodes import Node

logger = logging.getLogger('glass.template')
stream = logging.StreamHandler()
stream.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s: %(message)s',
                              datefmt='%d/%m/%Y %H:%M:%S %p')
stream.setFormatter(formatter)
logger.addHandler(stream)
