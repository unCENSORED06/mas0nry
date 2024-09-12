from cx_Freeze import setup, Executable

# Define the executable
executables = [Executable('mas0nry.py', base='Win32GUI')]

# Define setup parameters
setup(
    name='mas0nry',
    version='0.7.0',
    description='USE AT YOUR OWN RISK! I AM NOT LIABLE',
    executables=executables
)
