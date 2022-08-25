import re

from util import *
from LarkManager import LarkManager


# run app.activity.info -a xxx
# run app.service.info -a xxx
# run app.broadcast.info -a xxx
# run app.provider.info -a xxx
# run scanner.provider.finduris -a xxx

class ComponentEngine:
    def __init__(self, apk_project_dir, manifest_dir):
        self.project_dir = apk_project_dir
        self.apk_project_dir = apk_project_dir
        self.manifest_dir = manifest_dir
        self.total_file_lists = []
        self.sensitive_keys = ["onHandleIntent(", "getIntent(", "getStringExtra(",
                               "getExtras(", "startService(", "startActivity("]
        self.get_total_filelist()
        self.component_dict = self.get_export_component()
        self.scan_componet()

    def get_component_name(self, str):
        if "<activity " in str:
            return "activity"
        elif "<service " in str:
            return "service"
        elif "<receiver " in str:
            return "receiver"
        else:
            return None

    def get_export_component(self):
        export_component_lists = {"activity": {}, "service": {}, "receiver": {}}
        start = False
        tmp_activity_name = ""
        with open(self.manifest_dir, "r") as f:
            for line in f.readlines():
                if "<activity " in line or "<service " in line or "<receiver " in line:
                    component_name = self.get_component_name(line.strip())
                    activity_name = line.split("android:name=\"")[1].split("\"")[0]
                    tmp_activity_name = activity_name
                    export_component_lists[component_name][tmp_activity_name] = {"condition": [], "is_export": ""}
                    if "android:exported=\"false\"" in line:
                        export_component_lists[component_name][tmp_activity_name]["is_export"] = "exported=False"
                    elif "android:exported=\"true\"" in line:
                        export_component_lists[component_name][tmp_activity_name]["is_export"] = "exported=True"
                    else:
                        if "/>" in line:
                            export_component_lists[component_name][tmp_activity_name]["is_export"] = "exported=False"
                        else:
                            export_component_lists[component_name][tmp_activity_name]["is_export"] = "exported=True"
                    start = False if "/>" in line else True
                    continue
                if start:
                    if "<intent-filter>" in line:
                        start = True
                    elif "</intent-filter>" in line:
                        start = False
                    else:
                        export_component_lists[component_name][tmp_activity_name]["condition"].append(line.strip())
        return export_component_lists

    def get_total_filelist(self, root_project_dir=None):
        if not root_project_dir:
            root_project_dir = self.apk_project_dir
        filename_list = os.listdir(root_project_dir)
        for f in filename_list:
            real_dir = path.join(root_project_dir, f)
            if path.isfile(real_dir):
                if real_dir not in self.total_file_lists:
                    self.total_file_lists.append(real_dir)
            elif path.isdir(real_dir):
                self.get_total_filelist(real_dir)
            else:
                pass
        return self.total_file_lists

    def get_sensitive_key_file(self, file_content):
        output = []
        for sensitive_key in self.sensitive_keys:
            if sensitive_key.lower() in file_content.lower():
                output.append(f"存在:{sensitive_key}")
        return output

    def scan_componet(self):
        if not self.total_file_lists:
            self.get_total_filelist()
        for file_dir in self.total_file_lists:
            if file_dir.endswith(".java") and len(file_dir.split(".")) > 2:
                for component_type in self.component_dict:
                    for component_name in self.component_dict.get(component_type):
                        if component_name.split(".")[-1].lower() in file_dir.lower():
                            with open(file_dir, encoding=u'utf-8', errors='ignore') as f:
                                file_content = f.read()
                            self.component_dict.get(component_type).get(component_name)[
                                "special_keywords"] = self.get_sensitive_key_file(
                                file_content)
        return

    def scan_url(self):
        url_lists = []
        if not self.total_file_lists:
            self.get_total_filelist()
        for file_dir in self.total_file_lists:
            with open(file_dir, encoding=u'utf-8', errors='ignore') as f:
                file_content = f.read()
            match_url = re.findall('https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', file_content)
            for url in match_url:
                if url not in url_lists:
                    url_lists.append(url)
        return url_lists


def upload_component_export_lark(component_engine, lark_manager, spreadsheet_token):
    for component_type in component_engine.component_dict:
        sheet_id = lark_manager.add_spreadsheet(spreadsheet_token, component_type)
        lark_list = [
            [
                "component_type", "component_name", "is_export", "component_condition", "special_keywords"
            ]
        ]
        for component in component_engine.component_dict.get(component_type):
            component_detail = component_engine.component_dict.get(component_type).get(component)
            component_condition = json.dumps(component_detail.get("condition", "")).encode().decode('unicode_escape')
            is_export = component_detail.get("is_export", "")
            component_special_keywords = json.dumps(component_detail.get("special_keywords", "")).encode().decode(
                'unicode_escape')
            lark_list.append([
                component_type,
                component,
                is_export,
                component_condition,
                component_special_keywords
            ])
        lark_manager.write_sheet(lark_list, spreadsheet_token, sheet_id)
    return


def upload_apk_url(component_engine, lark_manager, spreadsheet_token):
    url_lists = component_engine.scan_url()
    sheet_id = lark_manager.add_spreadsheet(spreadsheet_token, "url fuzz")
    lark_list = [
        [
            "URL"
        ]
    ]
    for url in url_lists:
        lark_list.append([url])
    lark_manager.write_sheet(lark_list, spreadsheet_token, sheet_id)


@click.command()
@click.option('--project_dir', help='jadx -e xxx.apk,such as xxxxx_standalone')
def main(project_dir):
    # how to get user_access_token:https://open.feishu.cn/api-explorer/{}?apiName=app_ticket_resend&project=auth&resource=auth&state=&version=v3
    # user_token valid in 2 hours
    lark_manager = LarkManager(
        user_access_token="",
        folder_token=""
    )
    component_engine = ComponentEngine(
        apk_project_dir=project_dir,
        manifest_dir=f"{project_dir}/app/src/main/AndroidManifest.xml"
    )

    sheet_title = component_engine.project_dir.split('/')[-1]
    spreadsheet_token = lark_manager.create_sheet(sheet_title)

    upload_component_export_lark(component_engine, lark_manager, spreadsheet_token)
    upload_apk_url(component_engine, lark_manager, spreadsheet_token)
    print(f"https://xxxx.feishu.cn/sheets/{spreadsheet_token}")


if __name__ == '__main__':
    main()
