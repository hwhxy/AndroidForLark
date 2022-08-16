from util import *


# run app.activity.info -a xxx
# run app.service.info -a xxx
# run app.broadcast.info -a xxx
# run app.provider.info -a xxx
# run scanner.provider.finduris -a xxx

def judge_activity_file(activity_list, real_filename):
    for activity in activity_list:
        if f"{activity.split('.')[-1]}.java" in real_filename:
            return activity
    return None


def init_scan_result(component_list):
    result = {}
    for component in component_list:
        result[component] = {
            "condition": component_list[component]["condition"],
            "is_export": component_list[component]["is_export"]
        }
    return result


def scaner_file(result, project_dir, activity_list):
    file = os.listdir(project_dir)
    for f in file:
        real_dir = path.join(project_dir, f)
        if path.isfile(real_dir):
            if real_dir.endswith(".java"):
                activity = judge_activity_file(activity_list, real_dir)
                if activity:
                    special_key_list = judge_file_string(path.abspath(real_dir))
                    result[activity]["dir"] = real_dir
                    result[activity]["special_keywords"] = special_key_list
        elif path.isdir(real_dir):
            scaner_file(result, real_dir, activity_list)
        else:
            print("其他情况")
            pass
    return result


def judge_file_string(file_path):
    with open(file_path, encoding=u'utf-8', errors='ignore') as f:
        content = f.read()
    output = []
    if "onHandleIntent(".lower() in content.lower():
        output.append(f"存在:onHandleIntent")
    if "getIntent(".lower() in content.lower():
        output.append(f"存在:getIntent")
    if "getStringExtra(".lower() in content.lower():
        output.append(f"存在:getStringExtra")
    if "getExtras(".lower() in content.lower():
        output.append(f"存在:getExtras")
    if "startService(".lower() in content.lower():
        output.append(f"存在:startService")
    if "startActivity(".lower() in content.lower():
        output.append(f"存在:startActivity")
    return output


def get_component_name(str):
    if "<activity " in str:
        return "activity"
    elif "<service " in str:
        return "service"
    elif "<receiver " in str:
        return "receiver"
    else:
        return None


def get_export_activity(androidmanifest_dir):
    with open(androidmanifest_dir, "r") as f:
        start = False
        tmp_activity_name = ""
        export_activity = {"activity": {}, "service": {}, "receiver": {}}
        for line in f.readlines():
            if "<activity " in line or "<service " in line or "<receiver " in line:
                component_name = get_component_name(line.strip())
                activity_name = line.split("android:name=\"")[1].split("\"")[0]
                tmp_activity_name = activity_name
                export_activity[component_name][tmp_activity_name] = {"condition": [], "is_export": ""}
                if "android:exported=\"false\"" in line:
                    export_activity[component_name][tmp_activity_name]["is_export"] = "exported=False"
                elif "android:exported=\"true\"" in line:
                    export_activity[component_name][tmp_activity_name]["is_export"] = "exported=True"
                else:
                    if "/>" in line:
                        export_activity[component_name][tmp_activity_name]["is_export"] = "exported=False"
                    else:
                        export_activity[component_name][tmp_activity_name]["is_export"] = "exported=True"
                start = False if "/>" in line else True
                continue
            if start:
                if "<intent-filter>" in line:
                    start = True
                elif "</intent-filter>" in line:
                    start = False
                else:
                    export_activity[component_name][tmp_activity_name]["condition"].append(line.strip())
        return export_activity

@click.command()
@click.option('--project_dir', help='jadx -e xxx.apk,such as xxxxx_standalone')
def main(project_dir):
    lark_manager = get_larkmanager(
        user_access_token="",
        folder_token=""
    )
    sheet_title = project_dir.split('/')[-1]
    spreadsheet_token = lark_manager.create_sheet(sheet_title)
    androidmanifest_dir = f"{project_dir}/app/src/main/AndroidManifest.xml"
    export_list = get_export_activity(androidmanifest_dir)
    for component_type in export_list:
        sheet_id = lark_manager.add_spreadsheet(spreadsheet_token, component_type)
        lark_list = [["component_type", "component_name", "is_export", "component_condition", "component_dir",
                      "special_keywords"]]
        component_list = export_list[component_type]
        result = init_scan_result(component_list)
        result = scaner_file(result, project_dir, component_list)
        for activity in result:
            component_condition = json.dumps(result[activity].get("condition", "")).encode().decode('unicode_escape')
            is_export = result[activity].get("is_export", "")
            component_dir = result[activity].get("dir", "").encode().decode('unicode_escape')
            component_special_keywords = json.dumps(result[activity].get("special_keywords", "")).encode().decode(
                'unicode_escape')
            lark_list.append([component_type,
                              activity,
                              is_export,
                              component_condition,
                              component_dir,
                              component_special_keywords
                              ])
        lark_manager.write_sheet(lark_list, spreadsheet_token, sheet_id)
    print(f"https://i9jmwfqnis.feishu.cn/sheets/{spreadsheet_token}")


if __name__ == '__main__':
    main()
