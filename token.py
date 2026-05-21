import requests
from requests.auth import HTTPBasicAuth

CLIENT_ID = "66bb5ab788224e41aace2242c8a3ddee"
CLIENT_SECRET = "hXdriWPfZAAbzjisx2xa4s1RtNuj9b1AfXS7AkGFAijn4yxp3tXpLoStN8ivCpAw"
AUTHORIZATION_CODE = "Cgr5F8bxoGeVl4rzG4R2YviOUfYH8wV6AmeOnkcMn7emvtO7UZMj35By4JKCPvw748qg5ZyfS880XJNcG0CZy1L_pIkGArUJa5TQdV1j-OmSZnp452IWbEpx"

response = requests.post(
    "https://allegro.pl/auth/oauth/token",
    auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
    data={
        "grant_type": "authorization_code",
        "code": AUTHORIZATION_CODE,
        "redirect_uri": "https://localhost/"
    }
)

print(response.json())
