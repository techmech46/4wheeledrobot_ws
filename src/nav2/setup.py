from setuptools import setup
from glob import glob
import os

package_name = 'nav2'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@example.com',
    description='ROS2 navigation package for 4-wheeled mobile robot',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'robot_controller = nav2.nodes.robot_controller:main',
            'navigation_node = nav2.nodes.navigation_node:main',
            'goal_publisher = nav2.nodes.goal_publisher:main',
        ],
    },
)
