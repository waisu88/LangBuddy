import requests


endpoint = "http://localhost:8000/api/products/"

data = {"title": "this field is ok",
        "price": 32.22}

get_response = requests.get(endpoint, json=data)

print(get_response.json())