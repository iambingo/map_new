import json
import time
import os
from email.contentmanager import maintype

import requests

polling_interval = 2
max_retries = 30
fail_message = "Lighthouse任务执行失败"


def execute_polling_request(url, headers, json_data, interval, max_retries):
    """
    执行带轮询逻辑的请求
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, json=json_data, headers=headers)
            response.raise_for_status()  # 检查HTTP状态码，如果不是200-299则抛出异常
            result_query = response.json()

            run_status = result_query.get('data', {}).get('runStatus')

            if run_status == 'SUCCESS':
                print("任务执行成功")
                return result_query
            elif run_status == 'FAILED':
                print(f"任务执行失败: {result_query.get('message', 'Unknown error')}")
                raise RuntimeError(fail_message)
            elif run_status == 'PENDING':
                if attempt < max_retries:
                    print(f"任务执行中 (第 {attempt}/{max_retries} 次检查)... 等待 {interval} 秒后重试")
                    time.sleep(interval)
                else:
                    print("任务执行超时")
                    raise TimeoutError("任务执行超时，未达到成功状态")
            else:
                # 如果状态既不是 PENDING 也不是 SUCCESS/FAILED，视具体情况处理
                # 这里假设其他状态可能需要继续等待或视为异常，根据实际业务调整
                print(f"未知状态: {run_status}")
                if attempt < max_retries:
                    time.sleep(interval)
                else:
                    raise RuntimeError(f"未知任务状态: {run_status}")

        except requests.exceptions.RequestException as e:
            print(f"网络请求错误: {e}")
            raise
        except RuntimeError as e:
            # 重新抛出业务逻辑错误，由调用方处理
            raise
        except Exception as e:
            print(f"发生未预期错误: {e}")
            raise

    # 如果循环结束仍未返回（理论上不应该到达这里，因为上面有raise）
    raise TimeoutError("轮询次数用尽，任务未完成")

def download_and_process_files(file_list, save_dir):
    """
    下载文件并根据类型处理

    :param file_list: 文件列表字典
    :param sove_dir: 保存目录
    """
    if not file_list:
        print("没有找到文件列表")
        return

    # 确保保存目录存在
    os.makedirs(save_dir, exist_ok=True)
    print(f"开始下载文件到: {os.path.abspath(save_dir)}")

    for file_info in file_list:
        original_filename = file_info.get('fileName')
        file_url = file_info.get('fileUrl')

        if not original_filename or not file_url:
            print(f"警告: 文件信息不完整, 跳过: {file_info}")
            continue

        # 1. 确定最终保存的文件名
        # 如果是 summary_ 开头的 csv, 强制转为 html
        if original_filename.startswith('summary_') and original_filename.endswith('.csv'):
            final_filename = original_filename.replace('.csv', '.html')
            print(f"发现需要转换的文件: {original_filename} -> {final_filename}")
        else:
            # 其他文件 (如 weights.csv) 保持原样
            final_filename = original_filename

        # 构建完整保存路径
        save_path = os.path.join(save_dir, final_filename)

        # 安全检查: 防止路径遍历 (例如 filename=../../etc/passwd)
        if not os.path.abspath(save_path).startswith(os.path.abspath(save_dir)):
            print(f"警告: 非法文件名 {original_filename}, 跳过以防止路径遍历")
            continue

        # 2. 下载文件
        print(f"正在下载: {original_filename} ....")
        try:
            # 设置超时时间, 防止卡死
            response = requests.get(file_url, timeout=30)
            response.raise_for_status()  # 如果状态码不是 200, 抛出异常

            with open(save_path, 'wb') as f:
                f.write(response.content)

            print(f"成功保存: {save_path}")

        except requests.exceptions.RequestException as e:
            print(f"下载失败 {original_filename}: {e}")
        except Exception as e:
            print(f"保存文件时出错 {original_filename}: {e}")

        # 可选: 增加少量延迟, 避免对服务器造成过大压力
        time.sleep(0.5)


def get_data_from_lighthouse(a):
    b = json.dumps(a, ensure_ascii=False)

    # 调用接口参数
    config = {
        "appCode": "f7a94ef56bda481d897a7450d8361bf3",
        "operationType": "run"
    }
    config['args'] = b

    headers = {"currentLoginUsername": "SHIHONGYI344"}
    url = "http://pawm-pfp-83022-gateway.fat001.qa.pab.com.cn/data/agm/noRegister/callModel/601327f77528421b99c38bb23206ea7e"
    response = requests.post(url, json=config, headers=headers)
    result = response.json()
    print(result)

    config_query = {
        "appCode": "f7a94ef56bda481d897a7450d8361bf3",
        "operationType": "query",
        "runId": result["data"]
    }

    # 使用函数执行轮询
    try:
        # 请确保 config_query 已定义
        # config_query = {...}
        final_result = execute_polling_request(url, headers, config_query, polling_interval, max_retries)
        print("最终结果：", final_result)
    except Exception as e:
        print("程序终止：", e)

    SAVE_DIR = "./download_files"

    data = final_result.get('data', {})
    file_list = data.get('fileList', [])

    # 执行下载和处理
    download_and_process_files(file_list, SAVE_DIR)

    print("所有任务完成。")

if __name__ == '__main__':

    a = {
        "meeting_date": "20260507",
        "vote_config": {
            "固收-存单": {"3": 8, "4": 1},
            "固收-信用": {"3": 6, "4": 3},
            "固收-利率10Y": {"3": 8, "4": 1},
            "固收-利率30Y": {"3": 7, "4": 2, "5": 1},
            "含权-转债": {"2": 1, "3": 5, "4": 3},
            "含权-二级债基": {"3": 8, "4": 2},
            "含权-红利": {"3": 6, "4": 4},
            "含权-偏股混": {"2": 1, "3": 5, "4": 3},
            "含权-恒生科技": {"2": 2, "3": 2, "4": 6},
            "另类-黄金": {"3": 2, "4": 8}
        }
    } #接口输入样例

    get_data_from_lighthouse(a)