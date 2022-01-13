import json

DEFAULT_CONFIG = {
    'DEBUG': True,
    'MAX_CONTENT_LENGTH': None,
    'MAX_COOKIE_SIZE': 4093,
}

SESSION_CONFIG = {
    'SESSION_COOKIE_NAME': 'session',
    'SESSION_COOKIE_DOMAIN': None,
    'SESSION_COOKIE_PATH': '/',
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SECURE': False,
    'SESSION_COOKIE_SAMESITE': None,
    'SECRET_KEY': '',
    'SESSION_COOKIE_MAXAGE': None
}

DEFAULT_CONFIG.update(SESSION_CONFIG)


class Config(dict):
    def __init__(self):
        super().__init__(DEFAULT_CONFIG)

    def from_object(self, object_):
        ''' Load configuration from python object i.e
        python class
        >> class MyConfig:
            Debug = True
            SECRET = "kjjd"
        >> conf.from_object(MyConfig)
        '''
        for attr in dir(object_):
            if attr.isupper():
                self[attr] = getattr(object_, attr, None)

    def from_dict(self, dict_):
        ''' Load configuration from python dict
        >> d = {'DEBUG':True}
        >> conf.from_dict(d)
        '''
        self.update(dict_)

    def from_json(self, json_file):
        '''load configuration from json
        the parameter can be path to json file
        or a file object
        >> conf = Config()
        >> file = '/path/to/conf.json'
        >> conf.from_json(file)

        '''
        if isinstance(json_file, (bytes, str)):
            with open(json_file,'r',encoding='utf-8') as file:
                config = file.read()
                self.update(json.loads(config))

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            return None
