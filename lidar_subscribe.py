import roslibpy
import time

def lidar_callback(message):
    ranges = message['ranges']

    # LaserScan 배열 범위
    if len(ranges) < 360:
        print("ranges 수가 부족함")
        return

    # 각 방향 최소값 측정
    front = min(ranges[0:40] + ranges[320:359])  # 정면
    left = min(ranges[80:120])                   # 좌측
    right = min(ranges[240:280])                 # 우측

    print("\n 수신")
    print(f"  Front: {front:.2f} m")
    print(f"  Left : {left:.2f} m")
    print(f"  Right: {right:.2f} m")
    print("\n")

    if front < 0.8:
        print("정지! (앞에 벽이 있습니다!)")
        
    elif left < 0.8:
        print("오른쪽으로 이동하세요. (왼쪽에 벽이 있습니다!)")
    
    elif right < 0.8:
        print("왼쪽으로 이동하세요. (오른쪽에 벽이 있습니다.)")
    
    else:
        print("직진")

def main():
    ROS_IP = '192.168.112.128' 
    ROS_PORT = 9090

    print(f"ROS2 서버에 연결중입니다. {ROS_IP}:{ROS_PORT} ...")
    client = roslibpy.Ros(host=ROS_IP, port=ROS_PORT)

    client.run()
    print("ROSBridge 서버에 연결되었습니다.")

    # LaserScan 토픽 구독(ROS2에서 publish한 토픽명)
    listener = roslibpy.Topic(client, '/lidar_scan', 'sensor_msgs/LaserScan')

    listener.subscribe(lidar_callback)
    print("/lidar_scan 토픽을 구독합니다.")

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("연결 종료")
        listener.unsubscribe()
        client.terminate()

if __name__ == '__main__':
    main()
