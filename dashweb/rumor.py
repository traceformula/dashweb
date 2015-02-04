import logging
import inspect
import datetime
import jsonpickle
import drdoom
import time
import os


_all = "all"
_start_tag = "enter"
_end_tag = "exit"
_logger_handler_dashsell = "dashsell"
_logger_handler_dashweb = "dashweb"
_debug = "debug"
_info = "info"
_warning = "warning"
_error = "error"
_boomerang = "boomerang"

_logfile_path = os.path.dirname(os.path.realpath(__file__)) + "/../../logs/"

def get_time(time):
    return ["RENDER_TIME "+str(milify(time))+"ms"]

def milify(time):
    time = time*1000
    return ("%.4f" % time)

def get_identity():
    identity = ['guest' if not drdoom.get_uid() else 'uid_'+str(drdoom.get_uid())]
    identity += [drdoom.get_user_ip()]
    return " ".join(identity)

class Rumor:
    """
    This class responsible to handle the decorator logging system of the webapp
    This class provides more things such as:
    - able to include or exclude any parameter of the function that want to be logged
    - able to log the output of the function
    - able to measure the execution time of the function in milisecond
    """
    @classmethod
    def debug(cls, event, include=_all, exclude=None, timer=False, result=False):
        return _Logger(_debug, event, include, exclude, timer, result)

    @classmethod
    def info(cls, event, include=_all, exclude=None, timer=False, result=False):
        return _Logger(_info, event, include, exclude, timer, result)

    @classmethod
    def warning(cls, event, include=_all, exclude=None, timer=False, result=False):
        return _Logger(_warning, event, include, exclude, timer, result)

    @classmethod
    def error(cls, event, include=_all, exclude=None, timer=False, result=False):
        return _Logger(_error, event, include, exclude, timer, result)

    @classmethod
    def track_route(cls):
        return _RouteTracker()

    @classmethod
    def track_component(cls):
        return _ComponentTracker()

    @classmethod
    def track_mysterio(cls, type=''):
        return _MysterioTracker(type)

    @classmethod
    def track_wizard(cls, obj, **kwargs):
        return _WizardTracker(obj, **kwargs)



class Logger:
    """
    This class responsible to handle the inline logging system of the webapp
    """
    @classmethod
    def debug(cls, event, **kwargs):
        _InlineLogger.debug(event, **kwargs)

    @classmethod
    def info(cls, event, **kwargs):
        _InlineLogger.info(event, **kwargs)

    @classmethod
    def warning(cls, event, **kwargs):
         _InlineLogger.warning(event, **kwargs)

    @classmethod
    def error(cls, event, **kwargs):
         _InlineLogger.error(event, **kwargs)

    @classmethod
    def boomerang(cls, **kwargs):
         _InlineLogger.boomerang(**kwargs)

##################################### private class implementation of Rumor module ####################################

class _Logger:

    logger = logging.getLogger(_logger_handler_dashsell)

    def __init__(self, level, event, include, exclude, timer, result):
        self.event_name = event.replace(" ","_").upper()
        self.include = _all if include == _all else include.split(",")
        self.exclude = [] if exclude is None else exclude.split(",")
        self.timer = timer
        self.result = result
        self.data_name = list()
        self.data_default = list()
        self.data_match = dict()
        if level == _debug:
            self.logger = _Logger.logger.debug
        elif level == _info:
            self.logger = _Logger.logger.info
        elif level == _warning:
            self.logger = _Logger.logger.warning
        elif level == _error:
            self.logger = _Logger.logger.error

    def __call__(self, func):

        def fn(*args, **kwargs):
            #self.start_log(*args, **kwargs)
            t_start = 0 if not self.timer else time.time()
            val = func(*args, **kwargs)
            t_delta = 0 if not self.timer else time.time() - t_start
            self.end_log(val, t_delta, *args, **kwargs)
            return val

        self.init_params(func)

        return fn

    def init_params(self, func):
        argspec = inspect.getargspec(func)
        param_name, param_default = argspec[0], argspec[3] if argspec[3] is not None else []
        offset = len(param_name) - len(param_default)
        for i, name in enumerate(param_name):
            self.data_name.append(name)
            self.data_default.append(param_default[i-offset] if i >= offset else "")
            self.data_match[name] = param_default[i-offset] if i >= offset else ""

    def get_event_name(self, *args, **kwargs):
        return self.event_name

    def start_log(self, *args, **kwargs):
        message = [self.get_event_name()]
        message += [get_identity()]
        message += [_start_tag]
        message += [self.get_json_data(*args, **kwargs)]
        self.logger(" ".join(message))

    def get_json_data(self, *args, **kwargs):
        data = dict()
        for i, val in enumerate(self.data_name):
            if val not in self.exclude:
                data[val] = args[i] if len(args) > i else self.data_default[i]
        for key in kwargs:
            if key not in self.exclude:
                data[key] = kwargs[key]
        if self.include != _all:
            data = dict((k, v) for (k, v) in data.iteritems() if k in self.include)
        return jsonpickle.encode(data)

    def end_log(self, val, time, *args, **kwargs):
        if not self.timer and not self.check_val(val):
            pass
        message = [self.get_event_name(*args, **kwargs)]
        message += [get_identity()]
        #message += [_end_tag]
        message += [self.get_json_data(*args, **kwargs)]
        message += [] if not self.timer else get_time(time)
        message += [] if not self.check_val(val) else [jsonpickle.encode(val)]
        self.logger(" ".join(message))

    def check_val(self, val):
        t, result = type(val), False
        if (t is str or t is int or t is list or t is dict) and result:
            result = True
        return result


class _InlineLogger():

    logger = logging.getLogger(_logger_handler_dashsell)
    logger_dashweb = logging.getLogger(_logger_handler_dashweb)
    _instance = dict()

    def __init__(self, level):
        if level == _debug:
            self.logger = _InlineLogger.logger.debug
        elif level == _info:
            self.logger = _InlineLogger.logger.info
        elif level == _warning:
            self.logger = _InlineLogger.logger.warning
        elif level == _error:
            self.logger = _InlineLogger.logger.error
        elif level == _boomerang:
            self.logger = _InlineLogger.logger_dashweb.info

    def log(self, event, **kwargs):
        message = [event.replace(' ','_').upper()]
        message += [get_identity()]
        message += [jsonpickle.encode(kwargs)]
        self.logger(" ".join(message))

    @classmethod
    def initialize(cls):
        _InlineLogger._instance[_debug] = _InlineLogger(_debug)
        _InlineLogger._instance[_info] = _InlineLogger(_info)
        _InlineLogger._instance[_warning] = _InlineLogger(_warning)
        _InlineLogger._instance[_error] = _InlineLogger(_error)
        _InlineLogger._instance[_boomerang] = _InlineLogger(_boomerang)

    @classmethod
    def boomerang(cls, **kwargs):
        _InlineLogger._instance[_boomerang].log(_boomerang, **kwargs)

    @classmethod
    def debug(cls, event, **kwargs):
        _InlineLogger._instance[_debug].log(event, **kwargs)

    @classmethod
    def info(cls, event, **kwargs):
        _InlineLogger._instance[_info].log(event, **kwargs)

    @classmethod
    def warning(cls, event, **kwargs):
        _InlineLogger._instance[_warning].log(event, **kwargs)

    @classmethod
    def error(cls, event, **kwargs):
        _InlineLogger._instance[_error].log(event, **kwargs)



class _PyroTracker(_Logger):

    logger = logging.getLogger(_logger_handler_dashweb)

    def __init__(self):
        self.include = []
        self.exclude = []
        self.timer = True
        self.result = False
        self.data_name = list()
        self.data_default = list()
        self.data_match = dict()
        self.logger = _PyroTracker.logger.info
        self.local_init()

    def __call__(self, func):

        def fn(*args, **kwargs):
            t_start = 0 if not self.timer else time.time()
            val = self.run_func(func, args, kwargs)
            t_delta = 0 if not self.timer else time.time() - t_start
            self.end_log(val, t_delta, *args, **kwargs)
            return val

        self.init_params(func)

        return fn

    def local_init(self):
        pass


class _RouteTracker(_PyroTracker):

    def get_event_name(self, *args, **kwargs):
        event_name = "ROUTE "+drdoom.path()
        event_name += "" if drdoom.referer() is None else " REFERER " + drdoom.referer()
        return event_name

    def run_func(self, func, args, kwargs):
        return func(args[0])


class _ComponentTracker(_PyroTracker):

    def local_init(self):
        self.include = _all
        self.exclude = ['cls']

    def get_event_name(self, *args, **kwargs):
        return "COMPONENT " + args[0].__name__

    def run_func(self, func, args, kwargs):
        return func(*args, **kwargs)


class _MysterioTracker(_Logger):

    logger = logging.getLogger(_logger_handler_dashweb)

    def __init__(self, type):
        self.include = _all
        self.exclude = []
        self.timer = True
        self.result = False
        self.data_name = list()
        self.data_default = list()
        self.data_match = dict()
        self.init = False
        self.type = type
        self.logger = _MysterioTracker.logger.info

    def __call__(self, func):

        def fn(*args, **kwargs):
            t_start = 0 if not self.timer else time.time()
            val = func(*args, **kwargs)
            t_delta = 0 if not self.timer else time.time() - t_start
            event_name = get_event_name(fn)
            if self.type == '':
                self.init_params(fn)
            self.end_log(event_name, val, t_delta, *args, **kwargs)
            return val

        def get_event_name(fn):
            if self.type == 'dirty':
                log = " ".join(['mysterio', 'dirty', fn.__name__, fn.id]).upper()
            else:
                log = " ".join(['mysterio', fn.__name__, fn.source]).upper()
            return log

        return fn


    def end_log(self, event_name, val, time, *args, **kwargs):
        message = [event_name]
        message += [get_identity()]
        message += [self.get_json_data(*args, **kwargs)]
        message += [] if not self.timer else get_time(time)
        message += [] if not self.check_val(val) else [jsonpickle.encode(val)]
        self.logger(" ".join(message))

    def init_params(self, func):
        if not self.init:
            self.init = True
            argspec = func.argspec
            param_name, param_default = argspec[0], argspec[3] if argspec[3] is not None else []
            offset = len(param_name) - len(param_default)
            for i, name in enumerate(param_name):
                self.data_name.append(name)
                self.data_default.append(param_default[i-offset] if i >= offset else "")
                self.data_match[name] = param_default[i-offset] if i >= offset else ""


class _WizardTracker(_Logger):

    logger = logging.getLogger(_logger_handler_dashweb)

    def __init__(self, obj, **kwargs):
        self.name = obj.__class__.__name__
        self.kwargs = kwargs
        if hasattr(obj, 'error_message'):
            self.error_message = obj.error_message.replace(' ', '_')
        else:
            self.error_message = 'no message'
        self.logger = _WizardTracker.logger.info
        self.log()

    def log(self):
        message = [self.get_event_name()]
        message += [get_identity()]
        message += [jsonpickle.encode(self.kwargs)]
        self.logger(" ".join(message))

    def get_event_name(self):
        return " ".join(['WIZARD', self.name, self.error_message])


class _Processor:

    event_set = set()

    @classmethod
    def run(cls):
        logfile = cls.get_file()
        with open(logfile) as f:
            for line in f:
                cls.process_log(line)
                break
        print "done logging"

    @classmethod
    def process_log(cls, raw):
        data = raw.split(' ')
        tag = cls.check_log_validity(data)
        if not tag:
            pass
        json_data = cls.get_jsondata(data, tag)
        cls.save(json_data, tag)

    @classmethod
    def save(cls, data, tag):
        print data

    @classmethod
    def check_log_validity(cls, data):
        result = False if len(data) <= 6 else data[6]
        return result

    @classmethod
    def get_timestamp(cls, data):
        time = ' '.join([data[0], data[1]])
        return datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')

    @classmethod
    def get_jsondata(cls, data, tag):
        if tag == _start_tag:
            result = jsonpickle.decode(' '.join([str(d) for d in data[7:]]))
        elif tag == _end_tag:
            result = dict() if len(data) <= 8 else jsonpickle.decode(' '.join([str(d) for d in data[8:]]))
        result["created_at"] = cls.get_timestamp(data)
        result["event_name"] = data[3]
        result['uid'] = data[4]
        result['ip'] = data[5]
        return result

    @classmethod
    def get_file(cls):
        ext = (datetime.datetime.now()- datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        return ''.join([_logfile_path, 'dashsell.log.', ext])

if __name__ == "__main__":
    _Processor.run()


#################################  initialization  #################################################
_InlineLogger.initialize()
