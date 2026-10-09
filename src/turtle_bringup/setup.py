from glob import glob

from setuptools import find_packages, setup

package_name = 'turtle_bringup'

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
    package_data={'': ['py.typed']},
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Stepan Senkov',
    maintainer_email='nskyu2019@gmail.com',
    description='Bringup для turtlesim: launch-файл запуска симулятора. Практика ПР02 курса «Введение в ROS 2» (НГУ).',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)
