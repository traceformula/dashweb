import memcache
import hashlib
import drdoom
from f import config

_memcache_key_len = 249

memcache_uri = config.get_memcache_uri()
memcache_timeout = config.get_memcache_timeout()

def strtoint(string):
    """Function to convert string to integer
    """
    return int(hashlib.md5(string).hexdigest(), 16)


class Memcache:
    __uri = memcache_uri
    __mc = list()
    __timeout = memcache_timeout


    def __init__(self, uri):
        self.mc = memcache.Client([uri])


    @classmethod
    def _get_instance(cls, id):
        if len(cls.__mc) == 0:
            for uri in cls.__uri:
                cls.__mc.append(cls(uri))
        return cls.__mc[cls._get_mcid(id)]


    @classmethod
    def _get_mcid(cls, id):
        val = strtoint(id) % len(cls.__uri)
        return strtoint(id) % len(cls.__uri)


    @classmethod
    def get(cls, key):
        key = cls._sanity(key)
        return cls._get_instance(key).mc.get(key)


    @classmethod
    def set(cls, key, value):
        key = cls._sanity(key)
        cls._get_instance(key).mc.set(key, value, cls.__timeout)


    @classmethod
    def dirty(cls, key):
        key = cls._sanity(key)
        cls._get_instance(key).mc.delete(key)


    @classmethod
    def _sanity(cls, key):
        if len(key) >= _memcache_key_len:
            key = key[:_memcache_key_len]
        return key



class Localcache:
    __instance = dict()

    def __init__(self):
        self.__data = dict()

    @classmethod
    def _get_instance(cls):
        window_id = drdoom.get_window_id()
        if window_id not in cls.__instance:
            cls.__instance[window_id] = cls()
        return cls.__instance[window_id]

    @classmethod
    def get(cls, key):
        return cls._get_instance().__data[key] if key in cls._get_instance().__data else None

    @classmethod
    def dirty(cls, key):
        del cls._get_instance().__data[key]

    @classmethod
    def set(cls, key, value):
        cls._get_instance().__data[key] = value

    @classmethod
    def append(cls, key, value):
        cls._get_instance().__data[key] += value

    @classmethod
    def cleanup(cls):
        del cls.__instance[drdoom.get_window_id()]

    @classmethod
    def get_dependencies(cls):
        return [i for i in cls._get_instance().__data]

