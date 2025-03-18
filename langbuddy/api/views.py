from django.http import JsonResponse, HttpResponse
import json
from django.forms.models import model_to_dict
from products.models import Product




from rest_framework.response import Response
from rest_framework.decorators import api_view


@api_view(["GET", "POST"])
def api_home(request, *args, **kwargs):
    if request.method != "POST":
        return Response({"detail": "GET not allowed"}, status=405)
    model_data = Product.objects.all().order_by("?").first()
    data = {}
    if model_data:
        data = model_to_dict(model_data, fields=["id", "title"])
    return JsonResponse(data)