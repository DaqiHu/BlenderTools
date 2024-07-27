import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv


REPO_ROOT = Path(__file__).parent.parent

ENV_FILE = REPO_ROOT / '.env'
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

PYTHON_3_11_VIRTUAL_ENV = REPO_ROOT / '.venv'
PYTHON_3_10_VIRTUAL_ENV = REPO_ROOT / '.py3.10-venv'
PYTHON_3_9_VIRTUAL_ENV = REPO_ROOT / '.py3.9-venv'

BLENDER_STARTUP_SCRIPT = Path(__file__).parent / 'resources' / 'blender' / 'startup.py'
UNREAL_STARTUP_SCRIPT = Path(__file__).parent / 'resources' / 'unreal' / 'init_unreal.py'

SCRIPTS_FOLDER = REPO_ROOT / 'scripts'


UNREAL_PROJECT = os.environ.get('UNREAL_PROJECT_PATH') or REPO_ROOT / 'tests' / 'test_files' / 'unreal_projects' / 'test01' / 'test01.uproject'


def shell(command: str, **kwargs):
    process = subprocess.Popen(
        command,
        shell=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        **kwargs
    )

    output = []
    for line in iter(process.stdout.readline, ""): # type: ignore
        output += [line.rstrip()]
        sys.stdout.write(line)

    process.wait()

    if process.returncode != 0:
        raise OSError("\n".join(output))
    
def validate_venv(venv_path: Path) -> bool:
    if not venv_path.exists():
        print(f'Virtual environment not found here: "{venv_path}"')
        python_version = venv_path.name.split('-')[0].strip('.')
        if python_version == 'venv':
            python_version = '3.11'

        print('This can be fixed by running the following command at the root of the repo to  create a virtual environment with the correct python version:')
        print(f"C:/some/path/{python_version}/python.exe -m venv {venv_path}")
        return False

    return True


def validate_exe(exe_path: Path) -> bool:
    if not exe_path.exists():
        app_name = exe_path.name.split('.')[0].lower()
        if app_name != 'blender':   
            app_name = 'unreal'

        print(f'The {app_name} executable was not found here: "{exe_path}"')
        print('Are you sure you have the correct path to the executable? Is it installed?')
        print(f"Try setting the environment variable '{app_name.upper()}_EXE_PATH' to the correct path if you know where {app_name} is.")
        return False
    return True


def launch_blender(version: str, debug: str):
    virtual_env = PYTHON_3_11_VIRTUAL_ENV
    if version in ['3.6', '4.0']:
        virtual_env = PYTHON_3_10_VIRTUAL_ENV

    if not validate_venv(virtual_env):
        return

    site_packages = virtual_env / 'Lib' / 'site-packages'

    exe_path = os.environ.get('BLENDER_EXE_PATH')
    if not exe_path:
        if sys.platform == 'win32':
            exe_path = rf"C:\Program Files\Blender Foundation\Blender {version}\blender.exe"
        else:
            exe_path = None

    if not validate_exe(Path(exe_path)):
        return

    if exe_path:
        command = f'"{exe_path}" --python-use-system-env --python "{BLENDER_STARTUP_SCRIPT}"'
        shell(
            command, 
            env={
                **os.environ.copy(), 
                'PYTHONUNBUFFERED': '1',
                'BLENDER_APP_VERSION': version,
                'BLENDER_DEBUGGING_ON': debug,
                'PYTHONPATH': ';'.join([
                    str(site_packages),
                    str(SCRIPTS_FOLDER)
                ])
            }
        )


def launch_unreal(version: str, debug: str):
    virtual_env = PYTHON_3_11_VIRTUAL_ENV
    if version in ['5.3']:
        virtual_env = PYTHON_3_9_VIRTUAL_ENV

    if not validate_venv(virtual_env):
        return

    exe_path = os.environ.get('UNREAL_EXE_PATH')
    if not exe_path:
        if sys.platform == 'win32':
            exe_path = rf'C:\Program Files\Epic Games\UE_{app_version}\Engine\Binaries\Win64\UnrealEditor.exe'
        else:
            exe_path = None

    site_packages = virtual_env / 'Lib' / 'site-packages'

    if not validate_exe(Path(exe_path)):
        return

    if exe_path:
        command = f'"{exe_path}" "{UNREAL_PROJECT}" -stdout -nopause -forcelogflush -verbose'
        shell(
            command, 
            env={
                **os.environ.copy(),
                'PYTHONUNBUFFERED': '1',
                'UNREAL_APP_VERSION': version,
                'UNREAL_DEBUGGING_ON': debug,
                'UE_PYTHONPATH': ';'.join([
                    str(site_packages.absolute()), 
                    str(UNREAL_STARTUP_SCRIPT.parent.absolute()),
                ])
            }
        )

if __name__ == "__main__":
    app_name = sys.argv[1]
    app_version = sys.argv[2]
    debug_on = sys.argv[3]

    if app_name == 'blender':
        launch_blender(
            version=app_version,
            debug=debug_on
        )

    if app_name == 'unreal':
        launch_unreal(
            version=app_version,
            debug=debug_on
        )