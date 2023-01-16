from setuptools import setup

setup(
        name='dicoder',
        version='0.0.1',
        description='Dev assistant with LLM and code analysis dialouge',
        author='Aryaz Eghbali',
        packages=['server', 'coder', 'benchmark'],
        include_package_data=True,
)
