#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point


class SectorVisualizer(Node):
    """可视化机器人周围的6个扇区"""

    def __init__(self):
        # super().__init__('sector_visualizer')
        super().__init__('obstacle_sectors', namespace="red_standard_robot1")

        
        # 参数
        self.declare_parameter('robot_namespace', 'red_standard_robot1')
        self.declare_parameter('base_frame', 'base_footprint')
        self.declare_parameter('radius', 2.0)  # 扇区半径（米）
        self.declare_parameter('update_rate', 10.0)  # 更新频率（Hz）
        
        # 获取参数值
        self.robot_namespace = self.get_parameter('robot_namespace').get_parameter_value().string_value
        self.base_frame = self.get_parameter('base_frame').get_parameter_value().string_value
        self.radius = self.get_parameter('radius').get_parameter_value().double_value
        self.update_rate = self.get_parameter('update_rate').get_parameter_value().double_value
        
        # 清理命名空间
        # if self.robot_namespace and self.robot_namespace not in ['', '/']:
        #     self.robot_namespace = self.robot_namespace.strip().rstrip('/')
        # else:
        #     self.robot_namespace = ''
        
        # 创建主题名（发布到机器人命名空间下）
        marker_topic = 'obstacle_sectors'
        if self.robot_namespace:
            marker_topic = f"{marker_topic}"
        
        # 创建发布器
        self.marker_pub = self.create_publisher(
            MarkerArray,
            marker_topic,
            10
        )
        
        self.get_logger().info(f"发布主题: {marker_topic}")

        # 组合完整的坐标系名称
        if self.robot_namespace:
            # 清理基础框架名称
            base_frame = self.base_frame.strip().lstrip('/')
            # self.frame_id = f"{self.robot_namespace}/{base_frame}"
            self.frame_id = self.base_frame
        else:
            self.frame_id = self.base_frame
        
        # 定义6个扇区的角度范围（度转弧度）
        # 扇区0：前方 [-30°, +30°]
        # 扇区1：右前 [-90°, -30°]
        # 扇区2：右后 [-150°, -90°]
        # 扇区3：后方 [±150°, ±180°] (即 [150°, 180°] 和 [-180°, -150°])
        # 扇区4：左后 [90°, 150°]
        # 扇区5：左前 [30°, 90°]
        self.sector_ranges = [
            (-math.pi/6, math.pi/6),      # 扇区0: 前方 [-30°, +30°]
            (-math.pi/2, -math.pi/6),     # 扇区1: 右前 [-90°, -30°]
            (-5*math.pi/6, -math.pi/2),   # 扇区2: 右后 [-150°, -90°]
            (5*math.pi/6, math.pi),       # 扇区3: 后方 [150°, 180°]
            (-math.pi, -5*math.pi/6),     # 扇区3: 后方 [-180°, -150°]
            (math.pi/2, 5*math.pi/6),     # 扇区4: 左后 [90°, 150°]
            (math.pi/6, math.pi/2),       # 扇区5: 左前 [30°, 90°]
        ]
        
        self.sector_names = [
            "前方(0)",
            "右前(1)",
            "右后(2)",
            "后方(3)",
            "后方(3)",
            "左后(4)",
            "左前(5)"
        ]
        
        # 扇区颜色 (RGBA)
        self.sector_colors = [
            (0.0, 1.0, 0.0, 0.3),   # 扇区0: 绿色（前方）
            (1.0, 0.5, 0.0, 0.3),   # 扇区1: 橙色（右前）
            (1.0, 0.0, 0.0, 0.3),   # 扇区2: 红色（右后）
            (0.5, 0.0, 0.5, 0.3),   # 扇区3: 紫色（后方）
            (0.5, 0.0, 0.5, 0.3),   # 扇区3: 紫色（后方）
            (0.0, 0.0, 1.0, 0.3),   # 扇区4: 蓝色（左后）
            (0.0, 1.0, 1.0, 0.3),   # 扇区5: 青色（左前）
        ]
        
        # 边界线颜色
        self.boundary_colors = [
            (0.0, 1.0, 0.0, 1.0),   # 扇区0: 绿色
            (1.0, 0.5, 0.0, 1.0),   # 扇区1: 橙色
            (1.0, 0.0, 0.0, 1.0),   # 扇区2: 红色
            (0.5, 0.0, 0.5, 1.0),   # 扇区3: 紫色
            (0.5, 0.0, 0.5, 1.0),   # 扇区3: 紫色
            (0.0, 0.0, 1.0, 1.0),   # 扇区4: 蓝色
            (0.0, 1.0, 1.0, 1.0),   # 扇区5: 青色
        ]
        
        # 创建定时器
        timer_period = 1.0 / self.update_rate
        self.timer = self.create_timer(timer_period, self.publish_markers)
        
        # 添加调试信息
        self.get_logger().info('=' * 50)
        self.get_logger().info('扇区可视化节点已启动')
        self.get_logger().info(f'机器人命名空间: {self.robot_namespace if self.robot_namespace else "无"}')
        self.get_logger().info(f'基础坐标系: {self.base_frame}')
        self.get_logger().info(f'完整坐标系: {self.frame_id}')
        self.get_logger().info(f'发布主题: {marker_topic}')
        self.get_logger().info(f'扇区半径: {self.radius}m')
        self.get_logger().info(f'更新频率: {self.update_rate}Hz')
        self.get_logger().info('=' * 50)

    def publish_markers(self):
        """发布可视化标记"""
        marker_array = MarkerArray()
        marker_id = 0
        
        # 绘制扇区填充区域和边界线
        for i, (start_angle, end_angle) in enumerate(self.sector_ranges):
            # 创建扇区填充区域（三角形）
            sector_marker = Marker()
            sector_marker.header.frame_id = self.frame_id
            # sector_marker.header.stamp = self.get_clock().now().to_msg()
            sector_marker.header.stamp.sec = 0
            sector_marker.header.stamp.nanosec = 0
            sector_marker.ns = "sectors"
            sector_marker.id = marker_id
            sector_marker.type = Marker.TRIANGLE_LIST
            sector_marker.action = Marker.ADD
            
            # 计算扇区顶点
            # 中心点
            center = Point()
            center.x = 0.0
            center.y = 0.0
            center.z = 0.05
            
            # 起始边界点
            start_point = Point()
            start_point.x = self.radius * math.cos(start_angle)
            start_point.y = self.radius * math.sin(start_angle)
            start_point.z = 0.05
            
            # 结束边界点
            end_point = Point()
            end_point.x = self.radius * math.cos(end_angle)
            end_point.y = self.radius * math.sin(end_angle)
            end_point.z = 0.05
            
            # 添加三角形顶点（两个三角形组成扇形）
            # 三角形1: 中心-起点-中点
            mid_angle = (start_angle + end_angle) / 2
            mid_point = Point()
            mid_point.x = self.radius * math.cos(mid_angle)
            mid_point.y = self.radius * math.sin(mid_angle)
            mid_point.z = 0.05
            
            sector_marker.points.append(center)
            sector_marker.points.append(start_point)
            sector_marker.points.append(mid_point)
            
            # 三角形2: 中心-中点-终点
            sector_marker.points.append(center)
            sector_marker.points.append(mid_point)
            sector_marker.points.append(end_point)
            
            # 设置颜色
            color = self.sector_colors[i]
            sector_marker.color.r = color[0]
            sector_marker.color.g = color[1]
            sector_marker.color.b = color[2]
            sector_marker.color.a = color[3]
            
            sector_marker.scale.x = 1.0
            sector_marker.scale.y = 1.0
            sector_marker.scale.z = 1.0
            
            marker_array.markers.append(sector_marker)
            marker_id += 1
            
            # 创建边界射线（从中心到边界）
            boundary_marker = Marker()
            boundary_marker.header.frame_id = self.frame_id
            # boundary_marker.header.stamp = self.get_clock().now().to_msg()
            boundary_marker.header.stamp.sec = 0
            boundary_marker.header.stamp.nanosec = 0
            boundary_marker.ns = "boundaries"
            boundary_marker.id = marker_id
            boundary_marker.type = Marker.LINE_LIST
            boundary_marker.action = Marker.ADD
            
            # 起始边界线
            boundary_marker.points.append(center)
            boundary_marker.points.append(start_point)
            
            # 结束边界线
            boundary_marker.points.append(center)
            boundary_marker.points.append(end_point)
            
            # 设置颜色
            bcolor = self.boundary_colors[i]
            boundary_marker.color.r = bcolor[0]
            boundary_marker.color.g = bcolor[1]
            boundary_marker.color.b = bcolor[2]
            boundary_marker.color.a = bcolor[3]
            
            boundary_marker.scale.x = 0.05  # 线宽
            
            marker_array.markers.append(boundary_marker)
            marker_id += 1
        
        # 添加扇区标签（每个扇区只添加一次）
        # 扇区映射：0->0, 1->1, 2->2, 3->3, 4->3(跳过), 5->4, 6->5
        sector_label_info = [
            (0, "前方(0)", 0.0),                    # 扇区0: 前方
            (1, "右前(1)", -math.pi/3),             # 扇区1: 右前 (-60°)
            (2, "右后(2)", -2*math.pi/3),           # 扇区2: 右后 (-120°)
            (3, "后方(3)", math.pi),                 # 扇区3: 后方 (180°)
            (4, "左后(4)", 2*math.pi/3),            # 扇区4: 左后 (120°)
            (5, "左前(5)", math.pi/3),              # 扇区5: 左前 (60°)
        ]
        
        for sector_num, label_text, label_angle in sector_label_info:
            label_marker = Marker()
            label_marker.header.frame_id = self.frame_id
            # label_marker.header.stamp = self.get_clock().now().to_msg()
            label_marker.header.stamp.sec = 0
            label_marker.header.stamp.nanosec = 0
            label_marker.ns = "labels"
            label_marker.id = marker_id
            label_marker.type = Marker.TEXT_VIEW_FACING
            label_marker.action = Marker.ADD
            
            # 标签位置（在扇区中心，稍微向外偏移）
            label_distance = self.radius * 0.7
            
            label_marker.pose.position.x = label_distance * math.cos(label_angle)
            label_marker.pose.position.y = label_distance * math.sin(label_angle)
            label_marker.pose.position.z = 0.2
            
            label_marker.text = label_text
            
            label_marker.scale.z = 0.3  # 文字大小
            
            # 文字颜色为白色
            label_marker.color.r = 1.0
            label_marker.color.g = 1.0
            label_marker.color.b = 1.0
            label_marker.color.a = 1.0
            
            marker_array.markers.append(label_marker)
            marker_id += 1
        
        # 添加调试标记：在小车中心添加红色原点
        self.add_debug_origin(marker_array, marker_id)
        marker_id += 1
        
        # 发布所有标记
        self.marker_pub.publish(marker_array)
        
        # 可选：定期输出调试信息（每10次输出一次）
        if hasattr(self, '_debug_counter'):
            self._debug_counter += 1
            if self._debug_counter % 20 == 0:
                self.get_logger().info(f"发布扇区可视化到主题: {self.marker_pub.topic}")
        else:
            self._debug_counter = 1

    def add_debug_origin(self, marker_array, marker_id):
        """在小车中心添加红色原点标记，便于调试"""
        origin_marker = Marker()
        origin_marker.header.frame_id = self.frame_id
        # origin_marker.header.stamp = self.get_clock().now().to_msg()
        origin_marker.header.stamp.sec = 0
        origin_marker.header.stamp.nanosec = 0
        origin_marker.ns = "debug"
        origin_marker.id = marker_id
        origin_marker.type = Marker.SPHERE
        origin_marker.action = Marker.ADD
        
        # 原点位置
        origin_marker.pose.position.x = 0.0
        origin_marker.pose.position.y = 0.0
        origin_marker.pose.position.z = 0.0
        
        origin_marker.scale.x = 0.1
        origin_marker.scale.y = 0.1
        origin_marker.scale.z = 0.1
        
        origin_marker.color.r = 1.0  # 红色
        origin_marker.color.g = 0.0
        origin_marker.color.b = 0.0
        origin_marker.color.a = 1.0
        
        marker_array.markers.append(origin_marker)


def main(args=None):
    rclpy.init(args=args)
    
    node = SectorVisualizer()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()