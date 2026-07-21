// elevation_bridge_node.cpp
// Subscribe to registered pointcloud, build elevation map, compute slope

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <grid_map_ros/grid_map_ros.hpp>
#include <grid_map_msgs/msg/grid_map.hpp>
#include <pcl_conversions/pcl_conversions.h>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <cmath>

class ElevationBridgeNode : public rclcpp::Node
{
public:
  ElevationBridgeNode() : Node("elevation_bridge_node")
  {
    // Declare parameters
    this->declare_parameter<double>("map_length_x", 10.0);
    this->declare_parameter<double>("map_length_y", 10.0);
    this->declare_parameter<double>("resolution", 0.1);
    this->declare_parameter<double>("max_slope_deg", 25.0);
    this->declare_parameter<double>("obstacle_slope_deg", 35.0);
    this->declare_parameter<double>("vehicle_height", 0.5);
    this->declare_parameter<std::string>("map_frame", "odom");

    // Get parameters
    map_length_x_ = this->get_parameter("map_length_x").as_double();
    map_length_y_ = this->get_parameter("map_length_y").as_double();
    resolution_ = this->get_parameter("resolution").as_double();
    max_slope_deg_ = this->get_parameter("max_slope_deg").as_double();
    obstacle_slope_deg_ = this->get_parameter("obstacle_slope_deg").as_double();
    vehicle_height_ = this->get_parameter("vehicle_height").as_double();
    map_frame_ = this->get_parameter("map_frame").as_string();

    // Initialize grid map
    map_.setFrameId(map_frame_);
    map_.setGeometry(grid_map::Length(map_length_x_, map_length_y_), resolution_);
    map_.add("elevation", 0.0);
    map_.add("slope", 0.0);
    map_.add("count", 0.0);

    RCLCPP_INFO(this->get_logger(), "Grid map initialized: %.1f x %.1f m, resolution: %.2f m",
                map_length_x_, map_length_y_, resolution_);

    // Subscribers
    cloud_sub_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
        "registered_scan", 10,
        std::bind(&ElevationBridgeNode::cloudCallback, this, std::placeholders::_1));

    odom_sub_ = this->create_subscription<nav_msgs::msg::Odometry>(
        "lidar_odometry", 10,
        std::bind(&ElevationBridgeNode::odomCallback, this, std::placeholders::_1));

    // Publishers
    elevation_map_pub_ = this->create_publisher<grid_map_msgs::msg::GridMap>(
        "elevation_map", 10);

    terrain_map_pub_ = this->create_publisher<sensor_msgs::msg::PointCloud2>(
        "terrain_map_slope", 10);

    // Timer for publishing
    timer_ = this->create_wall_timer(
        std::chrono::milliseconds(200),
        std::bind(&ElevationBridgeNode::publishMaps, this));

    RCLCPP_INFO(this->get_logger(), "Elevation Bridge Node started!");
    RCLCPP_INFO(this->get_logger(), "  max_slope: %.1f deg, obstacle_slope: %.1f deg",
                max_slope_deg_, obstacle_slope_deg_);
  }

private:
  void odomCallback(const nav_msgs::msg::Odometry::SharedPtr msg)
  {
    robot_x_ = msg->pose.pose.position.x;
    robot_y_ = msg->pose.pose.position.y;
    robot_z_ = msg->pose.pose.position.z;
    has_odom_ = true;
  }

  void cloudCallback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    if (!has_odom_) {
      RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 5000,
                           "Waiting for odometry...");
      return;
    }

    // Convert to PCL
    pcl::PointCloud<pcl::PointXYZI>::Ptr cloud(new pcl::PointCloud<pcl::PointXYZI>());
    pcl::fromROSMsg(*msg, *cloud);

    // Move map to follow robot
    // grid_map::Position robot_pos(robot_x_, robot_y_);
    // map_.move(robot_pos);

    // Update elevation map with new points
    for (const auto& pt : cloud->points) {
      grid_map::Position pos(pt.x, pt.y);

      if (!map_.isInside(pos)) continue;

      grid_map::Index idx;
      if (!map_.getIndex(pos, idx)) continue;

      float& elev = map_.at("elevation", idx);
      float& cnt = map_.at("count", idx);

      // Simple incremental mean update
      cnt += 1.0f;
      float delta = pt.z - elev;
      elev += delta / cnt;
    }

    // Compute slope
    computeSlope();

    last_cloud_time_ = msg->header.stamp;
  }

  void computeSlope()
  {
    auto& elevation = map_["elevation"];
    auto& slope = map_["slope"];

    for (grid_map::GridMapIterator it(map_); !it.isPastEnd(); ++it) {
      const grid_map::Index idx(*it);

      if (!map_.isValid(idx, "elevation")) {
        slope(idx(0), idx(1)) = NAN;
        continue;
      }

      float center_z = elevation(idx(0), idx(1));
      float max_slope = 0.0f;

      // Check 8 neighbors
      int dx[] = {-1, 0, 1, -1, 1, -1, 0, 1};
      int dy[] = {-1, -1, -1, 0, 0, 1, 1, 1};
      float dist[] = {1.414f, 1.0f, 1.414f, 1.0f, 1.0f, 1.414f, 1.0f, 1.414f};

      for (int n = 0; n < 8; n++) {
        grid_map::Index neighbor(idx(0) + dx[n], idx(1) + dy[n]);

        if (!map_.isValid(neighbor, "elevation")) continue;

        float neighbor_z = elevation(neighbor(0), neighbor(1));
        float elev_diff = std::abs(center_z - neighbor_z);
        float horiz_dist = dist[n] * resolution_;

        float slope_rad = std::atan(elev_diff / horiz_dist);
        float slope_deg = slope_rad * 180.0f / M_PI;

        max_slope = std::max(max_slope, slope_deg);
      }

      slope(idx(0), idx(1)) = max_slope;
    }
  }

  void publishMaps()
  {
    if (!has_odom_) return;

    auto now = this->now();

    // Publish GridMap (for visualization)
    auto grid_map_msg = grid_map::GridMapRosConverter::toMessage(map_);
    grid_map_msg->header.stamp = now;
    grid_map_msg->header.frame_id = map_frame_;
    elevation_map_pub_->publish(std::move(grid_map_msg));

    // Publish as PointCloud2 (for IntensityVoxelLayer)
    publishTerrainCloud(now);
  }

  void publishTerrainCloud(const rclcpp::Time& stamp)
  {
    pcl::PointCloud<pcl::PointXYZI>::Ptr cloud(new pcl::PointCloud<pcl::PointXYZI>());

    for (grid_map::GridMapIterator it(map_); !it.isPastEnd(); ++it) {
      const grid_map::Index idx(*it);

      if (!map_.isValid(idx, "elevation")) continue;
      if (!map_.isValid(idx, "slope")) continue;

      grid_map::Position pos;
      map_.getPosition(idx, pos);

      pcl::PointXYZI pt;
      pt.x = pos.x();
      pt.y = pos.y();
      pt.z = map_.at("elevation", idx);

      // Convert slope to intensity
      float slope_deg = map_.at("slope", idx);
      pt.intensity = slopeToIntensity(slope_deg);

      cloud->push_back(pt);
    }

    sensor_msgs::msg::PointCloud2 msg;
    pcl::toROSMsg(*cloud, msg);
    msg.header.stamp = stamp;
    msg.header.frame_id = map_frame_;

    terrain_map_pub_->publish(msg);
  }

  float slopeToIntensity(float slope_deg)
  {
    float intensity = 0.0f;

    if (slope_deg >= obstacle_slope_deg_) {
      intensity = vehicle_height_;
    } else if (slope_deg >= max_slope_deg_) {
      float ratio = (slope_deg - max_slope_deg_) / (obstacle_slope_deg_ - max_slope_deg_);
      intensity = vehicle_height_ * (0.5f + 0.5f * ratio);
    } else {
      intensity = vehicle_height_ * 0.5f * (slope_deg / max_slope_deg_);
    }

    return std::max(0.0f, std::min(intensity, (float)vehicle_height_));
  }

  // Parameters
  double map_length_x_;
  double map_length_y_;
  double resolution_;
  double max_slope_deg_;
  double obstacle_slope_deg_;
  double vehicle_height_;
  std::string map_frame_;

  // State
  double robot_x_ = 0.0;
  double robot_y_ = 0.0;
  double robot_z_ = 0.0;
  bool has_odom_ = false;
  rclcpp::Time last_cloud_time_;

  // Grid map
  grid_map::GridMap map_;

  // ROS
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr cloud_sub_;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;
  rclcpp::Publisher<grid_map_msgs::msg::GridMap>::SharedPtr elevation_map_pub_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr terrain_map_pub_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<ElevationBridgeNode>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
