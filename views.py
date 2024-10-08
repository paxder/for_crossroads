from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.gzip import gzip_page
from django.views.decorators.http import require_http_methods, require_POST
from api.rest import getResponse, bad_response, good_response
from api.rest import handler404, handler403, handler400, handler405, handler500
import json, os, time
from api.decorators import user_has_valid_token,secure_api_request
from api.services.followers import Followers

@gzip_page
@require_http_methods(["GET"])
@user_has_valid_token
def index(request):
    """ Index """
    return JsonResponse({})

@gzip_page
@require_http_methods(["POST"])
@user_has_valid_token
def getMyFollowers(request):
    """
    Get list of my followers
    """
    try: 
        req = json.loads(request.body)    
        user_id = req['user_id']
        f = Followers(user_id)
        data = f.getMyFollowersList()
        resp = {'followers':data, 'last_id' : None}
        if len(data) > 0:
            resp['last_id'] = data[-1]['id']
        return getResponse(resp)
    except:
        return getResponse(bad_response)
