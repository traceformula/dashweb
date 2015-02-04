import pyramid.threadlocal as t
import random
import uuid

_uid = 'uid'
_window_id = 'window_id'
_post = 'post'
_get = 'get'
_islogin = 'islogin'
_window_error = 'window_error'
_window_notif = 'window_notif'
_back_state = 'back_state'
_back_state_max = 1500
_separator = ',,,'



def refresh():
    exception = [_islogin, _uid, _window_id, _window_error, _window_notif, _back_state]
    s = session()
    for key in s:
        if key not in exception:
            del s[key]


def request():
    try:
        request = t.get_current_request()
    except ErrorRunInConsole, e:
        request = ConsoleRequest()
    request = ConsoleRequest() if request is None else request
    return request


def referer():
    return request().referer


def host():
    return request().host


def path():
    return request().path


def path_url():
    return request().path_url


def user_agent():
    try:
        from user_agents import parse
    except:
        return None
    return parse(request().user_agent)


def is_mobile():
    return user_agent().is_mobile if user_agent() else False


def is_tablet():
    return user_agent().is_tablet if user_agent() else False


def is_touch_capable():
    return user_agent().is_touch_capable if user_agent() else False


def is_pc():
    return user_agent().is_pc if user_agent() else True


def is_bot():
    return user_agent().is_bot if user_agent() else False


def session():
    return request().session


def islogin():
    islogin = get(_islogin)
    islogin = 0 if islogin is None else islogin
    if not islogin:
        if get_uid():
            set(_islogin, 1)
            islogin = True
    return islogin


def login(uid):
    set(_islogin, 1)
    set_uid(uid)


def logout():
    set(_islogin, 0)
    set_uid(False)


def get_uid():
    s = session()
    if _uid not in s:
        s[_uid] = False
    return s[_uid]


def set_uid(uid):
    s = session()
    s[_uid] = uid


def get(key, default=None):
    s = session()
    return default if key not in s else s[key]


def set(key, value):
    s = session()
    s[key] = value


def delete(key):
    s = session()
    if key in s:
        del s[key]


def pop(key, default=None):
    value = get(key, default=default)
    delete(key)
    return value


def get_window_id():
    s = session()
    if _window_id not in s:
        s[_window_id] = str(uuid.uuid4())
    return s[_window_id]


def get_user_ip():
    return request().client_addr


def cleanup():
    s = session()
    if _window_id in s:
        del s[_window_id]


def set_error(message):
    set(_window_error, message)


def get_error():
    return pop(_window_error)


def set_notif(message):
    set(_window_notif, message)


def current_url():
    c_path = path()
    c_host = host()
    if 'localhost' not in c_host and '127.0.0.1' not in c_host and 'dashsell' in c_host:
        if c_path.startswith('/shopfront_public/'):
            subdomain = c_path.split('/')[2]
            c_path = '/'.join([''] + c_path.split('/')[3:])
            if 'staging' in c_host:
                c_host = ''.join(['http://', subdomain, '.staging.dashsell.com'])
            else:
                c_host = ''.join(['http://', subdomain, '.dashsell.com'])
        else:
            if 'staging' in c_host:
                c_host = 'http://staging.dashsell.com'
            else:
                c_host = 'http://www.dashsell.com'
        url = ''.join([c_host, c_path])
    else:
        url = ''.join([c_path])

    return url


def get_notif():
    return pop(_window_notif)



###################################  DRDoom for History Handler #########################################


def pop_history():
    History.pop()


def peek_history():
    result = History.peek()
    return result


class History:

    query = '?history=1' 

    @classmethod
    def push_state(cls, home=False):
        return _Pusher(home)

    @classmethod
    def pop(cls):
        states = get(_back_state, default=False)
        if states:
            states = states.split(_separator)
            if states[-1] != cls.get_current_url():
                back_state = states.pop()
            set(_back_state, _separator.join(states))


    @classmethod
    def peek(cls, force=False):
        states = get(_back_state, default=False)
        if states:
            states = states.split(_separator)
            back_state = states[-1]
            if not force:
                if back_state == cls.get_current_url():
                    if len(states) > 1:
                        back_state  = states[-2]
                    else:
                        back_state = False
        else:
            back_state = False
        return back_state


    @classmethod
    def is_current_state_history(cls):
        get_request = request().GET
        history = False if 'history' not in get_request else True
        return history


    @classmethod
    def get_current_url(cls):
        url = current_url()
        url = ''.join([url, cls.query])
        return url




class _Pusher:

    def __init__(self, home):
        self.home = home

    def __call__(self, fn):

        def wrapper():
            push_url = History.get_current_url()
            if self.home:
                delete(_back_state)
            latest_push_url = History.peek(force=True)
            states = get(_back_state, default=False)
            if states:
                states_length = len(states)
                states = states.split(_separator)
            else:
                states = []
                states_length = 0
            if latest_push_url != push_url:
                states.append(push_url)
                states_length += len(push_url)
            while states_length > _back_state_max:
                old_state = states[0]
                del states[0]
                states_length -= len(old_state)

            set(_back_state, _separator.join(states))
            
            return fn()

        return wrapper

            


class ConsoleRequest():

    def __init__(self):
        self.session = dict()
        self.referer = "console"
        self.path = "console"
        self.client_addr = "console"


class ErrorRunInConsole(Exception):
    def __init__(self, *args):
        self.args = [a for a in args]

