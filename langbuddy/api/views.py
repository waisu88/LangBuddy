import json
from django.forms.models import model_to_dict
from products.models import Product
from products.serializers import ProductSerializer



from rest_framework.response import Response
from rest_framework.decorators import api_view


@api_view(["GET", "POST"])
def api_home(request, *args, **kwargs):
    # # if request.method != "POST":
    # #     return Response({"detail": "GET not allowed"}, status=405)
    # instance = Product.objects.all().order_by("?").first()
    # data = {}
    # if instance:
    #     data = ProductSerializer(instance).data
    #     # data = model_to_dict(model_data, fields=["id", "title"])
    # data = request.data
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        print(serializer.data)
        # data = serializer.data
        return Response(serializer.data)
    return Response({"message": "invalid data"}, status=400)