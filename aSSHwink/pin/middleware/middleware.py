from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from asshwink.settings import PIN


class PinAuthMiddleware(MiddlewareMixin):

    def process_request(self,request):
        request.session.set_expiry(1800)
        #return HttpResponse(str(reverse('autoPinAuth',kwargs={'pin_sent':1234})))
        preAuthUrls=[reverse('pinAuth'),reverse('auth'),reverse('autoPinAuth',kwargs={'pin_sent':PIN})]
        pinAuthorized=request.session.get("pinAuthorized",False)

        if request.path not in preAuthUrls:
            if not pinAuthorized:
                return HttpResponseRedirect("%s?next=%s" % (reverse('pinAuth'), request.path))
