from pyramid.response import Response
from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPFound
import mysterio
import drdoom
import jsonpickle
from rumor import Rumor
import os
import uuid

static_path = os.path.dirname(__file__) + "/../f/static"
config = None

no_close_tag_elements = ["img", "br", "hr", "input", "link", "meta", "input"]


class Pyro:

    def __init__(self, **params):
        self.pyro_id = str(uuid.uuid4())
        self.init(**params)
        self.class_name = self.__class__.__name__
        data = self.js_init()
        JsParser.save(self.class_name, data)
        self.h = self.inject_data(data)


    @classmethod
    @Rumor.track_component()
    def get(cls, **params):
        a = cls(**params)
        return a.h


    def js_init(self):
        pass

    
    def tree(self):
        raise NotImplementedError()


    def inject_data(self, data):
        z = "".join(self.tree())
        if ">" in z:
            tmp = self.init_component_data(data)
            z = z.replace(">", tmp + ">", 1)
        return z


    def init_component_data(self, data):
        #tmp = " data-sc= \"" + str(data) + "\""
        tmp = " pyro_name= \"" + self.class_name + "\""
        if hasattr(self, "id"):
            tmp += " cid= \"" + self.id + "\""
        return tmp


    @classmethod
    def route(cls, path, layout=None):
        return _Route(path, layout)


    @classmethod
    def not_found(cls, layout=None):
        return _NotFoundRoute(layout)


    @classmethod
    def server_error(cls, layout=None):
        return _ServerErrorRoute(layout)


    @classmethod
    def active(cls, fn):
        def wrapper(request):
            a = dict((d, request.GET[d]) for d in request.GET)
            return fn(**a)

        config.add_route(fn.__name__, fn.__name__)
        config.add_view(route_name=fn.__name__, view=wrapper)
        config.commit()
        return wrapper


class JsParser:

    _jsdata = 'JsParserData'
    
    @classmethod
    def init(cls):
        mysterio.local_set(cls._jsdata, '')
        
    @classmethod
    def retrieve(cls):
        result = ['']
        jsdata = mysterio.local_get(cls._jsdata)
        result += ['<script type="text/javascript">']
        result += ['function js_init(){;']
        result += [jsdata]
        result += ['};']
        result += ['</script>']
        return result
        
    @classmethod
    def save(cls, class_name, jsdata):
        if jsdata is None:
            return
        result = cls.process(class_name, jsdata)
        mysterio.local_append(cls._jsdata, result)

    @classmethod
    def process(cls, class_name, jsdata):
        jsdata = cls.normalize(jsdata)
        config = cls.make_config(jsdata['data'])
        var_name = '_'.join([class_name, str(jsdata['id'])])
        js_function = 'z.' + jsdata['fn'] + '(' + config + ');'
        result = ' '.join(['var', var_name, '= new', js_function])
        result = cls.result_require(result, jsdata['path'])
        return result

    @classmethod
    def result_require(cls, result, path):
        return "require(['" + path + "'], function(z){" + result + "});"

    @classmethod
    def normalize(cls, js_data):
        js_data['id'] = js_data['id'] if 'id' in js_data else ''
        js_data['data'] = js_data['data'] if 'data' in js_data else ''
        return js_data

    @classmethod
    def make_config(cls, config_data):
        result = ''
        if config_data != '':
            result += '{'
            for key in config_data:
                result += (key + ':' + cls.parse(config_data[key]) + ",")
            result = result[0:-1]
            result += '}'
        return result

    @classmethod
    def parse(cls, value):
        t = type(value)
        val = ''
        if t == bool:
            val = 'true' if value else 'false'
        elif t == int or t == long or t == float:
            val = str(value)
        elif t == str:
            if 'js(' in value:
                val = value[3:-1]
            else:
                val = "'" + value + "'"
        return val



class HtmlParser:
    def __init__(self):
        self.exception_tag = self.init_exception_tag()
        self.init_tag("a", "abbr", "acronym", "address", "applet", "area", "b", "base", "basefont", "bdo", "big", "blockquote", "body", "br", "button", "caption", "center", "cite", "code", "col", "colgroup", "dd", "del", "dfn", "dir", "div", "dl", "dt", "em", "fieldset", "font", "form", "frame", "frameset", "h1", "h2", "h3", "h4", "h5", "h6", "head", "hr", "html", "i", "iframe", "img", "input", "ins", "isindex", "kbd", "label", "legend", "li", "link", "map", "menu", "meta", "nav", "noframes", "noscript", "object", "ol", "optgroup", "option", "p", "param", "pre", "q", "s", "section", "samp", "script", "select", "small", "span", "strike", "strong", "style", "sub", "sup", "table", "tbody", "td", "textarea", "tfoot", "th", "thead", "title", "tr", "tt", "u", "ul", "var", "plusone")

    def init_exception_tag(self):
        exception = dict()
        exception['plusone'] = 'g:plusone'
        return exception

    def init_tag(self, *args):
        for i in args:
            if i in self.exception_tag:
                setattr(self, i, Element(self.exception_tag[i]))
            else:
                setattr(self, i, Element(i))

    def script_tag(self, *args):
        self.args = args
        return self._generate_javascript()

    def css_tag(self, *args):
        self.args = args
        return self._generate_css()

    def _generate_javascript(self):
        z = []
        for i in self.args:
            if i == "vendor_all":
                continue
            if i == "require":
                z += "<script data-main=\"/static/javascript/application\" src=\"/static/javascript/require.js\"></script>"
            else:
                z += "<script src=\"/static/javascript/" + i + ".js\"></script>"
        return z

    def _generate_css(self):
        z = []
        for i in self.args:
            # z += "<link rel=\"stylesheet\" type=\"text/css\" href=\"/static/css/" + i + ".css\">"
            z += "<link rel=\"stylesheet/less\" type=\"text/css\" href=\"/static/css/" + i + ".less\">"
        return z

    def text(self, text):
        return [text]


class Element:
    def __init__(self, tag):
        self.tag = tag

    def __call__(self, direct_text = None, **kwargs):
        self.number_times = 1
        if direct_text is not None:
            self._generate()
            self.z += direct_text + "</" + self.tag + ">"
            return self.z
        else:
            self.kwargs = kwargs
            return self

    def raw(self):
        self._generate()
        if self.tag not in no_close_tag_elements:
            self.z += "</" + self.tag + ">"
        else:
            self.z = self.z * self.number_times
        return self.z

    def _generate(self):
        z = []
        z += "<" + self.tag
        has_css = False
        for i in self.kwargs:
            if i == "id":
                z += " id" + " = \"" + self.kwargs["id"] + "\""
            elif i == "_class":
                z += " class" + " = \"" + self.kwargs["_class"] + "\""
            elif i == "_for":
                z += " for" + " = \"" + self.kwargs["_for"] + "\""
            elif "css" in i:
                has_css = True
            else:
                z += " " + i.replace("_","-") + " = \"" + self.kwargs[i] + "\" "
        if has_css:
            z += " style" + " = \""
            for i in self.kwargs:
                if "css" in i:
                    css_var = i.split('css_')[1].replace('_', '-')
                    z += css_var + ":" + self.kwargs[i] + ";"
            z += "\""
        z += ">"
        self.z = z

    def into(self, html):
        self._generate()
        html += self.z
        return Into(html, self.tag)

    def call(self, route_name, action):
        self.kwargs["id"] = route_name
        if "_class" not in self.kwargs:
            self.kwargs["_class"] = "sc"
        else:
            self.kwargs["_class"] += " sc"
        return self

    def times(self, number_times):
        self.number_times = number_times
        return self


class Into:
    def __init__(self, html, tag):
        self.html = html
        self.tag = tag

    def __enter__(self):
        "enter"

    def __exit__(self, a, b, c):
        if self.tag not in no_close_tag_elements:
            self.html.append("</" + self.tag + ">")


class _Route:
    def __init__(self, path, layout):
        self.path = path
        self.layout = layout

    def __call__(self, fn):

        @Rumor.track_route()
        def wrapper(request):
            JsParser.init()
            result = fn()
            get = drdoom.request().GET
            json_state = False if 'json' not in get else get['json']
            history = False if 'history' not in get else True
            if history:
                drdoom.pop_history()
            if json_state:
                response = dict()
                result = "".join(result)
                response['body'] = result
                response = jsonpickle.encode(response)
                response = Response(response)
            elif type(result) is HTTPFound or self.layout is None:
                response = result
            elif self.layout is not None:
                h = "".join(self.layout(result) + JsParser.retrieve())
                route_name = "/".join(fn.__module__.split("view.")[-1].split("."))
                response = Response(h)
            mysterio.cleanup()
            return response

        config.add_route(self.path, self.path)
        config.add_view(route_name=self.path, view=wrapper)
        config.commit()

        return wrapper


class _NotFoundRoute:

    def __init__(self, layout):
        self.layout = layout


    def __call__(self, fn):

        @Rumor.track_route()
        def wrapper(request):
            JsParser.init()
            result = fn()
            get = drdoom.request().GET
            json_state = False if 'json' not in get else get['json']
            if json_state:
                response = dict()
                result = "".join(result)
                response['body'] = result
                response = jsonpickle.encode(response)
                response = Response(response)
            else:
                h = "".join(self.layout(result))
                route_name = "/".join(fn.__module__.split("view.")[-1].split("."))
                response = Response(h)
            mysterio.cleanup()
            return response

        config.add_view(view=wrapper, context=NotFound)
        config.commit()

        return wrapper


class _ServerErrorRoute:

    def __init__(self, layout):
        self.layout = layout


    def __call__(self, fn):

        @Rumor.track_route()
        def wrapper(request):
            JsParser.init()
            result = fn()
            get = drdoom.request().GET
            json_state = False if 'json' not in get else get['json']
            if json_state:
                response = dict()
                result = "".join(result)
                response['body'] = result
                response = jsonpickle.encode(response)
                response = Response(response)
            else:
                h = "".join(self.layout(result))
                route_name = "/".join(fn.__module__.split("view.")[-1].split("."))
                response = Response(h)
            mysterio.cleanup()
            return response

        config.add_view(view=wrapper, context=Exception)
        config.commit()

        return wrapper


h = HtmlParser()
