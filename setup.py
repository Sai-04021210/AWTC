from setuptools import setup, find_packages

setup(
    name="awlc",
    version="0.1.0",
    description="Automated Water Level Control System",
    author="AWLC Team",
    author_email="example@example.com",
    packages=find_packages(),
    install_requires=[
        "paho-mqtt>=1.6.1",
    ],
    entry_points={
        'console_scripts': [
            'water-level-simulator=src.water_level_server.water_level_simulator:main',
            'pump-controller=src.middleware.pump_controller:main',
        ],
    },
    python_requires='>=3.6',
)
