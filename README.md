# 26_rmuc_nav

在 [pb2025_sentry_nav](https://github.com/SMBU-PolarBear-Robotics-Team/pb2025_sentry_nav) 基础上新增了三个功能包：高程地图构建（`elevation_bridge`）、扇区可视化（`sector_visualization`）、扩展地形分析（`terrain_analysis_ext`）。

原始导航栈的代码直接平铺在本仓库中，可以作为一个独立的 ROS2 工作空间使用。

---

## 新增功能包

### elevation_bridge

订阅配准后点云（`cloud_registered`）和里程计（`lidar_odometry`），用 `grid_map` 库建一个固定尺寸的高程地图，对每个格元用8邻域梯度计算坡度，再把坡度映射为 intensity 发出去。

**发布：**
- `elevation_map` (`grid_map_msgs/msg/GridMap`) — 含 elevation / slope / count 三层，接 grid_map RViz 插件看
- `terrain_map_slope` (`sensor_msgs/msg/PointCloud2`) — intensity 编码坡度，接 NAV2 的 `IntensityVoxelLayer`

**订阅：**
- `cloud_registered` (重映射自 `registered_scan`)
- `lidar_odometry`

**参数：**

| 参数 | 默认值 | 说明 |
|---|---|---|
| `map_length_x` / `map_length_y` | 30.0 m | 地图尺寸 |
| `resolution` | 0.2 m | 格元分辨率 |
| `max_slope_deg` | 25.0 | 视为通行困难的坡度（度） |
| `obstacle_slope_deg` | 35.0 | 视为障碍物的坡度（度） |
| `vehicle_height` | 0.5 m | 车体高度，用于 intensity 缩放 |
| `map_frame` | `odom` | 地图坐标系 |

**启动：**

```bash
ros2 launch elevation_bridge elevation_bridge_launch.py \
  namespace:=red_standard_robot1 \
  use_sim_time:=true
```

RViz 配置文件在 `elevation_bridge/config/elevation_bridge.rviz`，可以直接加载查看高程图和坡度点云。

---

### sector_visualization

在 RViz 里把机器人底盘坐标系周围划分为 6 个方向扇区，用半透明色块 + 边界线 + 标签渲染，方便调试障碍物方位感知。

**扇区划分：**

| 编号 | 方向 | 角度范围 | 颜色 |
|---|---|---|---|
| 0 | 前方 | [-30°, +30°] | 绿 |
| 1 | 右前 | [-90°, -30°] | 橙 |
| 2 | 右后 | [-150°, -90°] | 红 |
| 3 | 后方 | [±150°, ±180°] | 紫 |
| 4 | 左后 | [90°, 150°] | 蓝 |
| 5 | 左前 | [30°, 90°] | 青 |

**发布：**
- `/red_standard_robot1/obstacle_sectors` (`visualization_msgs/msg/MarkerArray`)

**参数：**

| 参数 | 默认值 | 说明 |
|---|---|---|
| `robot_namespace` | `red_standard_robot1` | 命名空间 |
| `base_frame` | `base_footprint` | 扇区锚定坐标系 |
| `radius` | 2.0 m | 扇区半径 |
| `update_rate` | 10.0 Hz | 发布频率 |

**启动：**

```bash
ros2 launch sector_visualization sector_visualization.launch.py
```

或者直接：

```bash
ros2 run sector_visualization sector_visualizer --ros-args \
  -p radius:=3.0 \
  -p base_frame:=chassis
```

RViz 中添加 `MarkerArray`，话题设为 `/red_standard_robot1/obstacle_sectors`，Fixed Frame 设为 `base_footprint`。

---

### terrain_analysis_ext

对车体 **4 m 以外**区域做地形分析，intensity 编码障碍物离地高度，与 `terrain_analysis`（负责 4 m 以内）配合给 NAV2 提供完整的地形代价信息。代码来自 [autonomous_exploration_development_environment](https://github.com/HongbiaoZ/autonomous_exploration_development_environment)，已适配 ROS2 Humble。

**订阅：**
- `registered_scan` — 配准后点云
- `lidar_odometry` — 里程计
- `terrain_map` — 来自 `terrain_analysis` 的本地地形（4 m 内）

**发布：**
- `terrain_map_ext` (`sensor_msgs/msg/PointCloud2`) — 合并本地地形后的扩展地形图

**启动：**

```bash
ros2 launch terrain_analysis_ext terrain_analysis_ext.launch
```

---

## 工作空间搭建

```bash
mkdir -p ~/ros_ws/src
cd ~/ros_ws/src

git clone --recursive https://github.com/jiedong01/26_rmuc_nav.git
```

安装依赖：

```bash
cd ~/ros_ws

# elevation_bridge 依赖 grid_map
sudo apt install -y ros-humble-grid-map ros-humble-grid-map-ros ros-humble-grid-map-msgs

# small_gicp_relocalization 依赖
sudo apt install -y libeigen3-dev libomp-dev
git clone https://github.com/koide3/small_gicp.git /tmp/small_gicp
cd /tmp/small_gicp && mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc) && sudo make install
cd ~/ros_ws

rosdep install -r --from-paths src --ignore-src --rosdistro humble -y
```

编译：

```bash
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
```

---

## 运行

### 仿真

**导航模式：**

```bash
ros2 launch pb2025_nav_bringup rm_navigation_simulation_launch.py \
  world:=rmuc_2025 \
  slam:=False
```

**建图模式：**

```bash
ros2 launch pb2025_nav_bringup rm_navigation_simulation_launch.py \
  slam:=True
```

保存栅格地图：

```bash
ros2 run nav2_map_server map_saver_cli -f <MAP_NAME> --ros-args -r __ns:=/red_standard_robot1
```

**同时启动高程地图（新增）：**

```bash
# 另开终端
ros2 launch elevation_bridge elevation_bridge_launch.py use_sim_time:=true
```

**同时启动扇区可视化（新增）：**

```bash
ros2 launch sector_visualization sector_visualization.launch.py
```

### 实车

**建图模式：**

```bash
ros2 launch pb2025_nav_bringup rm_navigation_reality_launch.py \
  slam:=True \
  use_robot_state_pub:=True
```

**导航模式：**

```bash
ros2 launch pb2025_nav_bringup rm_navigation_reality_launch.py \
  world:=<YOUR_WORLD_NAME> \
  slam:=False \
  use_robot_state_pub:=True
```

**同时启动高程地图（新增）：**

```bash
ros2 launch elevation_bridge elevation_bridge_launch.py \
  use_sim_time:=false \
  namespace:=red_standard_robot1
```

---

## 文件结构

```
.
├── elevation_bridge                    # 新增：高程地图 + 坡度点云，供 NAV2 IntensityVoxelLayer 使用
├── sector_visualization                # 新增：RViz 6扇区可视化
├── terrain_analysis_ext                # 新增（适配自 AEDE）：车体4m外扩展地形分析
├── fake_vel_transform                  # 虚拟速度参考坐标系
├── ign_sim_pointcloud_tool             # 仿真器点云处理工具
├── livox_ros_driver2                   # Livox 驱动
├── loam_interface                      # point_lio 里程计接口
├── pb2025_nav_bringup                  # 启动文件
├── pb2025_sentry_nav                   # meta-package 描述文件
├── pb_nav2_plugins                     # NAV2 插件
├── pb_omni_pid_pursuit_controller      # 路径跟踪控制器
├── pb_teleop_twist_joy                 # 手柄控制
├── point_lio                           # 里程计
├── pointcloud_to_laserscan             # 点云转 laserScan（SLAM 模式）
├── sensor_scan_generation              # 点云坐标变换
├── small_gicp_relocalization           # 重定位
└── terrain_analysis                    # 车体4m内地形分析
```

---

## 关于原始导航栈

原始代码来自北极熊战队 [pb2025_sentry_nav](https://github.com/SMBU-PolarBear-Robotics-Team/pb2025_sentry_nav)，基于 NAV2 框架，使用 Livox mid360 倾斜侧放，`point_lio` 里程计，`small_gicp` 重定位，`pb_omni_pid_pursuit_controller` 路径跟踪。

坐标变换链：`lidar_odom` -> `loam_interface` -> `odom` -> `sensor_scan_generation` -> `chassis`

查看 tf tree：

```bash
ros2 run rqt_tf_tree rqt_tf_tree --ros-args \
  -r /tf:=tf -r /tf_static:=tf_static -r __ns:=/red_standard_robot1
```

**启动参数（仿真/实车通用）：**

| 参数 | 描述 | 默认值 |
|---|---|---|
| `namespace` | 顶级命名空间 | `red_standard_robot1` |
| `use_sim_time` | 使用仿真时钟 | 仿真: True / 实车: False |
| `slam` | 建图模式（True 时禁用 small_gicp，发布静态 map->odom） | False |
| `world` | 地图名，仿真可选 rmul_2024 / rmuc_2024 / rmul_2025 / rmuc_2025 | `rmuc_2025` |
| `map` | 地图文件完整路径 | 根据 world 自动填充 |
| `prior_pcd_file` | 先验点云完整路径 | 根据 world 自动填充 |
| `params_file` | ROS2 参数文件路径 | `nav2_params.yaml` |
| `autostart` | 自动启动 nav2 | True |
| `use_composition` | 使用 Composable Node | True |
| `use_rviz` | 启动 RViz | True |
| `use_robot_state_pub` | 用 robot_state_publisher 发布 TF（实车测试导航模块时开） | False |

多机器人（实验性）：

```bash
ros2 launch pb2025_nav_bringup rm_multi_navigation_simulation_launch.py \
  world:=rmul_2024 \
  robots:=" \
  red_standard_robot1={x: 0.0, y: 0.0, yaw: 0.0}; \
  blue_standard_robot1={x: 5.6, y: 1.4, yaw: 3.14}; \
  "
```

先验点云（用于 point_lio 和 small_gicp）体积较大，不存储在 git 中，前往 FlowUs 下载。
