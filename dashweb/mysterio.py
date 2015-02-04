import base64
import drdoom
import inspect
from f import config
from cache import Memcache, Localcache
from rumor import Rumor

# this is the password that we will use as a key to scramble and encode object key
_salt = "SN7ueeBDs7eSS4oDfGIphuBTlVoBqp2RxMLPxf"

# divider constant that will be use to seperate between encoded arguments
_d1 = "%20"
_d2 = "%30"
_d3 = "%40"
_empty = "%50"
_int = "%60"
_long = "%70"
_bool = "%80"

# types of cache use
_function = "function"
_unit = "unit"
_list = "list"

def local_set(key, value):
    Localcache.set(key, value)

def local_append(key, value):
    Localcache.append(key, value)

def local_get(key):
    return Localcache.get(key)

def cleanup():
    val = Localcache.get_dependencies()
    content = ','.join(val)
    Memcache.set(drdoom.get_window_id(), content)
    Localcache.cleanup()
    drdoom.cleanup()

def encode(val, key=_salt):
    """Function to encode string
    """
    encoded_chars = []
    for i in range(len(val)):
        key_c = key[i % len(key)]
        encoded_c = chr((ord(val[i]) + ord(key_c)) % 256)
        encoded_chars.append(encoded_c)
    encoded_string = "".join(encoded_chars)
    return base64.urlsafe_b64encode(encoded_string)

def decode(val, key=_salt):
    """Function to decode encoded string
    """
    val = base64.urlsafe_b64decode(val)
    encoded_chars = []
    for i in range(len(val)):
        key_c = key[i % len(key)]
        encoded_c = chr((ord(val[i]) + 256 - ord(key_c)) % 256)
        encoded_chars.append(encoded_c)
    encoded_string = "".join(encoded_chars)
    return encoded_string

class Mysterio(object):
    """ Facade class of caching
    """
    __obj = dict()

    @classmethod
    def learn(cls, cast=_function, subscribe=None):
        if cast == _function:
            return _MysterioFunction()
        elif cast == _unit:
            return _MysterioUnit(subscribe)
        elif cast == _list:
            return _MysterioList(subscribe)

    @classmethod
    def register(cls, obj):
        cls.__obj[obj.__name__] = obj

    @classmethod
    def render(cls, id):
        obj, a, kw = id.split(_d1)
        args = (cls.decode(i) for i in a.split(_d2)) if a != _empty else ()
        kwargs = dict(z.split(_d3) for z in kw.split(_d2)) if kw != _empty else None
        kwargs = dict((cls.decode(z), cls.decode(kwargs[z])) for z in kwargs) if kwargs is not None else {}
        renderer = cls.__obj[obj]
        return renderer.render(*args, **kwargs)

    @classmethod
    def decode(cls, val):
        v = decode(val)
        v = int(v[3:]) if _int == v[0:3] else \
            long(v[3:]) if _long == v[0:3] else \
            (True if v[3:] == "True" else False) if _bool == v[0:3] else v
        return v

    @classmethod
    def get(cls, key):
        val = Localcache.get(key)
        if not val:
            val = Memcache.get(key)
        return val

    @classmethod
    def set(cls, key, val):
        Localcache.set(key, val)
        Memcache.set(key, val)

    @classmethod
    def local_get(cls, key):
        val = Localcache.get(key)
        return val

    @classmethod
    def local_pop(cls, key):
        val = Localcache.get(key)
        Localcache.dirty(key)
        return val

    @classmethod
    def local_set(cls, key, val):
        Localcache.set(key, val)

class _MysterioBase(object):

    def run(self, func, args, kwargs, id):
        """function to get the value of request
        """
        val = Localcache.get(id)
        source = "localcache"
        if not val:
            val = Memcache.get(id)
            if not val:
                source = "db"
                val = func(*args, **kwargs)
                Memcache.set(id, val)
            else:
                source = "memcache"
            Localcache.set(id, val)
        return val, source

    @classmethod
    def encode(cls, obj):
        t = type(obj)
        if obj is None:
            v = encode('')
        elif t is str or t is unicode:
            v = encode(str(obj))
        elif t is bool:
            v = encode(_bool + str(obj))
        elif t is int or t is long:
            v = encode(_long + str(obj))
        elif t is tuple or t is list:
            v = _d2.join([cls.encode(i) for i in obj])
        elif t is dict:
            v = _d2.join([_d3.join([cls.encode(i), cls.encode(obj[i])]) for i in obj])
        return v

    @classmethod
    def get_id(cls, obj, args, kwargs):
        f = [obj.__name__]
        f += [obj.__module__] if hasattr(obj, '__module__') else []
        f += [cls.encode(args)] if args is not None else [_empty]
        f += [cls.encode(kwargs)] if kwargs is not None else [_empty]
        return _d1.join(f)

class _MysterioFunction(_MysterioBase):

    def __init__(self):
        self.dep = list()

    def __call__(self, func):
        self.func = func

        @Rumor.track_mysterio()
        def fn(*args, **kwargs):
            id = _MysterioFunction.get_id(self.func, args, kwargs)
            val, source = self.run(func, args, kwargs, id)
            setattr(fn, "source", source)
            return val

        #@Rumor.track_mysterio('dirty')
        def dirty(*args, **kwargs):
            for func in self.dep:
                func(*args, **kwargs)
            id = _MysterioFunction.get_id(self.func, args, kwargs)
            setattr(dirty, 'id', id)
            Memcache.dirty(id)

        def on_dirty(func):
            self.dep.append(func)

        fn.__name__ = func.__name__
        dirty.__name__ = func.__name__
        setattr(fn, 'dirty', dirty)
        setattr(fn, 'on_dirty', on_dirty)
        setattr(fn, "render", fn)
        setattr(fn, "argspec", inspect.getargspec(func))

        Mysterio.register(fn)
        return fn

class _MysterioComponent(_MysterioBase):

    def __init__(self, subscribe):
        self.subscribe = subscribe

    def call(self, cls):
        cls.dep = list()
        cls.subscription = None

        @classmethod
        def new_get(cls, *args, **kwargs):
            id = _MysterioUnit.get_id(cls, args, kwargs)
            val, source = self.run(cls.get_html, args, kwargs, id)
            setattr(fn, "source", source)
            return val

        @classmethod
        def get_html(cls, *args, **kwargs):
            return cls(**kwargs).h

        def new_init(func):
            def init_func(self, *args, **kwargs):
                self.id =_MysterioUnit.get_id(cls, args, kwargs)
                self.data = cls.subscription.im_func(*args, **kwargs)
                func(self, *args, **kwargs)
            return init_func

        @classmethod
        def dirty(*args, **kwargs):
            for obj in cls.dep:
                obj(*args, **kwargs)
            id = _MysterioUnit.get_id(cls, args, kwargs)
            Memcache.dirty(id)

        @classmethod
        def on_dirty(cls, obj):
            cls.dep.append(obj)

        @classmethod
        def subscribe(cls, obj):
            obj.on_dirty(cls.dirty)
            cls.subscription = obj

        setattr(cls, "init", new_init(cls.init))
        setattr(cls, "get_html", get_html)
        setattr(cls, "get", new_get)
        setattr(cls, "render", new_get)
        setattr(cls, "dirty", dirty)
        setattr(cls, "on_dirty", on_dirty)
        setattr(cls, "subscribe", subscribe)

        Mysterio.register(cls)
        cls.subscribe(self.subscribe)

class _MysterioUnit(_MysterioComponent):

    def __call__(self, cls):
        self.call(cls)
        return cls

class _MysterioList(_MysterioComponent):

    def __call__(self, cls):
        self.call(cls)
        return cls


