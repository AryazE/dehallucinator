from setuptools import setup

setup(
    name="dehallucinator",
    version="0.0.1",
    description="Iterative grounding for LLM-based code completion",
    author="Aryaz Eghbali",
    packages=["server", "coder", "benchmark"],
    include_package_data=True,
)
