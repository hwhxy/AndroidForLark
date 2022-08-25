from util import *


class LarkManager:
    # how to get user_access_token:https://open.feishu.cn/api-explorer/?apiName=app_ticket_resend&project=auth&resource=auth&state=&version=v3
    # user_token valid in 2 hours

    def __init__(self, user_access_token, folder_token):
        self.user_access_token = user_access_token
        self.folder_token = folder_token
        self.headers = {
            "Authorization": f"Bearer {self.user_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

    def create_sheet(self, sheet_title):
        url = "https://open.feishu.cn/open-apis/sheets/v3/spreadsheets"
        data = {
            "title": sheet_title,
            "folder_token": self.folder_token
        }
        rsp = requests.post(url, headers=self.headers, json=data, timeout=5, verify=False)
        content = json.loads(rsp.content)
        if "data" in content and "spreadsheet" in content.get("data") and "spreadsheet_token" in content.get(
                "data").get("spreadsheet"):
            spreadsheet_token = content.get("data").get("spreadsheet").get("spreadsheet_token")
            print(f"create_sheet:{spreadsheet_token}")
            return spreadsheet_token
        else:
            print(f"create_sheet:{content}")
            return None

    def add_spreadsheet(self, spreadsheet_token, title):
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/sheets_batch_update"
        data = {
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": title,
                            "index": 0
                        }
                    }
                }
            ]
        }
        rsp = requests.post(url, headers=self.headers, json=data, timeout=5, verify=False)
        content = json.loads(rsp.content)
        if "data" in content and "replies" in content.get("data"):
            addSheet_list = content.get("data").get("replies")
            if len(addSheet_list) > 0 and "addSheet" in addSheet_list[0]:
                if "properties" in addSheet_list[0]["addSheet"] and "sheetId" in addSheet_list[0]["addSheet"][
                    "properties"]:
                    sheetId = addSheet_list[0]["addSheet"]["properties"]["sheetId"]
                    print(f"add_spreadsheet:{sheetId}")
                    return sheetId
        print(f"add_spreadsheet:{content}")
        return None

    def write_sheet(self, data, spreadsheet_token, sheet_id):
        write_sheet_url = f"https://open.feishu.cn/open-apis/sheet/v2/spreadsheets/{spreadsheet_token}/values"
        raw_num, col_num = len(data), len(data[0])
        start = 1
        while start - 1 < raw_num:
            if raw_num - start < 5000:
                end = raw_num
            else:
                end = start + 4999
            write_range = f"{sheet_id}!A{start}:{num_char(col_num)}{end}"
            body = {
                "valueRange": {
                    "range": write_range,
                    "values": data[start - 1:start + 499]
                }
            }
            while True:
                resp = requests.put(write_sheet_url, headers=self.headers, json=body, timeout=5, verify=False)
                if resp.status_code != 200 or json.loads(resp.text).get("msg", "") != "success":
                    print(json.loads(resp.text))
                    continue
                break
            start = start + 500
