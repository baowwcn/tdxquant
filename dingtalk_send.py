import json
import urllib.request
import urllib.parse

DINGTALK_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=441620abea617c90504c220f757006a98174facd87b102554bc177aa24837e3f"

def send_dingtalk(message: str, at_mobiles: list = None, is_at_all: bool = False):
    url = DINGTALK_WEBHOOK

    data = {
        "msgtype": "text",
        "text": {
            "content": message
        },
        "at": {
            "atMobiles": at_mobiles or [],
            "isAtAll": is_at_all
        }
    }

    json_data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=json_data, method='POST')
    req.add_header('Content-Type', 'application/json')

    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        if result.get('errcode') == 0:
            print("发送成功")
        else:
            print(f"发送失败: {result}")
        return result

if __name__ == "__main__":
    send_dingtalk("TEST: ok")