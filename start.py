import json
import re
from datetime import datetime
from time import sleep, strftime
from tkinter import filedialog
import os
import os.path
import random
import traceback
import filetype
import requests
import schedule

headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 15; V2218A Build/AP3A.240905.015.A2; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/144.0.7559.109 Mobile Safari/537.36'
}

# 配置文件路径
CONFIG_FILE = "users.json"
# 日志文件
log_file = "clockin.log"

# 添加一个全局变量来控制任务执行
TASK_RUNNING = False
# 全局图片文件ID列表
global_pictureAry = []


# 添加配置文件管理函数
def load_config():
    """加载或创建配置文件"""
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "users": [
                {
                    "username": "",
                    "password": "",
                    "schoolid": "",
                    "statusName": "",
                    "address": "",
                    "location": "",
                    "clock_in_time": "",
                    "remark": "",
                    "pictureAry": [],
                    "enabled": False,
                    "last_clockin_date": None,
                    "clockin_version": "old2"
                }
            ]
        }
        save_config(default_config)
        print("\n[提示] 已创建默认配置文件 users.json")
        print("[提示] 请使用用户管理功能添加用户信息")
        return default_config

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 确保每个用户都有必要的字段
            for user in config['users']:
                if 'clockin_version' not in user:
                    user['clockin_version'] = 'old1'
                if 'last_clockin_date' not in user:
                    user['last_clockin_date'] = None
                if 'enabled' not in user:
                    user['enabled'] = False
                if 'pictureAry' not in user:
                    user['pictureAry'] = []
                if 'statusName' not in user:
                    user['statusName'] = "上班"
            return config
    except Exception as e:
        print(f"\n[错误] 配置文件读取失败: {str(e)}")
        print("[提示] 将创建新的配置文件")
        os.rename(CONFIG_FILE, f"{CONFIG_FILE}.bak")  # 备份损坏的配置文件
        return load_config()  # 递归调用创建新配置


def save_config(config):
    """保存配置到文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"\n[错误] 配置文件保存失败: {str(e)}")


def manage_users():
    config = load_config()
    while True:
        print("\n=== 用户管理 ===")
        print("当前用户列表：")
        for i, user in enumerate(config['users'], 1):
            status = "启用" if user['enabled'] else "禁用"
            version = user.get('clockin_version', 'old1')
            statusName = user.get('statusName', '上班')
            print(f"{i}. {user['username']} - {user['clock_in_time']} - {statusName} - {status} - {version}版")
        print("\n操作选项：")
        print("1. 添加用户")
        print("2. 修改用户")
        print("3. 删除用户")
        print("4. 启用/禁用用户")
        print("5. 管理用户图片")
        print("6. 返回主菜单")

        choice = input("\n请选择操作：")

        if choice == "1":
            new_user = {
                "username": input("请输入用户名："),
                "password": input("请输入密码："),
                "schoolid": input("请输入学号ID（可选）："),
                "statusName": input("请输入签到类型(上班/下班)：") or "上班",
                "address": input("请输入打卡地址："),
                "location": input("请输入经纬度坐标(坐标拾取器)："),
                "clock_in_time": input("请输入打卡时间（格式如09:00）："),
                "remark": input("请输入备注（可选）："),
                "pictureAry": [],
                "enabled": True,
                "clockin_version": input("请选择打卡版本(new/old1/old2)：") or "old2"
            }
            config['users'].append(new_user)
            save_config(config)
            print("用户添加成功！")

        elif choice == "2":
            user_idx = int(input("请输入要修改的用户序号：")) - 1
            if 0 <= user_idx < len(config['users']):
                user = config['users'][user_idx]
                print(f"\n修改用户 {user['username']} 的信息：")
                user['username'] = input(f"用户名 ({user['username']})：") or user['username']
                user['password'] = input(f"密码 (回车保持不变)：") or user['password']
                user['schoolid'] = input(f"学号ID ({user['schoolid']})：") or user['schoolid']
                user['statusName'] = input(f"签到类型 ({user.get('statusName', '上班')})：") or user.get('statusName',
                                                                                                        '上班')
                user['address'] = input(f"打卡地址 ({user['address']})：") or user['address']
                user['location'] = input(f"经纬度坐标 ({user['location']})：") or user['location']
                user['clock_in_time'] = input(f"打卡时间 ({user['clock_in_time']})：") or user['clock_in_time']
                user['remark'] = input(f"备注 ({user['remark']})：") or user['remark']
                user['clockin_version'] = input(
                    f"打卡版本(new/old1/old2) ({user.get('clockin_version', 'old1')})：") or user.get('clockin_version',
                                                                                                     'old1')
                save_config(config)
                print("用户信息修改成功！")
            else:
                print("无效的用户序号！")

        elif choice == "3":
            user_idx = int(input("请输入要删除的用户序号：")) - 1
            if 0 <= user_idx < len(config['users']):
                del config['users'][user_idx]
                save_config(config)
                print("用户删除成功！")
            else:
                print("无效的用户序号！")

        elif choice == "4":
            user_idx = int(input("请输入要切换状态的用户序号：")) - 1
            if 0 <= user_idx < len(config['users']):
                config['users'][user_idx]['enabled'] = not config['users'][user_idx]['enabled']
                save_config(config)
                status = "启用" if config['users'][user_idx]['enabled'] else "禁用"
                print(f"用户已{status}！")
            else:
                print("无效的用户序号！")

        elif choice == "5":
            user_idx = int(input("请输入要管理图片的用户序号：")) - 1
            if 0 <= user_idx < len(config['users']):
                user = config['users'][user_idx]
                print(f"\n管理用户 {user['username']} 的图片")
                print(f"当前图片列表: {user['pictureAry']}")
                print("\n操作选项：")
                print("1. 上传新图片")
                print("2. 清空图片列表")
                print("3. 返回")

                img_choice = input("请选择：")
                if img_choice == "1":
                    # 保存当前全局变量以便恢复
                    global_save = {
                        'username': user['username'],
                        'password': user['password'],
                        'schoolid': user['schoolid']
                    }

                    # 上传图片
                    uploaded_ids = upload_img(user)

                    # 将上传的图片ID添加到用户配置
                    if uploaded_ids:
                        user['pictureAry'].extend(uploaded_ids)
                        user['pictureAry'] = list(set(user['pictureAry']))  # 去重
                        save_config(config)
                        print(f"图片上传成功！当前图片列表: {user['pictureAry']}")
                elif img_choice == "2":
                    user['pictureAry'] = []
                    save_config(config)
                    print("图片列表已清空！")
            else:
                print("无效的用户序号！")

        elif choice == "6":
            break


# 添加日志函数
def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"

    print(log_entry.strip())  # 在控制台显示

    # 写入日志文件
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)


def new_clockin(session, user_config, clock_type=None):
    url = "https://sx.chaoxing.com/internship/planUser/myPlanList"
    res = session.get(url, headers=headers)
    if res.url == url:
        res = res.json()
    else:
        return [0, "登录失败，请检查用户名密码后重试"]
    if res["result"] == 0 and len(res["data"]) > 0:
        planlist = []
        for d in res["data"]:
            tempdict = {"planName": d["planName"], "planId": d["planId"], "fid": d["fid"], "planUserId": d["id"]}
            if d["planStatus"] == 1:
                tempdict["planStatus"] = "进行中"
            elif d["planStatus"] == 2:
                tempdict["planStatus"] = "已结束"
            elif d["planStatus"] == 3:
                tempdict["planStatus"] = "未开始"
            if d["sxStatus"] == 0:
                tempdict["sxStatus"] = "未实习"
            elif d["sxStatus"] == 1:
                tempdict["sxStatus"] = "实习中"
            elif d["sxStatus"] == 2:
                tempdict["sxStatus"] = "免实习"
            elif d["sxStatus"] == 3:
                tempdict["sxStatus"] = "终止实习"
            tempdict["planStartTime"] = d["planStartTime"]
            tempdict["planEndTime"] = d["planEndTime"]
            tempdict["recruitNames"] = d["recruitNames"]
            planlist.append(tempdict)
        print("{} {:<50} {:<10} {:<6} {:<23} {}".format("ID", "实习计划名称", "实习计划状态", "实习状态", "实习时间",
                                                        "实习岗位"))
        print("-" * 120)
        inputid = 0
        for d in planlist:
            inputid += 1
            print("{:<2} {:<40} {:<12} {:<7} {:<25} {}".format(inputid, d["planName"], d["planStatus"], d["sxStatus"],
                                                               d["planStartTime"] + "-" + d["planEndTime"],
                                                               d["recruitNames"]))
        while True:
            inputid = input("输入要进行实习打卡的ID：")
            try:
                inputid = int(inputid)
                if 0 < inputid <= len(planlist):
                    break
                else:
                    print("ID输入错误，请重新输入")
            except ValueError:
                print("ID输入错误，请重新输入")
        select_plan = planlist[inputid - 1]
        getDataByIdurl = "https://sx.chaoxing.com/internship/planUser/getDataById?planId={}&planUserId={}".format(
            select_plan["planId"], select_plan["planUserId"])
        res = session.get(getDataByIdurl, headers=headers)
        if res.url == getDataByIdurl:
            res = res.json()
            if res["result"] == 0 and res["data"] is not None:
                if len(res["data"]["userPeriods"]) > 0:
                    workStart = res["data"]["userPeriods"][0]["planUserRecruit"]["recruitVo"]["workStart"]
                    workEnd = res["data"]["userPeriods"][0]["planUserRecruit"]["recruitVo"]["workEnd"]
                else:
                    workStart = ""
                    workEnd = ""
                dgsxpcurl = "https://sx.chaoxing.com/internship/dgsxpc/{}".format(select_plan["planId"])
                res = session.get(dgsxpcurl, headers=headers)
                if res.url == dgsxpcurl:
                    res = res.json()
                    if res["result"] == 0 and res["data"] is not None:
                        isontimesign = res["data"]["isontimesign"]
                        allowOffset = res["data"]["offset"] or 2000
                        dateurl = "https://sx.chaoxing.com/internship/clockin-user/get/stu/{}/date?date={}".format(
                            select_plan["planId"],
                            datetime.now().strftime("%Y-%m-%d")
                        )
                        res = session.get(dateurl, headers=headers)
                        if res.url == dateurl:
                            res = res.json()
                            if res["result"] == 0 and res["data"] is not None:
                                cxid = res["data"]["cxid"]
                                clockinId = res["data"]["id"]
                                if clock_type is not None:
                                    clockintype = clock_type
                                    statusName = user_config.get('statusName', '上班')
                                else:
                                    statusName = user_config.get('statusName', '上班')
                                    if statusName == "上班":
                                        clockintype = "0"
                                    elif statusName == "下班":
                                        clockintype = "1"
                                    else:
                                        clockintype = "0"  # 默认上班
                                recruitId = res["data"]["recruitId"]
                                pcid = res["data"]["pcid"]
                                pcmajorid = res["data"]["pcmajorid"]
                                offduty = 0
                                if isontimesign:
                                    addclockinurl = "https://sx.chaoxing.com/internship/clockin-user/stu/addclockin/{}".format(
                                        cxid)
                                else:
                                    addclockinurl = "https://sx.chaoxing.com/internship/clockin-user/stu/addclockinOnceInDay/{}".format(
                                        cxid)
                                data = {
                                    "id": clockinId,
                                    "type": clockintype,
                                    "recruitId": recruitId,
                                    "pcid": pcid,
                                    "pcmajorid": pcmajorid,
                                    "address": user_config['address'],
                                    "geolocation": user_config['location'],
                                    "remark": user_config.get('remark', ''),
                                    "workStart": workStart,
                                    "workEnd": workEnd,
                                    "images": json.dumps(user_config.get('pictureAry', [])) if user_config.get(
                                        'pictureAry') else "",
                                    "allowOffset": allowOffset,
                                    "offset": "NaN",
                                    "offduty": offduty,
                                    "codecolor": "",
                                    "havestar": "",
                                    "worktype": "",
                                    "changeLocation": "",
                                    "statusName": statusName,
                                    "shouldSignAddress": ""
                                }
                                res = session.post(addclockinurl, headers=headers, data=data)
                                if res.url == addclockinurl:
                                    return [1, res.text]
                                else:
                                    return [0, "登录失败，请检查用户名密码后重试"]
                            else:
                                return [2, res["errorMsg"]]
                        else:
                            return [0, "登录失败，请检查用户名密码后重试"]
                    else:
                        return [2, res["errorMsg"]]
                else:
                    return [0, "登录失败，请检查用户名密码后重试"]
            else:
                return [2, res["errorMsg"]]
        else:
            return [0, "登录失败，请检查用户名密码后重试"]
    else:
        return [2, "未找到新版实习打卡任务"]


def old_clockin1(session, user_config):
    """
    旧版页面1打卡
    :param session: 会话对象
    :param user_config: 用户配置
    """
    res = session.get("https://www.dgsx.chaoxing.com/form/mobile/signIndex", headers=headers)
    txt = res.text
    if txt != "您还没有被分配实习计划。":
        if "用户登录状态异常，请重新登录！" not in txt:
            planName = re.search(r"planName: '(.*)',", txt, re.I).groups()[0]
            clockin_type = re.search(r"type: '(.*)',", txt, re.I).groups()[0]
            signType = re.search(r"signType: '(.*)',", txt, re.I).groups()[0]
            workAddress = re.search(r'<input type="hidden" id="workAddress" value="(.*)"/>', txt, re.I).groups()[0]
            geolocation = re.search(r'<input type="hidden" id="workLocation" value="(.*)">', txt, re.I).groups()[0]
            allowOffset = re.search(r'<input type="hidden" id="allowOffset" value="(.*)"/>', txt, re.I).groups()[0]
            signSettingId = re.search(r'<input type="hidden" id="signSettingId" value="(.*)"/>', txt, re.I).groups()[0]

            # 根据statusName确定type
            statusName = user_config.get('statusName', '上班')
            if statusName == "上班":
                clockin_type = "0"
            elif statusName == "下班":
                clockin_type = "1"

            data = {
                "planName": planName,
                "type": clockin_type,
                "signType": signType,
                "address": user_config['address'],
                "geolocation": user_config['location'],
                "remark": user_config.get('remark', ''),
                "images": json.dumps(user_config.get('pictureAry', [])) if user_config.get('pictureAry') else "",
                "offset": 0,
                "allowOffset": allowOffset,
                "signSettingId": signSettingId
            }
            res = session.post("https://www.dgsx.chaoxing.com/form/mobile/saveSign", headers=headers, data=data)
            return [1, res.text]
        else:
            return [0, "登录失败，请检查用户名密码后重试"]
    else:
        return [2, "未找到旧版页面1实习打卡任务"]


def old_clockin2(session, user_config):
    """
    旧版页面2打卡
    :param session: 会话对象
    :param user_config: 用户配置
    """
    res = session.get("https://i.chaoxing.com/base/cacheUserOrg", headers=headers).json()
    site = res["site"]
    for d in site:
        fid = str(d["fid"])
        session.cookies.set("wfwfid", fid)
        res = session.get("https://www.dgsx.chaoxing.com/mobile/clockin/show", headers=headers)
        txt = res.text
        if res.status_code == 200:
            if "alert('请先登录');" in txt or 'alert("实习计划已进入总结期或实习已终止，无法签到");' in txt:
                continue
            elif "用户登录状态异常，请重新登录！" not in txt:
                clockinId = re.search(r'<input id="clockinId" type="hidden" value="(.*)">', txt, re.I).groups()[0]
                recruitId = re.search(r'<input type="hidden" id="recruitId" value="(.*)" />', txt, re.I).groups()[0]
                pcid = re.search(r'<input type="hidden" id="pcid" value="(.*)" />', txt, re.I).groups()[0]
                pcmajorid = re.search(r'<input type="hidden" id="pcmajorid" value="(.*)" />', txt, re.I).groups()[0]
                should_bntover = re.search(
                    r'''<dd class="should_bntover" selid="(.*)" workStart='(.*)' workEnd='(.*)'>''', txt, re.I).groups()
                workStart = should_bntover[1]
                workEnd = should_bntover[2]
                allowOffset = re.search(r'<input type="hidden" id="allowOffset" value="(.*)"/>', txt, re.I).groups()[0]
                changeLocation = \
                re.search(r'<input type="text" name="location" id="location" value="(.*)" hidden/>', txt,
                          re.I).groups()[0]
                if re.search(r'<input id="workLocation" type="hidden" >', txt, re.I) is None:
                    if re.search(r'<input id="workLocation" type="hidden" value="(.*)">', txt, re.I) is None:
                        offset = "NaN"
                    else:
                        offset = re.search(r'<input id="workLocation" type="hidden" value="(.*)">', txt, re.I).groups()[
                            0]
                else:
                    offset = "NaN"

                # 根据statusName确定type
                statusName = user_config.get('statusName', '上班')
                if statusName == "上班":
                    clockin_type = 0
                elif statusName == "下班":
                    clockin_type = 1
                else:
                    clockin_type = 0

                data = {
                    "id": clockinId,
                    "type": clockin_type,
                    "recruitId": recruitId,
                    "pcid": pcid,
                    "pcmajorid": pcmajorid,
                    "address": user_config['address'],
                    "geolocation": user_config['location'],
                    "remark": user_config.get('remark', ''),
                    "workStart": workStart,
                    "workEnd": workEnd,
                    "images": json.dumps(user_config.get('pictureAry', [])) if user_config.get('pictureAry') else "",
                    "allowOffset": allowOffset,
                    "offset": offset,
                    "offduty": 0,
                    "changeLocation": changeLocation,
                    "statusName": statusName
                }
                res = session.post("https://www.dgsx.chaoxing.com/mobile/clockin/addclockin2", headers=headers,
                                   data=data)
                return [1, res.text]
            else:
                return [0, "登录失败，请检查用户名密码后重试"]
    return [2, "未找到旧版页面2实习打卡任务"]


def clockin_main(user_config, clock_type=None):
    """
    执行打卡
    :param user_config: 用户配置字典，包含所有用户信息
    :param clock_type: 打卡类型（"0"上班，"1"下班）
    """
    session = requests.session()
    resp = session.post(
        'https://passport2.chaoxing.com/api/login?name={}&pwd={}&schoolid={}&verify=0'.format(
            user_config['username'],
            user_config['password'],
            user_config['schoolid']
        ),
        headers=headers
    ).json()

    if resp["result"]:
        print(f"用户 {user_config['username']} 登录成功")

        # 使用用户配置中的版本
        version = user_config.get('clockin_version', 'old1')

        if version == 'new':
            print("使用新版打卡")
            result = new_clockin(session, user_config, clock_type)
            if result[0] == 1:
                return result[1]
            return f"新版打卡失败: {result[1]}"
        elif version == 'old1':
            print("使用旧版页面1打卡")
            result = old_clockin1(session, user_config)
            if result[0] == 1:
                return result[1]
            return f"旧版页面1打卡失败: {result[1]}"
        elif version == 'old2':
            print("使用旧版页面2打卡")
            result = old_clockin2(session, user_config)
            if result[0] == 1:
                return result[1]
            return f"旧版页面2打卡失败: {result[1]}"
        else:
            return f"未知的打卡版本: {version}"
    else:
        print(f"用户 {user_config['username']} 登录失败，请检查用户名密码")
        return "登录失败"


def upload_img(user_config=None):
    """
    上传图片
    :param user_config: 用户配置，如果为None则使用全局变量
    :return: 上传成功的图片ID列表
    """
    if user_config:
        username = user_config['username']
        password = user_config['password']
        schoolid = user_config['schoolid']
    else:
        # 使用默认配置
        config = load_config()
        if config['users']:
            user_config = config['users'][0]
            username = user_config['username']
            password = user_config['password']
            schoolid = user_config['schoolid']
        else:
            print("没有可用的用户配置")
            return []

    session = requests.session()
    resp = session.post(
        'https://passport2.chaoxing.com/api/login?name={}&pwd={}&schoolid={}&verify=0'.format(
            username, password, schoolid
        ),
        headers=headers
    ).json()

    uploaded_ids = []

    if resp["result"]:
        while True:
            print("\n请选择要上传的图片文件（支持jpg、png、gif、webp、bmp格式）")
            print("可以一次选择多个文件")
            filepaths = filedialog.askopenfilenames(
                title="选择图片文件",
                filetypes=(("图片文件", "*.jpg;*.jpeg;*.png;*.gif;*.webp;*.bmp"), ("所有文件", "*.*"))
            )

            if not filepaths:
                print("没有选择文件，返回")
                break

            for filepath in filepaths:
                file_type = filetype.guess(filepath)
                if file_type is None:
                    print(f"文件 {os.path.basename(filepath)} 不是图片文件，跳过")
                    continue
                elif file_type.extension not in ["jpg", "jpeg", "png", "gif", "webp", "bmp"]:
                    print(f"文件 {os.path.basename(filepath)} 格式不支持，跳过")
                    continue

                uploadurl = "https://sx.chaoxing.com/internship/usts/file"
                try:
                    with open(filepath, 'rb') as file:
                        files = {'file': file}
                        res = session.post(uploadurl, headers=headers, files=files)

                    if res.url == uploadurl:
                        res_json = res.json()
                        if res_json["result"] == 0:
                            objectid = res_json["data"]["objectid"]
                            uploaded_ids.append(objectid)
                            print(f"文件 {os.path.basename(filepath)} 上传成功，文件ID: {objectid}")
                        else:
                            print(f"文件 {os.path.basename(filepath)} 上传失败: {res_json.get('errorMsg', '未知错误')}")
                    else:
                        print(f"文件 {os.path.basename(filepath)} 上传失败: 登录状态异常")

                except Exception as e:
                    print(f"文件 {os.path.basename(filepath)} 上传异常: {str(e)}")

            if uploaded_ids:
                print(f"\n成功上传 {len(uploaded_ids)} 个文件")
                print("文件ID列表:", uploaded_ids)
                print("\n请在用户管理中将这些ID添加到用户的pictureAry字段中")

            more = input("\n是否继续上传更多图片？(y/n): ")
            if more.lower() != 'y':
                break

    else:
        print("登录失败，请检查用户名密码是否正确")

    return uploaded_ids


def schedule_clock_in():
    global TASK_RUNNING

    if TASK_RUNNING:
        return

    try:
        TASK_RUNNING = True
        config = load_config()
        current_date = datetime.now().date().isoformat()
        current_time = datetime.now().strftime("%H:%M")

        # 重置过期的打卡记录
        for user in config['users']:
            if user.get('last_clockin_date') and user['last_clockin_date'] != current_date:
                user['last_clockin_date'] = None
        save_config(config)

        # 找到需要打卡的用户
        current_users = sorted(
            [user for user in config['users']
             if user['enabled']
             and user.get('last_clockin_date') != current_date
             and user['clock_in_time'] == current_time],
            key=lambda x: x['username']
        )

        if not current_users:
            log_message(f"当前时间 {current_time} 没有需要打卡的用户")
            return

        log_message(f"=== 开始执行 {current_time} 的打卡任务 ===")
        log_message(f"待打卡用户：{', '.join(f'{u['username']}({u.get('remark', '无备注')})' for u in current_users)}")

        for i, user in enumerate(current_users, 1):
            log_message(f"正在为第 {i}/{len(current_users)} 个用户打卡")
            log_message(f"开始为用户 {user['username']} ({user.get('remark', '无备注')}) 执行打卡")
            try:
                # 执行打卡
                result = clockin_main(user)
                log_message(f"打卡返回结果: {result}")

                # 改进打卡结果验证
                success_keywords = ["打卡成功", "今日已打卡", "已经打过卡", "签到成功", "成功", "true", "True",
                                    "result", "200", "ok", "OK"]
                is_success = False
                result_str = str(result)

                # 检查JSON响应
                if "result" in result_str or "{" in result_str:
                    try:
                        result_json = json.loads(result_str)
                        if isinstance(result_json, dict):
                            if result_json.get("result") == True or result_json.get("result") == 1:
                                is_success = True
                            elif "result" in result_json and result_json["result"] == 0:
                                # 有些接口返回result: 0表示成功
                                is_success = True
                            elif "msg" in result_json and any(
                                    keyword in str(result_json.get("msg", "")).lower() for keyword in ["成功", "ok"]):
                                is_success = True
                    except:
                        pass

                # 检查字符串关键词
                if not is_success:
                    is_success = any(keyword.lower() in result_str.lower() for keyword in success_keywords)

                if is_success:
                    user['last_clockin_date'] = current_date
                    save_config(config)
                    log_message(f"用户 {user['username']} 自动打卡成功")
                    # 成功后等待5秒再打卡下一个用户
                    if i < len(current_users):
                        log_message(f"等待5秒后开始下一个用户的打卡...")
                        sleep(5)
                else:
                    log_message(f"用户 {user['username']} 打卡失败，返回信息: {result_str}")
                    # 重试一次
                    log_message(f"等待5秒后尝试重新打卡...")
                    sleep(5)
                    retry_result = clockin_main(user)
                    log_message(f"重试返回结果: {retry_result}")

                    retry_str = str(retry_result)
                    is_retry_success = any(keyword.lower() in retry_str.lower() for keyword in success_keywords)
                    if is_retry_success:
                        user['last_clockin_date'] = current_date
                        save_config(config)
                        log_message(f"用户 {user['username']} 重试打卡成功")
                        # 成功后等待5秒再打卡下一个用户
                        if i < len(current_users):
                            log_message(f"等待5秒后开始下一个用户的打卡...")
                            sleep(5)
                    else:
                        log_message(f"用户 {user['username']} 重试打卡失败，返回信息: {retry_str}")
                        # 失败后等待5秒再尝试下一个用户
                        if i < len(current_users):
                            log_message(f"等待5秒后开始下一个用户的打卡...")
                            sleep(5)

            except Exception as e:
                log_message(f"用户 {user['username']} 打卡出现异常: {str(e)}")
                traceback.print_exc()
                # 出错后等待60秒再尝试下一个用户
                if i < len(current_users):
                    log_message(f"等待60秒后开始下一个用户的打卡...")
                    sleep(60)

        # 打卡完成后的统计
        success_count = len([u for u in current_users if u.get('last_clockin_date') == current_date])
        log_message(f"=== {current_time} 打卡任务完成 ===")
        log_message(f"总计 {len(current_users)} 个用户，成功 {success_count} 个")

    finally:
        TASK_RUNNING = False


def test_clockin(user_name):
    """测试单个用户的打卡功能"""
    config = load_config()
    user = next((u for u in config['users'] if u['username'] == user_name), None)
    if not user:
        print(f"未找到用户 {user_name}")
        return

    log_message(f"开始测试用户 {user_name} 的打卡功能")
    result = clockin_main(user)
    log_message(f"打卡返回结果: {result}")


if __name__ == '__main__':
    while True:
        print("\n欢迎使用学习通实习打卡签到脚本")
        print("0. 手动打卡")
        print("1. 上传打卡图片")
        print("2. 启动自动打卡")
        print("3. 用户管理")
        print("4. 测试用户打卡")
        print("5. 退出")
        useid = input("请输入功能序号：")

        if useid == "0":
            config = load_config()
            if not config['users']:
                print("没有可用的用户，请先添加用户")
                continue

            print("\n请选择用户：")
            for i, user in enumerate(config['users'], 1):
                enabled_status = "启用" if user.get('enabled', False) else "禁用"
                print(f"{i}. {user['username']} ({user.get('remark', '无备注')}) - {enabled_status}")

            user_idx = int(input("请输入用户序号：")) - 1
            if 0 <= user_idx < len(config['users']):
                user = config['users'][user_idx]
                result = clockin_main(user)
                print(f"\n打卡结果: {result}")
            else:
                print("无效的用户序号！")

        elif useid == "1":
            config = load_config()
            if not config['users']:
                print("没有可用的用户，请先添加用户")
                continue

            print("\n请选择要上传图片的用户：")
            for i, user in enumerate(config['users'], 1):
                print(f"{i}. {user['username']} ({user.get('remark', '无备注')})")

            user_idx = int(input("请输入用户序号：")) - 1
            if 0 <= user_idx < len(config['users']):
                user = config['users'][user_idx]
                uploaded_ids = upload_img(user)
                if uploaded_ids:
                    print(f"上传成功的图片ID列表: {uploaded_ids}")
                    print("请在用户管理中将这些ID添加到用户的pictureAry字段中")
            else:
                print("无效的用户序号！")

        elif useid == "2":
            config = load_config()
            schedule.clear()

            # 为每个启用的用户设置定时任务
            enabled_users = [user for user in config['users'] if user.get('enabled', False)]
            if not enabled_users:
                print("没有启用的用户！请先在用户管理中启用用户")
                continue

            # 按时间排序用户
            enabled_users.sort(key=lambda x: x['clock_in_time'])

            # 获取所有不同的打卡时间
            unique_times = sorted(set(user['clock_in_time'] for user in enabled_users))

            # 显示打卡计划
            log_message("=== 打卡计划 ===")
            for time in unique_times:
                users_at_time = [u for u in enabled_users if u['clock_in_time'] == time]
                log_message(f"时间 {time}:")
                for i, user in enumerate(users_at_time, 1):
                    log_message(f"  {i}. {user['username']} ({user.get('remark', '无备注')})")
                schedule.every().day.at(time).do(schedule_clock_in)

            log_message(f"日志文件位置：{os.path.abspath(log_file)}")
            print("按Ctrl+C可以终止自动打卡")

            try:
                while True:
                    schedule.run_pending()
                    sleep(30)
            except KeyboardInterrupt:
                log_message("自动打卡已停止")
                schedule.clear()
                continue

        elif useid == "3":
            manage_users()

        elif useid == "4":
            config = load_config()
            if not config['users']:
                print("没有可用的用户，请先添加用户")
                continue

            print("\n请选择要测试的用户：")
            for i, user in enumerate(config['users'], 1):
                print(f"{i}. {user['username']} ({user.get('remark', '无备注')})")

            user_idx = int(input("请输入用户序号：")) - 1
            if 0 <= user_idx < len(config['users']):
                user = config['users'][user_idx]
                test_clockin(user['username'])
            else:
                print("无效的用户序号！")

        elif useid == "5":
            print("退出程序")
            break

        else:
            print("输入错误，请重新输入")