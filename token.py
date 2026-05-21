import requests
from requests.auth import HTTPBasicAuth

CLIENT_ID = "66bb5ab788224e41aace2242c8a3ddee"
CLIENT_SECRET = "hXdriWPfZAAbzjisx2xa4s1RtNuj9b1AfXS7AkGFAijn4yxp3tXpLoStN8ivCpAw"
AUTHORIZATION_CODE = "1gHWBVwvj1OYMu_PYNxT8AzcnEezcZr5ovLYLIGhhWIQlH54Wm1_b28Jn_CBCR7vswVhAJ6E7dR4MzgNwTK4jraRzAPXEagqpq14oVAd_eR2pdixGNtY6zW65lEsec4k"

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
