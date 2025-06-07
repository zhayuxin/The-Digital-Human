# 🧠 The Digital Human

一个基于 Flask 的 Web 应用，结合 [RunningHub](https://www.runninghub.cn) 平台的 API，实现了以下 AI 能力：

- 🗣️ 音色克隆（通过输入音频和文本合成个性语音）
- 🖼️ 图生视频（通过上传图片生成虚拟数字人视频）
- 👄 对口型（将语音与视频进行嘴型同步）

---

## 📁 项目结构


The-Digital-Human/
├── app.py                      # Flask 主程序
├── templates/
│   └── index.html              # 前端页面（上传界面）
├── static/uploads/            # 用户上传和生成的文件保存目录
└── README.md

---

## 📦 安装依赖

确保你已安装 Python 3.8 以上，然后运行以下命令安装依赖：
pip install flask requests
启动项目
python app.py

然后在浏览器打开：
http://127.0.0.1:5000
API 参数说明
本项目使用 RunningHub 提供的三个流程：

| 功能     | workflowId           | 说明             |
|----------|----------------------|------------------|
| 音色克隆 | 192321488477827XXXX | 输入音频和文本，输出语音 |
| 图生视频 | 192321793818091XXXX | 输入图像，生成视频 |
| 对口型   | 192503523609332XXXX | 输入音频和视频，生成口型同步视频 |

