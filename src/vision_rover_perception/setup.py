from glob import glob
from setuptools import find_packages, setup

package_name = 'vision_rover_perception'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/models', glob('models/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Vision Rover Developer',
    maintainer_email='developer@example.com',
    description='OpenCV and YOLO perception pipeline for Vision Rover.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'yolo_detector = vision_rover_perception.yolo_detector:main',
        ],
    },
)
