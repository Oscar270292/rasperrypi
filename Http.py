from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder, Quality
from picamera2.outputs import FileOutput
from libcamera import controls, Transform
import io

# 現在你可以使用 io.BufferedIOBase
from io import BufferedIOBase
from threading import Condition
from flask import Flask, render_template_string, Response

# 創建一個 Picamera2 對象
cam = Picamera2()
# 定義視頻配置
config = cam.create_video_configuration(
    # 主攝像頭配置，全高清分辨率和特定像素格式
    {'size': (1920, 1080), 'format': 'XBGR8888'},
    # 可選的轉換配置，這裡設置為垂直翻轉圖像
    transform=Transform(vflip=1),
    # 可選的控制圖像質量設置
    controls={
        'NoiseReductionMode': controls.draft.NoiseReductionModeEnum.HighQuality,
        'Sharpness': 1.5
    }
)
# 應用配置到相機
cam.configure(config)
# 開始錄影，指定編碼器和質量設置
# 輸出設置為通過 FileOutput 存儲到 StreamingOutput

class StreamingOutput(BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()
    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()
output = StreamingOutput()
cam.start_recording(JpegEncoder(), FileOutput(output), Quality.VERY_HIGH)

# 使用 Flask 創建一個網絡應用
from flask import Flask
app = Flask(__name__)

# HTML 模板，用於顯示視頻流
template = '''
<!DOCTYPE html>
<html lang="en">
    <body>
        <img src="{{ url_for('video_stream') }}" width="100%">
    </body>
</html>
'''
@app.route("/", methods=['GET'])
def get_stream_html():
    return render_template_string(template)

# 生成視頻幀
def gen_frames():
    while True:
        with output.condition:
            output.condition.wait()
            frame = output.frame
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
# 設置路由來提供視頻流
@app.route('/api/stream')
def video_stream():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# 開始運行 Flask 應用
app.run(host='0.0.0.0')
# 停止相機錄影
cam.stop()
