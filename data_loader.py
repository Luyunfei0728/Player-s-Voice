import pandas as pd
import re
import streamlit as st

def parse_chat_log(file_content):
    """
    解析特定的 [Time] User(ID): Message 格式日志
    输入: 原始文本字符串
    输出: Pandas DataFrame
    """
    data = []
    # 针对上传文件的特定格式进行切分
    blocks = file_content.split('【具体对话】')
    
    # 容错处理：如果格式不对，尝试直接按行解析
    content_to_parse = blocks[1:] if len(blocks) > 1 else [file_content]
    
    for block in content_to_parse:
        lines = block.split('\n')
        for line in lines:
            # 正则匹配标准日志行
            match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (.*?)\((.*?)\): (.*)', line)
            if match:
                time_str, user_name, user_id, message = match.groups()
                data.append({
                    "Time": time_str,
                    "User": user_name,
                    "UserID": user_id,
                    "Message": message.strip()
                })
    
    return pd.DataFrame(data)

def load_demo_data():
    """生成演示用的默认数据"""
    # 这里我们构造更能体现“夸赞”和“吐槽”差异的数据
    demo_data = [
        {"Time": "2026-09-10 14:52:32", "User": "DemoUser1", "UserID": "001", "Message": "许愿面包开局，面包真的太强了"},
        {"Time": "2026-09-10 14:53:08", "User": "DemoUser2", "UserID": "002", "Message": "面包配合陷阱流简直无敌，爱了爱了"},
        {"Time": "2026-09-10 14:54:32", "User": "DemoUser3", "UserID": "003", "Message": "西部地图设计得有问题，太难受了"},
        {"Time": "2026-09-12 12:36:30", "User": "RiskUser", "UserID": "999", "Message": "通缉令卡得像是PPT，严重Bug建议官方看看"},
        {"Time": "2026-09-12 12:40:00", "User": "Cheater", "UserID": "888", "Message": "开了25倍加速器，这游戏太慢了"},
        {"Time": "2026-09-12 12:41:00", "User": "GamerX", "UserID": "777", "Message": "精神病系统有点意思，但是数值不平衡"}
    ]
    return pd.DataFrame(demo_data)