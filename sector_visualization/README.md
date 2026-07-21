# 扇区可视化包 (Sector Visualization)

这个ROS2包用于在RViz中可视化机器人周围的6个扇区。

## 扇区划分

- **扇区0**: 前方 [-30°, +30°] - 绿色
- **扇区1**: 右前 [-90°, -30°] - 橙色
- **扇区2**: 右后 [-150°, -90°] - 红色
- **扇区3**: 后方 [±150°, ±180°] - 紫色
- **扇区4**: 左后 [90°, 150°] - 蓝色
- **扇区5**: 左前 [30°, 90°] - 青色

## 使用方法

### 1. 编译包

```bash
cd ~/ros2_display/catkin_ws
colcon build --packages-select sector_visualization --symlink-install
source install/setup.bash
```

### 2. Source工作空间

```bash
source install/setup.bash
# 或使用zsh
source install/setup.zsh
```

### 3. 启动可视化节点

使用launch文件启动：

```bash
ros2 launch sector_visualization sector_visualization.launch.py
```

或者直接运行节点：

```bash
ros2 run sector_visualization sector_visualizer
```

### 3. 在RViz中查看

1. 启动RViz：
```bash
rviz2
```

2. 添加MarkerArray显示：
   - 点击"Add"按钮
   - 选择"MarkerArray"
   - 设置Topic为 `/sector_visualization`

3. 确保Fixed Frame设置为机器人坐标系（默认为`base_link`）

## 参数配置

可以通过launch文件或命令行参数修改：

- `frame_id`: 坐标系名称（默认: `base_link`）
- `radius`: 扇区半径，单位米（默认: `2.0`）
- `update_rate`: 更新频率，单位Hz（默认: `10.0`）

示例：

```bash
ros2 run sector_visualization sector_visualizer --ros-args -p frame_id:=chassis -p radius:=3.0
```

## 可视化内容

节点会发布以下可视化元素：

1. **扇区填充区域**: 使用半透明颜色填充每个扇区
2. **边界射线**: 从机器人中心到扇区边界的射线
3. **扇区标签**: 显示扇区编号和名称

## 话题

- `/sector_visualization` (visualization_msgs/msg/MarkerArray): 可视化标记数组
