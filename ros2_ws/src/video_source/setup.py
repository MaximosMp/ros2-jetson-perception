from setuptools import find_packages, setup

package_name = 'video_source'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Maximos Bilalis',
    maintainer_email='15655703+MaximosMp@users.noreply.github.com',
    description='Plays a video file as a camera: publishes its frames as sensor_msgs/Image.',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'video_publisher = video_source.video_publisher:main',
        ],
    },
)
