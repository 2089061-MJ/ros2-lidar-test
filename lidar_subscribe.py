import roslibpy
import numpy as np
import pandas as pd
from db_helper import DB, DB_CONFIG
from datetime import datetime
import json

ROS_IP = '192.168.112.128'
ROS_PORT = 9090

print(f"ROS2 서버에 연결중입니다. {ROS_IP}:{ROS_PORT} ...")
client = roslibpy.Ros(host=ROS_IP, port=ROS_PORT)
client.run()
print("ROSBridge 서버에 연결되었습니다.")

# MySQL 서버
db = DB(**DB_CONFIG)
conn = db.connect()

cmd_vel_pub = roslibpy.Topic(client, '/turtle1/cmd_vel', 'geometry_msgs/msg/Twist')
listener = roslibpy.Topic(client, '/lidar_scan', 'sensor_msgs/LaserScan')


# 1) LiDAR 콜백
def lidar_callback(message):
    ranges = np.array(message["ranges"])

    # 앞/좌/우 거리 계산
    front = np.r_[ranges[350:360], ranges[0:10]]
    left  = ranges[80:100]
    right = ranges[260:280]

    front_dist = np.mean(front)
    left_dist = np.mean(left)
    right_dist = np.mean(right)

    # 거리 기준
    safe_dist = 0.5

    if front_dist < safe_dist:
        if left_dist > right_dist:
            action = "turn_left"
            cmd_vel_pub.publish({
                'linear':  {'x': 0.0, 'y': 0.0, 'z': 0.0},
                'angular': {'x': 0.0, 'y': 0.0, 'z': 1.0}
            })
        else:
            action = "turn_right"
            cmd_vel_pub.publish({
                'linear':  {'x': 0.0, 'y': 0.0, 'z': 0.0},
                'angular': {'x': 0.0, 'y': 0.0, 'z': -1.0}
            })
    else:
        action = "go_forward"
        cmd_vel_pub.publish({
            'linear':  {'x': 0.5, 'y': 0.0, 'z': 0.0},
            'angular': {'x': 0.0, 'y': 0.0, 'z': 0.0}
        })

    print("======================")
    print(f"Front: {front_dist:.2f}, Left: {left_dist:.2f}, Right: {right_dist:.2f}")
    print(f"Action: {action}")

    save_db(ranges, action)



# 2) DB 저장
def save_db(ranges, action):
    try:
        conn = db.connect()
        cursor = conn.cursor()
        sql = "INSERT INTO lidar_data (ranges, time, action) VALUES (%s, %s, %s)"
        json_ranges = json.dumps(list(ranges))
        data = (json_ranges, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action)
        cursor.execute(sql, data)
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"[DB ERROR] {e}")
    else:
        print("DB 저장 완료")


def load_data(return_type="dataframe"):
    conn = db.connect()
    cursor = conn.cursor()
    sql = "SELECT ranges, action FROM lidar_data"
    cursor.execute(sql)
    rows = cursor.fetchall()
    data = []

    for row in rows:
        ranges_json, action = row
        ranges = json.loads(ranges_json)
        if len(ranges) != 360:
            print(f"[WARNING] ranges length {len(ranges)} != 360 → 스킵")
            continue
        data.append(ranges + [action])

    columns = [f"range_{i}" for i in range(360)] + ["action"]
    df = pd.DataFrame(data, columns=columns)

    if return_type == "numpy":
        return df.to_numpy()
    return df

try:
    listener.subscribe(lidar_callback)
    while client.is_connected:
        pass
except KeyboardInterrupt:
    print("사용자 종료")
finally:
    listener.unsubscribe()
    client.terminate()
    conn.cursor().close()
    conn.close()
    print("종료")

    # CSV 저장
    np_data = load_data(return_type="numpy")
    df_data = pd.DataFrame(np_data, columns=[f"range_{i}" for i in range(360)] + ["action"])
    csv_filename = f"lidar_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df_data.to_csv(csv_filename, index=False)
    print(f"CSV 저장 완료: {csv_filename}")
