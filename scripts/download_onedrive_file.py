import os
import requests

from dotenv import load_dotenv

load_dotenv(override=True)

# ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# Graph API endpoint for listing root drive files
url = "https://my.microsoftpersonalcontent.com/personal/e4a75bfce97e854e/_layouts/15/download.aspx?UniqueId=e97e854e-5bfc-20a7-80e4-730000000000&Translate=false&tempauth=v1e.eyJzaXRlaWQiOiI0ZDFlZDBmOS0wNGYwLTRkZGMtOWUzZS1lYmJhNTMzOGFkMDciLCJhcHBfZGlzcGxheW5hbWUiOiJhenVyZS1haS1pbnRlZ3JhdGlvbiIsImFwcGlkIjoiMDNjMWM2NTQtMmFiYy00OTFlLWIzMTEtM2NjNzg1YjNhMmVmIiwiYXVkIjoiMDAwMDAwMDMtMDAwMC0wZmYxLWNlMDAtMDAwMDAwMDAwMDAwL215Lm1pY3Jvc29mdHBlcnNvbmFsY29udGVudC5jb21AOTE4ODA0MGQtNmM2Ny00YzViLWIxMTItMzZhMzA0YjY2ZGFkIiwiZXhwIjoiMTc1Njk2OTYwOSJ9.BmkPWDYxr4ynhFJp29TKMSoNmHrwHcBc4hKLygyZGww2c1V80Fi_TA3l4I6HUmoXVjMOCpkuFek2G7FvyYH74Xut3A8rBHl6g2Iq6jXjfXamIaHt1_KiBtkgluY3zlxVNU5BturABK7itOhmQ1Q1eMFUkpbNKbchIQrE9B2UAT9_GRm5askI-vuLRor4yULko-jQ1A14zO9Thb76xlfmoQ27GKPHhNvccA8rGaDq990hvS_VOkccO-ZTvVNxPAQ9dfQ7GwCWWg73PIJ_xhXPFGBdCwXCefVF79Gt4IBvmcA9GAZhoQTxbOxrI7CCoRSs2hyty4SfcPPFBU4NG1ISQAmMQPb6uJd5c0QO2797NSEWNXTzPIRcK5kbN6CylEMt1ZyDNwbwS8b6k8KbcPV07RB5pos7pPJeQiJPFF1RWqTUlRK_UlU_HQpdgU5JZ4Nz.gt0Am-plK7Cf5T8Pd7IH0sun3dSNUD6gs6YbBk_4h74&ApiVersion=2.0"

# headers = {
#     "Authorization": f"Bearer {ACCESS_TOKEN}"
# }

response = requests.get(url)

if response.status_code == 200:
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
