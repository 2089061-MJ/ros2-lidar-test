import rclpy
from rclpy.node import Node
import math
import random
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist

ANGLE_MIN_DEG = 0
ANGLE_MAX_DEG = 359
ANGLE_INCREMENT_DEG = 1
NUM_POINTS = 360
RANGE_MIN = 0.12
RANGE_MAX = 3.5

def create_empty_scan():
    ranges = [float(RANGE_MAX) for _ in range(NUM_POINTS)]
    intensities = [100.0 for _ in range(NUM_POINTS)]
    
    scan = LaserScan()
    scan.angle_min = float(math.radians(ANGLE_MIN_DEG))
    scan.angle_max = float(math.radians(ANGLE_MAX_DEG))
    scan.angle_increment = float(math.radians(ANGLE_INCREMENT_DEG))
    scan.range_min = float(RANGE_MIN)
    scan.range_max = float(RANGE_MAX)

    scan.ranges = ranges
    scan.intensities = intensities
    return scan


def make_the_wall(ranges, center_deg, width_deg):
    half_width = width_deg // 2
    for offset in range(-half_width, half_width + 1):
        idx = (center_deg + offset) % NUM_POINTS
        ranges[idx] = 0.4


def pattern_front_wall(scan):
    make_the_wall(scan.ranges, center_deg=0, width_deg=40)


def pattern_left_wall(scan):
    make_the_wall(scan.ranges, center_deg=90, width_deg=30)


def pattern_right_wall(scan):
    make_the_wall(scan.ranges, center_deg=270, width_deg=30)


def generate_single_scan(pattern_name):
    scan = create_empty_scan()
    if pattern_name == "front_wall":
        pattern_front_wall(scan)
    elif pattern_name == "left_wall":
        pattern_left_wall(scan)
    elif pattern_name == "right_wall":
        pattern_right_wall(scan)
    return scan


AVAILABLE_PATTERNS = ["front_wall", "left_wall", "right_wall"]

class LidarPublisher(Node):
    def __init__(self):
        super().__init__('lidar_mock_publisher')

        # LaserScan 퍼블리셔
        self.publisher = self.create_publisher(LaserScan, 'lidar_scan', 10)
        self.cmd_pub = self.create_publisher(Twist, 'turtle1/cmd_vel', 10)

        # 2초마다 발행하는 타이머
        self.timer = self.create_timer(2.0, self.timer_callback)

        self.get_logger().info("Lidar Publisher Started")

    def timer_callback(self):
        pattern = random.choice(AVAILABLE_PATTERNS)
        scan_msg = generate_single_scan(pattern)

        # LaserScan 메시지 타임스탬프 추가
        scan_msg.header.stamp = self.get_clock().now().to_msg()
        scan_msg.header.frame_id = "lidar"

        self.publisher.publish(scan_msg)
        self.get_logger().info(f"Published Lidar Pattern: {pattern}")

        cmd = self.turtle_action(pattern)
        self.cmd_pub.publish(cmd)
        self.get_logger().info(f"linear={cmd.linear.x:.2f}, angular={cmd.angular.z:.2f}")

    def turtle_action(self, pattern):
        cmd = Twist()

        if pattern == "front_wall":
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0

        elif pattern == "left_wall":
            cmd.linear.x = 0.2
            cmd.angular.z = -0.7

        elif pattern == "right_wall":
            cmd.linear.x = 0.2
            cmd.angular.z = 0.7

        return cmd

def main(args=None):
    rclpy.init(args=args)
    node = LidarPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
