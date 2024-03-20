import cv2
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, render_template, Response, jsonify, url_for
import os
from flask import send_file
import datetime
app = Flask(__name__)
video_dir = r'C:\Users\DELL\OneDrive\Desktop\app\static\video'
cap = cv2.VideoCapture(0)
fgbg = cv2.createBackgroundSubtractorMOG2()
min_area = 2000
fourcc = cv2.VideoWriter_fourcc(*'H264')
out = None
motion_detected = False
motion_start_time = 0
video_count = 0

sender_email = "camera.cpv301@gmail.com"
sender_password = "CameraCpv@301"

receiver_email = "vuonghoangtran1003@gmail.com"

smtp_server = smtplib.SMTP("smtp.gmail.com", 587)
smtp_server.starttls()
smtp_server.login(sender_email, "vqfc ndju oapv ijuh")

smtp_server.login(sender_email, sender_password)
def send_email():
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Motion Detected"

    body = "Motion detected ."
    msg.attach(MIMEText(body, 'plain'))

    smtp_server.sendmail(sender_email, receiver_email, msg.as_string())

desired_duration = 10

def generate_frames():
    global motion_detected, motion_start_time, out, video_count
    while True:
        ret, frame = cap.read()

        if not ret:
            break

        fgmask = fgbg.apply(frame)
        fgmask = cv2.erode(fgmask, None, iterations=2)
        fgmask = cv2.dilate(fgmask, None, iterations=2)

        contours, _ = cv2.findContours(fgmask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) < min_area:
                continue

            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            if not motion_detected:
                motion_detected = True
                motion_start_time = time.time()

        if motion_detected:
            if out is None:
                video_count += 1
                current_time = datetime.datetime.now().strftime("%H-%M-%S_%d-%m-%Y")
                video_name = f'C:\\Users\\DELL\\OneDrive\\Desktop\\app\\static\\video\\motion_capture_{video_count}_at_{current_time}.mp4'
                out = cv2.VideoWriter(video_name, fourcc, 25.0, (frame.shape[1], frame.shape[0]))
                send_email()
            out.write(frame)

            elapsed_time = time.time() - motion_start_time
            if elapsed_time >= desired_duration:
                motion_detected = False
                out.release()
                out = None

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/get_video_list')
def get_video_list():
    video_list = []
    video_files = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
    sorted_video_files = sorted(video_files, key=lambda x: os.path.getctime(os.path.join(video_dir, x)))
    for video in os.listdir(video_dir):
        video_url = url_for('static', filename='video/' + video)
        video_list.append({'name': video, 'url': video_url})
    return jsonify(video_list)

@app.route('/play_video/<video_name>')
def play_video(video_name):
    video_path = os.path.join(video_dir, video_name)
    return send_file(video_path, mimetype='video/mp4')

@app.route('/')
def index():
    video_list = os.listdir(video_dir)
    return render_template('index.html', videos=video_list)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)

