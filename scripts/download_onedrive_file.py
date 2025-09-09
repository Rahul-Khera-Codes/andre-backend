import os
import requests

from dotenv import load_dotenv

load_dotenv(override=True)

# ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# Graph API endpoint for listing root drive files
url = "https://my.microsoftpersonalcontent.com/personal/e4a75bfce97e854e/_layouts/15/download.aspx?UniqueId=8ec5474a-a0b0-4aab-9772-67206bf82492&Translate=false&tempauth=v1e.eyJzaXRlaWQiOiI0ZDFlZDBmOS0wNGYwLTRkZGMtOWUzZS1lYmJhNTMzOGFkMDciLCJhcHBfZGlzcGxheW5hbWUiOiJhenVyZS1haS1pbnRlZ3JhdGlvbiIsImFwcGlkIjoiMDNjMWM2NTQtMmFiYy00OTFlLWIzMTEtM2NjNzg1YjNhMmVmIiwiYXVkIjoiMDAwMDAwMDMtMDAwMC0wZmYxLWNlMDAtMDAwMDAwMDAwMDAwL215Lm1pY3Jvc29mdHBlcnNvbmFsY29udGVudC5jb21AOTE4ODA0MGQtNmM2Ny00YzViLWIxMTItMzZhMzA0YjY2ZGFkIiwiZXhwIjoiMTc1NzQxNTA0NyJ9.i7uXiEb5cmrMtXlOxtx2zHSJcKtXZNvk90CsSjqt5I7ZzzRBq9A_YAIu7B70lUgOr8JwVP7lXogOW1APu-aNkMxQC4seJOpv7qhuoJL45SHLhJbdCBl4oCkE9Ive2zKDJJjMwQfxEUop7tV8TOhnsB5j6rthyKYRPtYkq563bdWLQk0Pg1KI1FfepONUoxXSHwiedbARixxk3Il86O0vMwsrt3kGH31UAApGYDDsBwl_nIZ0f_7CC8v_kILJXA1bl051VqOwMlIhow0n2w1Fye3Jskry_StsqRpIfrk4i3qiaKH_WYtJTQLr9ikQDOSIlJgozXXiKcTDFH-ztcJ0chaIYG1_K40VKXGc-lbWyv63gtrU1ISkY9u4gX5Xc25w9yhKBisJxDP4L0EziEe5tnlGTzZwjtSx3tLwNa7HQAzE9MuoUwR2eqBlVOaa73Ym.zklPuuJeX21ypSpIBgPaJtS0faGT-6QX2-mgkJKzy2o&ApiVersion=2.0"

# headers = {
#     "Authorization": f"Bearer {ACCESS_TOKEN}"
# }

response = requests.get(url)

if response.status_code == 200:
    # print(response.headers)
    content = response.content
    print("Content type:", type(content))
    with open("download.pdf", 'wb') as f:
        f.write(content)
    # files = response.json().get("value", [])
    # print("Files in OneDrive root:")
    # for f in files:
    #     print(f)
    #     print(f"- {f['name']} (id: {f['id']})")
else:
    print("Error:", response.status_code, response.text)
