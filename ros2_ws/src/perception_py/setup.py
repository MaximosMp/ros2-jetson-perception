from glob import glob

from setuptools import find_packages, setup

package_name = 'perception_py'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Maximos Bilalis',
    maintainer_email='15655703+MaximosMp@users.noreply.github.com',
    description='YOLOX object detection node for ROS2 images.',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'detector = perception_py.detector:main',
            'visualizer = perception_py.visualizer:main',
        ],
    },
)
