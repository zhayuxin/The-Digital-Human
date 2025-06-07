import os
import time
import requests
from urllib.request import urlretrieve
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 配置
API_KEY = "636f885a5c0a4dc8a279a291d08bXXXX"
API_BASE = "https://www.runninghub.cn"

#音色克隆
CLONE_WORKFLOW_ID = "192321488477827XXXX"
#图生视频
VIDEO_WORKFLOW_ID = "192321793818091XXXX"
#对口型
LIPSYNC_WORKFLOW_ID = "192503523609332XXXX"

CLONE_AUDIO_NODE = "577"
CLONE_TEXT_NODE = "314"
VIDEO_IMAGE_NODE = "16"
LIPSYNC_AUDIO_NODE = "8"
LIPSYNC_VIDEO_NODE = "10"

HEADERS = {"Host": "www.runninghub.cn"}


def upload_file_to_api(file_path, file_type):
    files = {
        "file": (os.path.basename(file_path), open(file_path, 'rb'), f"{file_type}/*")
    }
    data = {
        "apiKey": API_KEY,
        "fileType": file_type
    }
    response = requests.post(f"{API_BASE}/task/openapi/upload", files=files, data=data, headers=HEADERS)
    json_data = response.json()
    if json_data["code"] != 0:
        raise Exception(json_data["msg"])
    return json_data["data"]["fileName"]


def create_task(workflow_id, node_list):
    payload = {
        "apiKey": API_KEY,
        "workflowId": workflow_id,
        "nodeInfoList": node_list
    }
    response = requests.post(f"{API_BASE}/task/openapi/create", json=payload, headers=HEADERS)
    json_data = response.json()
    if json_data["code"] != 0:
        raise Exception(json_data["msg"])
    return json_data["data"] if isinstance(json_data["data"], str) else json_data["data"]["taskId"]


def get_task_status(task_id):
    payload = {"apiKey": API_KEY, "taskId": task_id}
    response = requests.post(f"{API_BASE}/task/openapi/status", json=payload, headers=HEADERS)
    json_data = response.json()
    if json_data["code"] != 0:
        raise Exception(json_data["msg"])
    return json_data["data"] if isinstance(json_data["data"], str) else json_data["data"]["taskStatus"]


def get_result_url(task_id):
    payload = {"apiKey": API_KEY, "taskId": task_id}
    response = requests.post(f"{API_BASE}/task/openapi/outputs", json=payload, headers=HEADERS)
    json_data = response.json()
    if json_data["code"] != 0:
        raise Exception(json_data["msg"])
    return json_data["data"][0]["fileUrl"]


def poll_result(task_id, max_retries=150, interval=8):
    for i in range(max_retries):
        status = get_task_status(task_id)
        print(f"⏳ 第 {i + 1} 次轮询，状态: {status}")
        if status == "SUCCESS":
            return get_result_url(task_id)
        if status == "FAILED":
            raise Exception("任务失败")
        time.sleep(interval)
    raise Exception("任务超时")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate-video', methods=['POST'])
def generate_video():
    try:
        audio_file = request.files['audio']
        image_file = request.files['image']
        text = request.form['text']

        audio_path = os.path.join(UPLOAD_FOLDER, secure_filename(audio_file.filename))
        image_path = os.path.join(UPLOAD_FOLDER, secure_filename(image_file.filename))

        audio_file.save(audio_path)
        image_file.save(image_path)

        # 克隆音色
        audio_name = upload_file_to_api(audio_path, "audio")
        clone_nodes = [
            {"nodeId": CLONE_AUDIO_NODE, "fieldName": "audio", "fieldValue": audio_name},
            {"nodeId": CLONE_TEXT_NODE, "fieldName": "text", "fieldValue": text}
        ]
        clone_task_id = create_task(CLONE_WORKFLOW_ID, clone_nodes)
        cloned_audio_url = poll_result(clone_task_id)

        # 生成视频
        image_name = upload_file_to_api(image_path, "image")
        video_nodes = [
            {"nodeId": VIDEO_IMAGE_NODE, "fieldName": "image", "fieldValue": image_name}
        ]
        video_task_id = create_task(VIDEO_WORKFLOW_ID, video_nodes)
        video_url = poll_result(video_task_id)

        # 保存克隆音频 & 视频到本地
        timestamp = int(time.time())
        cloned_audio_filename = f"cloned_{timestamp}.mp3"
        video_filename = f"generated_{timestamp}.mp4"
        cloned_audio_path = os.path.join(UPLOAD_FOLDER, cloned_audio_filename)
        video_path = os.path.join(UPLOAD_FOLDER, video_filename)

        urlretrieve(cloned_audio_url, cloned_audio_path)
        urlretrieve(video_url, video_path)

        return jsonify({
            "success": True,
            "videoUrl": video_url,
            "clonedAudio": cloned_audio_filename,
            "generatedVideo": video_filename
        })

    except Exception as e:
        print("❌ 生成视频失败：", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/generate-lip-sync', methods=['POST', 'GET'])
def generate_lip_sync():
    try:
        if request.method == 'POST':
            audio_filename = request.form.get('audio')
            video_filename = request.form.get('video')
        else:  # GET 请求用于自动触发
            audio_filename = request.args.get('audio')
            video_filename = request.args.get('video')

        if not audio_filename or not video_filename:
            raise Exception("缺少音频或视频文件名参数")

        audio_path = os.path.join(UPLOAD_FOLDER, audio_filename)
        video_path = os.path.join(UPLOAD_FOLDER, video_filename)

        if not os.path.exists(audio_path):
            raise Exception(f"音频文件不存在: {audio_path}")
        if not os.path.exists(video_path):
            raise Exception(f"视频文件不存在: {video_path}")

        print("📁 上传对口型音频：", audio_path)
        print("📁 上传对口型视频：", video_path)

        audio_name = upload_file_to_api(audio_path, "audio")
        video_name = upload_file_to_api(video_path, "video")

        nodes = [
            {"nodeId": LIPSYNC_AUDIO_NODE, "fieldName": "audio", "fieldValue": audio_name},
            {"nodeId": LIPSYNC_VIDEO_NODE, "fieldName": "video", "fieldValue": video_name}
        ]

        task_id = create_task(LIPSYNC_WORKFLOW_ID, nodes)
        result_url = poll_result(task_id)

        lipsync_filename = f"lipsync_{int(time.time())}.mp4"
        lipsync_path = os.path.join(UPLOAD_FOLDER, lipsync_filename)
        urlretrieve(result_url, lipsync_path)

        return jsonify({"success": True, "videoUrl": result_url})

    except Exception as e:
        print("❌ 对口型失败：", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
