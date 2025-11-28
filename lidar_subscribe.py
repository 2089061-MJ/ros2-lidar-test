import roslibpy
import numpy as np

ROS_IP = '192.168.112.128' 
ROS_PORT = 9090

print(f"ROS2 서버에 연결중입니다. {ROS_IP}:{ROS_PORT} ...")
client = roslibpy.Ros(host=ROS_IP, port=ROS_PORT)

client.run()
print("ROSBridge 서버에 연결되었습니다.")

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

try:
    listener.subscribe(lidar_callback)
    while client.is_connected:
        pass
except KeyboardInterrupt:
    pass
finally:
    listener.unsubscribe()
    client.terminate()
    print('연결 종료')
