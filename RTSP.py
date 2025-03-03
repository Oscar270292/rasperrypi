#!/usr/bin/python3
# 導入 PiCamera2 及其相關模組
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, Quality
from picamera2.outputs import FfmpegOutput
import os, time

# 初始化 Picamera2
picam2 = Picamera2()
frame_rate = 30

# 設定視頻配置
video_config = picam2.create_video_configuration(
    main={"size": (1640, 1232), "format": "RGB888"},  # 主視頻流配置
    lores={"size": (640, 480), "format": "YUV420"},  # 低分辨率視頻流配置
    controls={'FrameRate': frame_rate}  # 控制項設置為 30fps
)
picam2.align_configuration(video_config)  # 對齊配置
picam2.configure(video_config)  # 應用配置

# 設定 Ffmpeg 輸出流，用於 RTSP 傳輸
HQoutput = FfmpegOutput("-f rtsp -rtsp_transport udp rtsp://myuser:mypass@172.20.10.2:8554/hqstream", audio=False)
LQoutput = FfmpegOutput("-f rtsp -rtsp_transport udp rtsp://myuser:mypass@172.20.10.2:8554/lqstream", audio=False)

# 設定高品質和低品質的 H264 編碼器
encoder_HQ = H264Encoder(repeat=True, iperiod=30, framerate=frame_rate, enable_sps_framerate=True)
encoder_LQ = H264Encoder(repeat=True, iperiod=30, framerate=frame_rate, enable_sps_framerate=True)

try:
    print("開始")  # 開始錄製
    picam2.start_recording(encoder_HQ, HQoutput, quality=Quality.LOW)  # 開始高品質錄製
    picam2.start_recording(encoder_LQ, LQoutput, quality=Quality.LOW, name="lores")  # 開始低品質錄製
    print("已開始")

    # 進入無限循環以保持腳本運行
    while True:
        time.sleep(5)  # 每隔 5 秒
        # 捕獲一幀圖像並臨時保存
        still = picam2.capture_request()
        still.save("main", "/dev/shm/camera-tmp.jpg")
        still.release()
        # 用新圖替換舊圖
        os.rename('/dev/shm/camera-tmp.jpg', '/dev/shm/camera.jpg')
except:
    print("退出 PiCamera2 流程")  # 如果發生錯誤，輸出退出信息
    # 停止錄制
    picam2.stop_recording()
