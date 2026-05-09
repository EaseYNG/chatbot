"""
网络请求示例 - 使用 requests 库
演示 GET、POST、异常处理、会话管理等常见操作
"""

import requests
import json
import time


def get_example():
    """GET 请求示例"""
    print("=" * 50)
    print("GET 请求示例")
    print("=" * 50)

    # 基本 GET 请求
    url = "https://httpbin.org/get"
    params = {"name": "Alice", "age": 30}

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()  # 检查 HTTP 错误

        data = response.json()
        print(f"状态码: {response.status_code}")
        print(f"请求 URL: {response.url}")
        print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")

    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")


def post_example():
    """POST 请求示例"""
    print("\n" + "=" * 50)
    print("POST 请求示例")
    print("=" * 50)

    url = "https://httpbin.org/post"
    payload = {"username": "test_user", "password": "secret123"}
    headers = {"Content-Type": "application/json"}

    try:
        # 发送 JSON 数据
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()

        data = response.json()
        print(f"状态码: {response.status_code}")
        print(f"发送的数据: {json.dumps(data.get('json', {}), indent=2, ensure_ascii=False)}")
        print(f"请求头: {json.dumps(data.get('headers', {}), indent=2)}")

    except requests.exceptions.RequestException as e:
        print(f"POST 请求失败: {e}")


def download_file_example():
    """下载文件示例"""
    print("\n" + "=" * 50)
    print("下载文件示例")
    print("=" * 50)

    url = "https://httpbin.org/image/png"
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()

        # 获取文件大小
        file_size = int(response.headers.get("content-length", 0))
        print(f"文件大小: {file_size / 1024:.2f} KB")
        print(f"Content-Type: {response.headers.get('content-type')}")

        # 流式下载，适合大文件
        with open("downloaded_image.png", "wb") as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    progress = (downloaded / file_size * 100) if file_size else 0
                    print(f"\r下载进度: {progress:.1f}%", end="")

        print("\n文件下载完成: downloaded_image.png")

    except requests.exceptions.RequestException as e:
        print(f"下载失败: {e}")


def session_example():
    """会话管理示例 - 保持 cookies 和连接池"""
    print("\n" + "=" * 50)
    print("会话管理示例")
    print("=" * 50)

    session = requests.Session()

    # 设置会话级别的默认配置
    session.headers.update({"User-Agent": "MyApp/1.0"})
    session.timeout = 5

    try:
        # 第一次请求 - 设置 cookie
        url1 = "https://httpbin.org/cookies/set"
        response1 = session.get(url1, params={"cookie_name": "session_id", "cookie_value": "abc123"})
        print(f"设置 Cookie 响应: {response1.status_code}")

        # 第二次请求 - 自动携带 cookie
        url2 = "https://httpbin.org/cookies"
        response2 = session.get(url2)
        data = response2.json()
        print(f"获取到的 Cookies: {json.dumps(data.get('cookies', {}), indent=2)}")

    except requests.exceptions.RequestException as e:
        print(f"会话请求失败: {e}")
    finally:
        session.close()


def error_handling_example():
    """错误处理示例"""
    print("\n" + "=" * 50)
    print("错误处理示例")
    print("=" * 50)

    test_cases = [
        ("https://httpbin.org/status/404", "404 Not Found"),
        ("https://httpbin.org/status/500", "500 Server Error"),
        ("https://httpbin.org/delay/10", "超时测试"),
        ("https://invalid-domain-12345.com", "DNS 解析失败"),
    ]

    for url, description in test_cases:
        print(f"\n测试: {description}")
        try:
            response = requests.get(url, timeout=3)
            response.raise_for_status()
            print(f"  成功: {response.status_code}")

        except requests.exceptions.Timeout:
            print(f"  错误: 请求超时")
        except requests.exceptions.ConnectionError:
            print(f"  错误: 连接失败 (DNS/网络问题)")
        except requests.exceptions.HTTPError as e:
            print(f"  错误: HTTP {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  错误: {type(e).__name__}: {e}")


def main():
    """主函数"""
    print("Python 网络请求示例\n")

    # 1. GET 请求
    get_example()

    # 2. POST 请求
    post_example()

    # 3. 下载文件
    download_file_example()

    # 4. 会话管理
    session_example()

    # 5. 错误处理
    error_handling_example()

    print("\n" + "=" * 50)
    print("所有示例执行完毕")
    print("=" * 50)


if __name__ == "__main__":
    main()
