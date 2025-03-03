from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
import cv2
import numpy as np
from flask import Flask, render_template_string, Response

# 初始化 Flask 和 Camera
app = Flask(__name__)
camera = Picamera2()

# 配置攝影機
config = camera.create_video_configuration(main={"format": "RGB888"})
camera.configure(config)

# 啟動預覽和相機錄制
camera.start_preview()  # 預覽啟動
camera.start()  # 相機錄制開始

# 載入 OpenCV 的人臉識別模型
def load_face_cascade():
    cascPath = '/home/b10505025/camera-python-opencv/camera-opencv/03-face_datection/haarcascade_frontalface_default.xml'  # 路徑
    return cv2.CascadeClassifier(cascPath)

face_cascade = load_face_cascade()

def gen_frames():
    while True:
        # 從 Picamera2 獲取幀
        buffer = camera.capture_array()
        frame = cv2.cvtColor(np.array(buffer), cv2.COLOR_RGB2BGR)

        # 人臉識別
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w*2, y+h*2), (0, 255, 0), 2)

        # 將幀編碼成 JPEG 以供 Flask 服務器傳輸
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# 啟動 Flask 服務器
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


