import drdoom
from rumor import Rumor, Logger
import jsonpickle
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
import f

_dynamic = 'dynamic'
_referer = 'referer'

_source = 'source'
_mobile = 'm'


class WAuth:

    @classmethod
    def check_image_empty(cls, redirect="", arg="", error_message="", ajax=False):
        return _CheckImageEmpty(redirect=redirect, arg=arg, error_message=error_message, ajax=ajax)

    @classmethod
    def check_input_empty(cls, redirect="", arg="", error_message="", ajax=False):
        return _CheckInputEmpty(redirect=redirect, arg=arg, error_message=error_message, ajax=ajax)

    @classmethod
    def check_price_valid(cls, redirect="", arg="", error_message="", ajax=False):
        return _CheckPriceValid(redirect=redirect, arg=arg, error_message=error_message, ajax=ajax)

    @classmethod
    def check_phone_valid(cls, redirect="", arg="", error_message="", ajax=False):
        return _CheckPhoneValid(redirect=redirect, arg=arg, error_message=error_message, ajax=ajax)

    @classmethod
    def check_location_valid(cls, redirect="", arg="", error_message="", ajax=False):
        return _CheckLocationValid(redirect=redirect, arg=arg, error_message=error_message, ajax=ajax)

    @classmethod
    def check_input_type(cls, redirect="", arg="", input_type=int, error_message="", ajax=False):
        return _CheckInputType(redirect=redirect, arg=arg, input_type=input_type, error_message=error_message, ajax=ajax)

    @classmethod
    def check_input_minlength(cls, redirect="", arg="", minlength=0, error_message="", ajax=False):
        return _CheckInputMinlength(redirect=redirect, arg=arg, minlength=minlength, error_message=error_message, ajax=ajax)

    @classmethod
    def check_input_maxlength(cls, redirect="", arg="", maxlength=0, error_message="", ajax=False):
        return _CheckInputMaxlength(redirect=redirect, arg=arg, maxlength=maxlength, error_message=error_message, ajax=ajax)

    @classmethod
    def check_max_image(cls, redirect="", arg="", max_image=0, error_message="", ajax=False):
        return _CheckMaxImage(redirect=redirect, arg=arg, max_image=max_image, error_message=error_message, ajax=ajax)

    @classmethod
    def check_captcha(cls, redirect, error_message):
        return _CheckCaptcha(redirect, error_message)

    @classmethod
    def doomify(cls, include=None, getall=None, exclude=set([])):
        return _Doomify(include, getall, exclude)

    @classmethod
    def description_doomify(cls, args):
        return _DescriptionDoomify(args)

    @classmethod
    def shopfront_details_doomify(cls, args):
        return _ShopfrontDetailsDoomify(args)



class Required:

    @classmethod
    def item_session(cls, redirect, redirect_mobile=False):
        return _ItemSession(redirect, redirect_mobile)

    @classmethod
    def edit_session(cls, redirect, redirect_mobile=False):
        return _EditSession(redirect, redirect_mobile)

    @classmethod
    def item_owner(cls, redirect, redirect_mobile=False):
        return _ItemOwner(redirect, redirect_mobile)

    @classmethod
    def country_supported(cls, redirect, redirect_mobile=False):
        return _CountrySupported(redirect, redirect_mobile)

    @classmethod
    def country_set(cls, redirect, redirect_mobile=False):
        return _CountrySet(redirect, redirect_mobile)

    @classmethod
    def shopfront_exist(cls, redirect, redirect_mobile=False):
        return _ShopfrontExist(redirect, redirect_mobile)

    @classmethod
    def shopfront_published(cls, redirect, redirect_mobile=False):
        return _ShopfrontPublished(redirect, redirect_mobile)

    @classmethod
    def shopfront_completed(cls, redirect, redirect_mobile=False):
        return _ShopfrontCompleted(redirect, redirect_mobile)

    @classmethod
    def shopfront_owner(cls, redirect, redirect_mobile=False):
        return _ShopfrontOwner(redirect, redirect_mobile)

    @classmethod
    def shopfront_domain_unset(cls, redirect, redirect_mobile=False):
        return _ShopfrontDomainUnset(redirect, redirect_mobile)

    @classmethod
    def shopfront_domain_set(cls, redirect, redirect_mobile=False):
        return _ShopfrontDomainSet(redirect, redirect_mobile)

    @classmethod
    def shopfront_item_exist(cls, redirect, redirect_mobile=False):
        return _ShopfrontItemExist(redirect, redirect_mobile)

    @classmethod
    def item_exist(cls, redirect, redirect_mobile=False):
        return _ItemExist(redirect, redirect_mobile)

    @classmethod
    def broadcast_exist(cls, redirect, redirect_mobile=False):
        return _BroadcastExist(redirect, redirect_mobile)

    @classmethod
    def premium_user(cls, redirect, redirect_mobile=False):
        return _PremiumUser(redirect, redirect_mobile)

    @classmethod
    def login(cls, redirect, redirect_mobile=False):
        return _Login(redirect, redirect_mobile)

    @classmethod
    def dashsell_liutenant(cls, redirect, redirect_mobile=False):
        return _DashsellLiutenant(redirect, redirect_mobile)

    @classmethod
    def dashsell_commander(cls, redirect, redirect_mobile=False):
        return _DashsellCommander(redirect, redirect_mobile)

    @classmethod
    def dashsell_admiral(cls, redirect, redirect_mobile=False):
        return _DashsellAdmiral(redirect, redirect_mobile)



def get_redirect(redirect):
    try:
        elements = redirect.split('/')
        request = drdoom.request().matchdict
        for i in range(len(elements)):
            element = elements[i]
            if '{' in element:
                element = request[element[1:-1]]
            elements[i] = element
        redirect = '/'.join(elements)
    except AttributeError, e:
        redirect = '/'
    return redirect



################################## WAuth subclass Implementation ###################################################

class _Doomify():
    """
    Doomify store all the post request that is currently being processed to user's cookie via drdoom
    """
    def __init__(self, include, getall, exclude):
        self.include = include
        self.getall = getall
        self.exclude = exclude
        self.limit = 1000

    def __call__(self, fn):

        def wrapper():
            post = drdoom.request().POST

            #Handling the include
            if self.include is None:
                for key in post:
                    if key not in self.exclude:
                        drdoom.set(key, post[key][:self.limit])
            else:
                for key in self.include:
                    if key not in self.exclude:
                        drdoom.set(key, post[key][:self.limit])

            #Handling getall for checkboxes or multiple input with one name
            if self.getall is not None:
                for key in self.getall:
                    drdoom.set(key, post.getall(key))

            return fn()

        return wrapper


class _DescriptionDoomify():
    """
    UltraDoomify store your item parameter using unique handler
    """
    def __init__(self, args):
        self.args = args

    def __call__(self, fn):

        def wrapper():
            post = drdoom.request().POST

            iid = drdoom.get('iid')
            if self.args in post:
                f.model.item.update_description(iid, post[self.args])

            return fn()

        return wrapper


class _ShopfrontDetailsDoomify():
    """
    UltraDoomify store your item parameter using unique handler
    """
    def __init__(self, args):
        self.args = args

    def __call__(self, fn):

        def wrapper():
            post = drdoom.request().POST

            uid = drdoom.get('uid')
            if self.args in post:
                f.model.shopfront.update_details(uid, post[self.args])

            return fn()

        return wrapper


class _CheckCaptcha:
    def __init__(self, redirect, error_message):
        self.redirect = redirect
        self.error_message = error_message

    def __call__(self, fn):

        def wrapper():
            post = drdoom.request().POST

            response = fn()
            if 'adcopy_response' in post and 'adcopy_challenge' in post:
                captcha_response = req['adcopy_response']
                captcha_challenge = req['adcopy_challenge']
                if not f.etc.captcha.verify(captcha_response, drdoom.request().remote_addr,
                    challenge=captcha_challenge):
                    Rumor.track_wizard(self)
                    drdoom.set_error(self.error_message)
                    response = HTTPFound(location='/confirm')

            return response

        return wrapper




################################## Required Section ##########################################################


class _BaseRequired:

    def __init__(self, redirect, redirect_mobile=False):
        self.redirect = redirect
        self.redirect_mobile = redirect_mobile
        self.init()

    def init(self):
        pass

    def get_redirect(self):
        redirect = self.redirect
        get = drdoom.request().GET
        if _source in get:
            if get[_source] == _mobile:
                redirect = self.redirect_mobile
        return get_redirect(redirect)


class _ItemSession(_BaseRequired):

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            self.error_message = "not in sell mode"
            iid = drdoom.get('iid')
            if iid is not None:
                response = fn()
            else:
                Rumor.track_wizard(self)
                response = HTTPFound(location=self.redirect)

            return response

        return wrapper


class _EditSession(_BaseRequired):

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            self.error_message = "not in edit mode"
            is_edit = drdoom.get('edit_item')
            if is_edit:
                response = fn()
            else:
                Rumor.track_wizard(self)
                response = HTTPFound(location=self.redirect)

            return response

        return wrapper


class _Login(_BaseRequired):

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            self.error_message = "not logging in"
            if drdoom.islogin():
                response = fn()
            else:
                Rumor.track_wizard(self)
                response = HTTPFound(location=self.redirect)

            return response

        return wrapper


class _CountrySupported(_BaseRequired):

    def init(self):
        self.supported = f.country.supported.get_country_list()

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            self.error_message = "country not supported"
            if drdoom.islogin():
                uid = drdoom.get_uid()
                cid = f.model.user.get_country(uid)
                if cid in self.supported:
                    response = fn()
                else:
                    Rumor.track_wizard(self, cid=cid)
                    response = HTTPFound(location=self.redirect)
            else:
                response = fn()

            return response

        return wrapper


class _CountrySet(_BaseRequired):

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            self.error_message = "country unset"
            if drdoom.islogin():
                uid = drdoom.get_uid()
                cid = f.model.user.get_country(uid)
                if cid != 0:
                    response = fn()
                else:
                    Rumor.track_wizard(self)
                    response = HTTPFound(location=self.redirect)
            else:
                response = fn()

            return response

        return wrapper


class _ShopfrontExist(_BaseRequired):

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            self.error_message = "No shop found here"
            key = drdoom.request().matchdict
            shopfront_name = key['shopfront_name']
            if not f.model.shopfront.get_owner(shopfront_name):
                Rumor.track_wizard(self, shopfront_name=shopfront_name)
                drdoom.set_error(self.error_message)
                response = HTTPFound(location=self.redirect)
            else:
                response = fn()

            return response

        return wrapper


class _ShopfrontCompleted(_BaseRequired):

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            self.error_message = "Shops not completed yet"
            uid = drdoom.get_uid()

            total_progress = 0
            total_progress += f.etc.progress.shop_progress(uid)
            total_progress += f.etc.progress.shop_listing_progress(uid)
            
            if total_progress < 200:
                Rumor.track_wizard(self, uid=uid, progress=total_progress)
                response = HTTPFound(location=self.redirect)
            else:
                response = fn()

            return response

        return wrapper


class _ShopfrontPublished(_BaseRequired):

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            key = drdoom.request().matchdict
            uid = drdoom.get_uid()

            #Case for shopfront public is not exists
            if 'shopfront_name' in key:
                shopfront_name = key['shopfront_name']
                self.error_message = "No shop found here"
                if not f.model.shopfront.is_shopfront_published(shopfront_name):
                    Rumor.track_wizard(self, shopfront_name=shopfront_name)
                    drdoom.set_error(self.error_message)
                    response = HTTPFound(location=self.redirect)
                else:
                    response = fn()
            else:
                #Case for the user haven't published their shopfront
                self.error_message = "Shopfront not published yet"
                shopfront_name = f.model.user.get_subdomain(uid)
                if not f.model.shopfront.is_shopfront_published(shopfront_name):
                    Rumor.track_wizard(self, shopfront_name=shopfront_name)
                    response = HTTPFound(location=self.redirect)
                else:
                    response = fn()

            return response

        return wrapper


class _ShopfrontItemExist(_BaseRequired):

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            self.error_message = "item shopfront not exist"
            key = drdoom.request().matchdict
            if 'shopfront_name' in key:
                shopfront_name = key['shopfront_name']
                uid = f.model.shopfront.get_owner(shopfront_name)
            else:
                uid = drdoom.get_uid()
            iid = int(key['iid'])
            if not f.model.item.is_item_owner(iid, uid):
                Rumor.track_wizard(self, iid=iid, uid=uid)
                response = HTTPFound(location=self.redirect)
            else:
                response = fn()

            return response

        return wrapper


class _ItemExist(_BaseRequired):

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            self.error_message = "item does not exist"
            error = False
            key = drdoom.request().matchdict
            iid = key['iid']
            try:
                iid = int(iid)
                details = f.model.item.get_details(iid)
                if details is None:
                    error = True
            except:
                error = True
            if error:
                Rumor.track_wizard(self, iid=iid)
                response = HTTPFound(location=self.redirect)
            else:
                response = fn()

            return response

        return wrapper


class _BroadcastExist(_BaseRequired):

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            self.error_message = "shopfront broadcast not exist"
            key = drdoom.request().matchdict
            if 'shopfront_name' in key:
                shopfront_name = key['shopfront_name']
                uid = f.model.shopfront.get_owner(shopfront_name)
            else:
                uid = drdoom.get_uid()
            broadcast_id = int(key['broadcast_id'])
            shopfront_id = f.model.broadcast.get_broadcast_source(broadcast_id)
            owner_id = f.model.shopfront.get_owner_by_id(shopfront_id)
            if owner_id != uid:
                Rumor.track_wizard(self, broadcast_id=broadcast_id, uid=uid)
                response = HTTPFound(location=self.redirect)
            else:
                response = fn()

            return response

        return wrapper


class _ShopfrontOwner(_BaseRequired):

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            self.error_message = "not shopfront owner"
            key = drdoom.request().matchdict
            uid = drdoom.get_uid()
            shopfront_name = key['shopfront_name']
            if uid == f.model.shopfront.get_owner(shopfront_name):
                response = fn()
            else:
                Rumor.track_wizard(self, shopfront_name=shopfront_name, uid=uid)
                response = HTTPFound(location=self.redirect)

            return response

        return wrapper


class _PremiumUser(_BaseRequired):

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            self.error_message = "not premium user"
            key = drdoom.request().matchdict
            uid = drdoom.get_uid()
            if f.model.user.is_premium(uid):
                response = fn()
            else:
                Rumor.track_wizard(self, uid=uid)
                response = HTTPFound(location=self.redirect)

            return response

        return wrapper


class _ShopfrontDomainUnset(_BaseRequired):

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            self.error_message = "Subdomain is already set"
            key = drdoom.request().matchdict
            uid = drdoom.get_uid()
            if not f.model.user.get_subdomain(uid):
                response = fn()
            else:
                Rumor.track_wizard(self, uid=uid)
                response = HTTPFound(location=self.redirect)

            return response

        return wrapper


class _ShopfrontDomainSet(_BaseRequired):

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            self.error_message = "Subdomain is not being set"
            key = drdoom.request().matchdict
            uid = drdoom.get_uid()
            if not f.model.user.get_subdomain(uid):
                Rumor.track_wizard(self, uid=uid)
                response = HTTPFound(location=self.redirect)
            else:
                response = fn()

            return response

        return wrapper


class _ItemOwner(_BaseRequired):

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            self.error_message = "Not the item owner"
            key = drdoom.request().matchdict
            uid = drdoom.get_uid()
            iid = int(key['iid'])
            if not f.model.item.is_item_owner(iid, uid):
                Rumor.track_wizard(self, iid=iid, uid=uid)
                response = HTTPFound(location=self.redirect)
            else:
                response = fn()

            return response

        return wrapper


class _DashsellLiutenant(_BaseRequired):

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            self.error_message = "you are not dashsell liutenant"
            uid = drdoom.get_uid()
            if f.model.user.is_liutenant_or_above(uid):
                response = fn()
            else:
                Rumor.track_wizard(self, uid=uid)
                response = HTTPFound(location=self.redirect)

            return response

        return wrapper


class _DashsellCommander(_BaseRequired):

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            self.error_message = "you are not dashsell commander"
            uid = drdoom.get_uid()
            if f.model.user.is_commander_or_above(uid):
                response = fn()
            else:
                Rumor.track_wizard(self, uid=uid)
                response = HTTPFound(location=self.redirect)

            return response

        return wrapper


class _DashsellAdmiral(_BaseRequired):

    def __call__(self, fn):
        def wrapper():
            self.redirect = self.get_redirect()
            self.error_message = "you are not dashsell admiral"
            uid = drdoom.get_uid()
            if f.model.user.is_admiral(uid):
                response = fn()
            else:
                Rumor.track_wizard(self, uid=uid)
                response = HTTPFound(location=self.redirect)

            return response

        return wrapper





################################## PostInput Section ##########################################################


class _PostInput:
    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def __call__(self, fn):
        def wrapper():
            if self.check_error():
                drdoom.set_error(self.error_message)
                Rumor.track_wizard(self)
                response = self.get_redirect(self.redirect, self.ajax)
            else:
                response = fn()

            return response

        return wrapper

    def get_redirect(self, redirect, ajax):
        if redirect == _dynamic:
            post = drdoom.request().POST
            redirect =  post['redirect_failed'] if 'redirect_failed' in post else '/'
        elif redirect == _referer:
            redirect = drdoom.referer()
        if ajax:
            res = dict()
            res['redirect'] = redirect
            response = Response(jsonpickle.encode(res))
        else:
            response = HTTPFound(location=redirect)
        return response

    def check_error(self):
        post = drdoom.request().POST
        error = self.check_input(post)
        return error


class _CheckInputEmpty(_PostInput):

    def check_input(self, post):
        error = False
        if self.arg not in post:
            error = True
        else:
            if post[self.arg] == "":
                error = True
        return error


class _CheckImageEmpty(_PostInput):

    def check_input(self, post):
        error = True
        for i in range(4):
            arg = self.arg + str(i)
            if arg in post:
                if post[arg] != "":
                    error = False
        return error


class _CheckPriceValid(_PostInput):

    def check_input(self, post):
        error = False
        price = post[self.arg]
        total_dot = price.count('.')
        price = price.replace(',','').replace('.','')
        try:
            price_int = int(price)
            if total_dot > 1:
                error = True
        except ValueError:
            error = True
        if price_int < 0:
            error = True
        return error


class _CheckPhoneValid(_PostInput):

    def check_input(self, post):
        error = False
        if self.arg in post:
            phone_number = post[self.arg]
            if phone_number != "":
                try:
                    num = int(phone_number)
                except ValueError:
                    error = True
        return error


class _CheckLocationValid(_PostInput):

    def check_input(self, post):
        error = False
        if self.arg in post:
            location = post[self.arg]
            if location == "":
                error = True
        return error


class _CheckInputType(_PostInput):

    def check_input(self, post):
        try:
            value = self.input_type(post[self.arg])
            error = False
        except ValueError:
            error = True
        return error


class _CheckInputMinlength(_PostInput):

    def check_input(self, post):
        if len(post[self.arg].replace(' ','')) >= self.minlength:
            error = False
        else:
            error = True
        return error


class _CheckInputMaxlength(_PostInput):

    def check_input(self, post):
        if len(post[self.arg].replace(' ','')) <= self.maxlength:
            error = False
        else:
            error = True
        return error


class _CheckMaxImage(_PostInput):

    def check_input(self, post):
        if self.arg in post:
            total_images = post[self.arg].split(f.define.IMAGE_SEPARATOR)
            if len(total_images) <= self.max_image:
                error = False
            else:
                error = True
        else:
            total_images = 0
            for i in range(self.max_image):
                arg = self.arg + str(i)
                if post[arg]:
                    total_images += 1
            if total_images <= self.max_image:
                error = False
            else:
                error = True

        return error


