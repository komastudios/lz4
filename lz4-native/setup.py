from setuptools import setup, find_packages

setup(
    name="lz4-native",
    version="0.1.0",
    packages=find_packages(),
    # Include native libs if present (for bundled wheels)
    # The build system will populate this directory before building the wheel
    package_data={"lz4_native": ["lib/*.so", "lib/*.dylib", "lib/*.dll"]},
    include_package_data=True,
    install_requires=["cffi>=1.0.0"],
    description="Python wrapper for native LZ4 library (Block and Frame APIs)",
    python_requires=">=3.6",
)
