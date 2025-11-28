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

# LaserScan 토픽 구독(ROS2에서 publish한 토픽명)
listener = roslibpy.Topic(client, '/lidar_scan', 'sensor_msgs/LaserScan')

def lidar_callback(message):
    ranges = np.array(message["ranges"])
    
    front = np.r_[ranges[350:360], ranges[0:10]]
    left  = ranges[80:100]
    right = ranges[260:280]
    
    front_dist = np.mean(front)
    left_dist = np.mean(left)
    right_dist = np.mean(right)
    
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

        
    print("\n 수신")
    print(f"  Front: {front_dist:.2f} m")
    print(f"  Left : {left_dist:.2f} m")
    print(f"  Right: {right_dist:.2f} m")
    print("\n")
    print(action)
    save_db(ranges, action)
    
def save_db(ranges, action):
    conn = db.connect()
    cursor = conn.cursor()
    
    sql = "INSERT INTO lidar_data (ranges, time, action) VALUES (%s, %s, %s)"
    json_ranges = json.dumps(list(ranges))
    data = (json_ranges, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action)
    
    cursor.execute(sql, data)
    conn.commit()
    print("DB 저장 완료")
    
def load_data(return_type="dataframe"):
    conn = db.connect()
    cursor = conn.cursor()
    
    sql = "SELECT ranges, action FROM lidar_data"
    cursor.execute(sql)
    
    rows = cursor.fetchall()
    data = []
    
    for row in rows:
        ranges_json = row[0]  # 튜플 0번 인덱스: ranges
        action = row[1]       # 튜플 1번 인덱스: action

        ranges = json.loads(ranges_json)

        if len(ranges) != 360:
            print(f"Warning: ranges length != 360 (len={len(ranges)}) → 스킵")
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
    pass
finally:
    listener.unsubscribe()
    client.terminate()
    conn.cursor().close()
    conn.close()
    print('종료')
    np_data = load_data(return_type="numpy")
    print(np_data.shape)

    

