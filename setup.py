from setuptools import setup, find_packages

setup(
    name="foodhelper",
    version="1.0.0",
    description="Matdagbok med bilder för selektiva ätare",
    author="FoodHelper",
    license="GPL-3.0",
    packages=find_packages(),
        package_data={
        "": ["locale/*/LC_MESSAGES/*.mo"],
    },
    entry_points={
        "console_scripts": [
            "foodhelper=foodhelper.main:main",
        ],
    },
    python_requires=">=3.8",
    install_requires=[
        "PyGObject>=3.42",
    ],
)
