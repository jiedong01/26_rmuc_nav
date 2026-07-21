from setuptools import setup
import os
from glob import glob

package_name = 'sector_visualization'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Yuan',
    maintainer_email='yuan@example.com',
    description='可视化机器人周围的6个扇区',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'sector_visualizer = sector_visualization.sector_visualizer:main',
        ],
    },
)
