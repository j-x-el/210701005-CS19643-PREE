SOURCE CODE:

SET UP.py
-- coding: utf-8 --
import re
import sys

from setuptools import find_packages, setup

with open("aimmo/_init_.py", "r") as fd:
    version = re.search(
        r'^_version_\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE
    ).group(1)

try:
    from semantic_release import setup_hook

    setup_hook(sys.argv)
except ImportError:
    pass

setup(
    name="aimmo",
    packages=find_packages(exclude=[".tests", ".tests.*"]),
    package_dir={"aimmo": "aimmo"},
    include_package_data=True,
    install_requires=[
        "cfl-common",
        "django==3.2.25",
        "django-csp==3.7",
        "django-js-reverse==0.9.1",
        "djangorestframework==3.13.1",
        "eventlet==0.31.0",
        "hypothesis==5.41.3",
        "kubernetes==26.1.0",
        "requests==2.31.0",
    ],
    tests_require=["docker >= 3.5, < 3.6", "PyYAML == 5.4"],
    version=version,
    zip_safe=False,

from _future_ import print_function
from enum import Enum
import re
import sys
import platform
import subprocess
import traceback
import inspect
from subprocess import PIPE, CalledProcessError

# python2 support
try:
    input = raw_input
except NameError:
    pass


MINIKUBE_VERSION = "latest"
KUBECTL_VERSION = "latest"


class OSType(Enum):
    MAC = 1
    LINUX = 2
    WINDOWS = 3


class ArchType(Enum):
    AMD64 = 1
    ARM64 = 2


def main():
    try:
        os_type = get_os_type()
        arch_type = get_arch_type()

        setup = setup_factory(os_type, arch_type)

        try:
            print("Starting setup for OS: %s\n" % os_type.name)
            setup(os_type, arch_type)
            print("\nFinished setup.")
        except CalledProcessError as e:
            print("Something has gone wrong.")
            print("Command '%s' returned exit code '%s'" % (e.cmd, e.returncode))
            traceback.print_exc()
        except OSError as e:
            print("Tried to execute a command that didn't exist.")
            traceback.print_exc()
        except ValueError as e:
            print("Tried to execute a command with invalid arguments.")
            traceback.print_exc()
    except KeyError as e:
        print("Setup encountered an error: %s" % e.args[0])
    except:
        print("An unexpected error has occured:\n")
        raise


def get_os_type():
    """
    Return the OS type if one can be determined
    Returns:
        OSType: OS type
    """
    system = platform.system()

    system_os_type_map = {
        "Darwin": OSType.MAC,
        "Linux": OSType.LINUX,
        "Windows": OSType.WINDOWS,
    }

    try:
        return system_os_type_map[system]
    except KeyError:
        raise KeyError("'%s' system is not supported" % system)


def get_arch_type():
    """
    Return the architecture type
    Returns:
        ArchType: architecture type
    """
    arch = platform.machine()

    arch_type_map = {
        "amd64": ArchType.AMD64,
        "x86_64": ArchType.AMD64,
        "arm64": ArchType.ARM64,
    }

    try:
        return arch_type_map[arch]
    except KeyError:
        raise KeyError("'%s' architecture is not supported" % arch)


def setup_factory(os_type, arch_type):
    """
    Return the setup function which matches supplied host type
    Args:
        os_type (OSType): the type of host to setup
        arch_type (ArchType): host architecture type
    Returns:
        Callable: setup function
    """
    if os_type == OSType.MAC:
        return mac_setup

    elif os_type == OSType.LINUX:
        return linux_setup

    elif os_type == OSType.WINDOWS:
        return windows_setup

    raise RuntimeError("could not find setup function for supplied host type")


def mac_setup(os_type, arch_type):
    """
    Runs the commands needed in order to set up Kurono for MAC
    Args:
        os_type (OSType): host OS type
        arch_type (ArchType): host architecture type
    """
    tasks = [
        ensure_homebrew_installed,
        install_sqlite3,
        install_nodejs,
        install_yarn,
        set_up_frontend_dependencies,
        install_pipenv,
        build_pipenv_virtualenv,
        install_docker,
        install_minikube,
        install_kubectl,
        install_helm,
        helm_add_agones_repo,
        minikube_start_profile,
        helm_install_aimmo,
    ]

    _create_sudo_timestamp()

    for task in tasks:
        task(os_type, arch_type)


def windows_setup(os_type, arch_type):
    raise NotImplementedError


def linux_setup(os_type, arch_type):
    """
    Runs the commands needed in order to set up Kurono for LINUX
    Args:
        os_type (OSType): host OS type
        arch_type (ArchType): host architecture type
    """
    tasks = [
        update_apt_packages,
        install_nodejs,
        check_for_cmdtest,
        configure_yarn_repo,
        install_yarn,
        install_pip,
        install_pipenv,
        build_pipenv_virtualenv,
        set_up_frontend_dependencies,
        install_docker,
        install_minikube,
        install_kubectl,
        install_helm,
        helm_add_agones_repo,
        minikube_start_profile,
        helm_install_aimmo,
    ]

    _create_sudo_timestamp()

    for task in tasks:
        task(os_type, arch_type)


def _create_sudo_timestamp():
    """
    Request sudo access to create timestamp file for duration of setup
    """
    print("\033[1mrequesting_sudo_access\033[0m... ")

    # Request sudo password before task
    subprocess.Popen("sudo true", stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True).communicate()
    print("\033[1mrequesting_sudo_access\033[0m... [ \033[92mOK\033[0m ]")


def _cmd(command, comment=None):
    """
    Run command inside a terminal
    Args:
        command (str): command to be run
        comment (str): optional comment
    Returns:
        Tuple[int, List[str]]: return code, stdout lines output
    """
    stdout_lines = []

    if not comment:
        # Set comment to calling function name
        comment = inspect.currentframe().f_back.f_code.co_name

    if comment:
        print(" " * 110, end="\r")
        print("\033[1m%s\033[0m...\n" % comment, end="\r")

    p = subprocess.Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)

    for line in iter(p.stdout.readline, b""):
        stdout_lines.append(line.decode("utf-8"))
        sys.stdout.write("%s\r" % line.decode("utf-8")[:-1].rstrip())
        sys.stdout.flush()

    # Delete line
    sys.stdout.write("\x1b[2K")
    sys.stdout.write("\x1b[1A")

    p.communicate()

    if p.returncode != 0:
        if comment:
            sys.stdout.write("\033[1m%s\033[0m... [ \033[93mFAILED\033[0m ]\n" % comment)
        for line in stdout_lines:
            sys.stdout.write(f"{line}\n")
        raise CalledProcessError(p.returncode, command)

    if comment:
        sys.stdout.write("\033[1m%s\033[0m... [ \033[92mOK\033[0m ]\n" % comment)

    return (p.returncode, stdout_lines)


def ensure_homebrew_installed(os_type, arch_type):
    if os_type == OSType.MAC:
        _cmd("brew -v")


def install_sqlite3(os_type, arch_type):
    if os_type == OSType.MAC:
        try:
            if _cmd("sqlite3 -version", "check_sqlite3")[0] == 0:
                return
        except CalledProcessError:
            pass

        _cmd("brew install sqlite3")


def install_yarn(os_type, arch_type):
    if os_type in [OSType.MAC, OSType.LINUX]:
        try:
            if _cmd("yarn --version ", "check_yarn")[0] == 0:
                return
        except CalledProcessError:
            pass

    if os_type == OSType.MAC:
        _cmd("npm install --global yarn", "install yarn")
    elif os_type == OSType.LINUX:
        _cmd("sudo npm install --global yarn", "install yarn")


def set_up_frontend_dependencies(os_type, arch_type):
    if os_type == OSType.MAC:
        _cmd("cd ./game_frontend && yarn")
    elif os_type == OSType.LINUX:
        _cmd("cd ./game_frontend && sudo yarn")


def install_pipenv(os_type, arch_type):
    if os_type in [OSType.MAC, OSType.LINUX]:
        try:
            if _cmd("pipenv --version", "check_pipenv")[0] == 0:
                return
        except CalledProcessError:
            pass

    if os_type == OSType.MAC:
        _cmd("brew install pipenv")
    elif os_type == OSType.LINUX:
        _cmd("pip install pipenv")


def build_pipenv_virtualenv(os_type, arch_type):
    if os_type in [OSType.MAC, OSType.LINUX]:
        _cmd("pipenv install --dev")


def install_docker(os_type, arch_type):
    if os_type in [OSType.MAC, OSType.LINUX]:
        try:
            if _cmd("docker -v", "check_docker")[0] == 0:
                return
        except CalledProcessError:
            pass

    if os_type == OSType.MAC:
        _cmd("brew install --cask docker")
    elif os_type == OSType.LINUX:
        # First time install needs to setup a repository
        # Update the package and install them
        # Add Docker's GPG key
        # The following command is used to setup the stable repository
        # Install docker
        docker_install = """sudo apt-get update 
                sudo apt-get install -y ca-certificates curl gnupg lsb-release
                curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
                echo \
                "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
                $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
                sudo apt-get update
                sudo apt-get install -y docker-ce
                sudo apt-get install -y docker-ce-cli
                sudo apt-get install -y containerd.io
                """
        try:
            _cmd(docker_install)
        except CalledProcessError:
            print("\nInstalation failed, trying again..\n")
            _cmd(docker_install)


def install_minikube(os_type, arch_type, version=MINIKUBE_VERSION):
    comment = "install_minikube"

    if version == "latest":
        rc, lines = _cmd("curl https://api.github.com/repos/kubernetes/minikube/releases/latest | grep tag_name")
        match = re.search(r"(v[0-9\.]+)", lines[0])
        if rc == 0 and match:
            version = match.group(1)

    if os_type in [OSType.MAC, OSType.LINUX]:
        try:
            _, lines = _cmd("minikube version", "check_minikube")
            if version in lines[0]:
                return
        except CalledProcessError:
            pass

    if os_type == OSType.MAC:
        _cmd(
            "curl -Lo minikube https://storage.googleapis.com/minikube/releases/%s/minikube-darwin-%s"
            % (version, arch_type.name.lower()),
            comment + ": download",
        )
    elif os_type == OSType.LINUX:
        _cmd(
            "curl -Lo minikube https://storage.googleapis.com/minikube/releases/%s/minikube-linux-%s"
            % (version, arch_type.name.lower()),
            comment + ": download",
        )

    if os_type in [OSType.MAC, OSType.LINUX]:
        _cmd("chmod +x minikube", comment + ": set permissions")
        _cmd("sudo mv minikube /usr/local/bin/", comment + ": copy binary")


def install_kubectl(os_type, arch_type, version=KUBECTL_VERSION):
    comment = "install_kubectl"

    if version == "latest":
        rc, lines = _cmd("curl -L -s https://dl.k8s.io/release/stable.txt")
        if rc == 0:
            version = lines[0]

    if os_type in [OSType.MAC, OSType.LINUX]:
        try:
            _, lines = _cmd("kubectl version --client --short", "check_kubectl")
            if version in lines[0]:
                return
        except CalledProcessError:
            pass

    if os_type == OSType.MAC:
        _cmd(
            "curl -Lo kubectl https://dl.k8s.io/release/%s/bin/darwin/%s/kubectl"
            % (
                version,
                (arch_type.name).lower(),
            ),
            comment + ": download",
        )

    if os_type == OSType.LINUX:
        _cmd(
            "curl -Lo kubectl https://dl.k8s.io/release/%s/bin/linux/%s/kubectl"
            % (
                version,
                (arch_type.name).lower(),
            ),
            comment + ": download",
        )

    if os_type in [OSType.MAC, OSType.LINUX]:
        _cmd("chmod +x kubectl", comment + ": set permissions")
        _cmd("sudo mv kubectl /usr/local/bin/", comment + ": copy binary")


def install_helm(os_type, arch_type):
    if os_type in [OSType.MAC, OSType.LINUX]:
        try:
            rc, _ = _cmd("helm version > /dev/null", "check_helm")
            if rc == 0:
                return
        except CalledProcessError:
            pass

        _cmd("curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash")


def helm_add_agones_repo(os_type, arch_type):
    if os_type in [OSType.MAC, OSType.LINUX]:
        _cmd("helm repo add agones https://agones.dev/chart/stable && " "helm repo update")


def minikube_start_profile(os_type, arch_type):
    if os_type == OSType.MAC:
        _cmd("minikube start -p agones --driver=hyperkit")

    if os_type == OSType.LINUX:
        _cmd("minikube start -p agones")


def helm_install_aimmo(os_type, arch_type):
    if os_type in [OSType.MAC, OSType.LINUX]:
        try:
            if _cmd("helm status -n agones-system aimmo > /dev/null", "check_helm_aimmo")[0] == 0:
                return
        except CalledProcessError:
            pass

        _cmd(
            "minikube profile agones && "
            "helm install aimmo --namespace agones-system --create-namespace agones/agones"
        )


def install_pip(os_type, arch_type):
    if os_type == OSType.LINUX:
        try:
            if _cmd("pip --version", "check_pip")[0] == 0:
                return
        except CalledProcessError:
            pass
        _cmd("sudo apt-get install python3-pip", "install_pip")


def install_nodejs(os_type, arch_type):
    if os_type in [OSType.MAC, OSType.LINUX]:
        try:
            if _cmd("node --version", "check_nodejs")[0] == 0:
                return
        except CalledProcessError:
            pass
    if os_type == OSType.MAC:
        _cmd("brew install node@14")
    if os_type == OSType.LINUX:
        _cmd("curl -fsSL https://deb.nodesource.com/setup_14.x | sudo -E bash -" "sudo apt-get install -y nodejs")


def check_for_cmdtest(os_type, arch_type):
    """
    This function is for use within the Linux setup section of the script. It checks if
    the cmdtest package is installed, if it is we ask the user if we can remove it, if yes
    we remove the package, if not the process continues without removing it.
    """

    if os_type == OSType.LINUX:
        try:
            _cmd("dpkg-query -W -f='{status}' cmdtest")
        except CalledProcessError:
            return

        while True:
            choice = input(
                "Looks like cmdtest is installed on your machine. "
                "cmdtest clashes with yarn so we recommend to remove it. "
                "Is it okay to remove cmdtest? [y/n]"
            ).lower()
            if choice in ["y", "yes"]:
                _cmd("sudo apt-get remove -y cmdtest", "remove_cmdtest")
                break
            if choice in ["n", "no"]:
                print("Continuing without removing cmdtest...")
                break
            print("Please answer 'yes' or 'no' ('y' or 'n').")


def update_apt_packages(os_type, arch_type):
    if os_type == OSType.LINUX:
        _cmd("sudo apt-get update")


def configure_yarn_repo(os_type, arch_type):
    comment = "configure_yarn"
    if os_type == OSType.LINUX:
        _cmd(
            "curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -",
            comment + ": add key",
        )
        _cmd(
            'echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list',
            comment + ": add repo",
        )


if _name_ == "_main_":
    main()
[7:08 PM, 5/19/2024] Aaron Joel Cse Rec: coverage:
  precision: 2
  round: down
  range: "70...100"
  status:
    patch:
      default:
        target: 90%

ignore:
  - "aimmo_setup.py"
  - "run.py"
  - "aimmo/static/*"
  - "aimmo/static/*/"
  - "aimmo/static/*//"
  - "aimmo-game/agones/*"
  - "aimmo-game/agones/*/"
  - "aimmo_runner/*"
  - "aimmo_runner/*/"
  - "test_utils/*"
  - "setup.py"

comment: false
#!/usr/bin/env python
import argparse
import logging
import traceback

from aimmo_runner import runner

logging.basicConfig()

parser = argparse.ArgumentParser(description="Runs Kurono.")

parser.add_argument(
    "-t",
    "--target",
    dest="build_target",
    choices=["runner", "tester"],
    action="store",
    default="runner",
    help="""Specify the build stage you wish the docker containers to stop at.
                            By default we simply run the project. This can be used to run the tests
                            but it is recommended that you used 'all_tests.py'
                            Options: runner, tester  """,
)
parser.add_argument(
    "-c",
    "--using-cypress",
    dest="using_cypress",
    action="store_true",
    default=False,
    help="""Specify if you want to run the project for running Cypress tests. This
    disables the building of the Docker images and builds the frontend in production 
    mode without watching for changes.""",
)

if _name_ == "_main_":
    try:
        args = parser.parse_args()

        runner.run(
            using_cypress=args.using_cypress,
            build_target=args.build_target,
        )
    except Exception as err:
        traceback.print_exc()
        raise
import atexit
import os
import platform
import subprocess

import kubernetes
from kubernetes.client import AppsV1Api, CoreV1Api
from kubernetes.config import load_kube_config

from .docker_scripts import build_docker_images
from .shell_api import run_command

MINIKUBE_EXECUTABLE = "minikube"


def get_ip():
    internal_ip = str(
        run_command(
            "minikube -p agones ssh grep host.minikube.internal /etc/hosts".split(),
            capture_output=True,
        ).split()[0],
        "utf-8",
    )
    return internal_ip


def delete_components():
    apps_api_instance = AppsV1Api()
    api = CoreV1Api()
    for rs in apps_api_instance.list_namespaced_deployment("default").items:
        apps_api_instance.delete_namespaced_deployment(
            body=kubernetes.client.V1DeleteOptions(),
            name=rs.metadata.name,
            namespace="default",
            grace_period_seconds=0,
        )
    for service in api.list_namespaced_service(namespace="default").items:
        api.delete_namespaced_service(service.metadata.name, "default")

    delete_fleet_on_exit()


def restart_pods():
    """
    Disables all the components running in the cluster and starts them again
    with fresh updated state.
    :param game_creator_yaml: Replication controller yaml settings file.
    """
    print("Restarting pods")

    try:
        run_command(["kubectl", "create", "-f", "agones/fleet.yml"])
    except subprocess.CalledProcessError:
        run_command("kubectl delete fleet aimmo-game --ignore-not-found".split(" "))
        run_command("kubectl delete --all deployment -n default".split(" "))
        run_command(["kubectl", "create", "-f", "agones/fleet.yml"])


def create_roles():
    """
    Applies the service accounts, roles, and bindings for restricting
    the rights of certain pods and their processses.
    """
    run_command(["kubectl", "apply", "-Rf", "rbac"])


def delete_fleet_on_exit():
    print("Exiting")
    print("Deleting aimmo-game fleet")
    run_command(
        [
            "kubectl",
            "delete",
            "fleet",
            "aimmo-game",
            "--ignore-not-found",
        ]
    )


def start(build_target=None):
    """
    The entry point to the minikube class. Sends calls appropriately to set
    up minikube.
    """
    if platform.machine().lower() not in ("amd64", "x86_64"):
        raise ValueError("Requires 64-bit")
    os.environ["MINIKUBE_PATH"] = MINIKUBE_EXECUTABLE

    # We assume the minikube was started with a profile called "agones"
    load_kube_config(context="agones")

    create_roles()
    build_docker_images(MINIKUBE_EXECUTABLE, build_target=build_target)
    restart_pods()
    atexit.register(delete_components)
    print("Cluster ready")
[7:08 PM, 5/19/2024] Aaron Joel Cse Rec: from _future_ import absolute_import

import logging
import os
import sys

import django
from django.conf import settings

from .shell_api import log, run_command, run_command_async

ROOT_DIR_LOCATION = os.path.abspath(os.path.dirname((os.path.dirname(_file_))))

_MANAGE_PY = os.path.join(ROOT_DIR_LOCATION, "example_project", "manage.py")
_FRONTEND_BUNDLER_JS = os.path.join(ROOT_DIR_LOCATION, "game_frontend", "djangoBundler.js")

PROCESSES = []


def create_superuser_if_missing(username, password):
    from django.contrib.auth.models import User

    try:
        User.objects.get_by_natural_key(username)
    except User.DoesNotExist:
        log("Creating superuser %s with password %s" % (username, password))
        User.objects.create_superuser(username=username, email="admin@admin.com", password=password)


def build_worker_package():
    run_command([os.path.join(ROOT_DIR_LOCATION, "aimmo_runner", "build_worker_wheel.sh")], capture_output=True)


def build_frontend(using_cypress, capture_output):
    if using_cypress:
        run_command(["node", _FRONTEND_BUNDLER_JS], capture_output=capture_output)
    else:
        frontend_bundler = run_command_async(["node", _FRONTEND_BUNDLER_JS], capture_output=capture_output)
        PROCESSES.append(frontend_bundler)


def start_game_servers(build_target, server_args, capture_output: bool):
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(_file_)))
    sys.path.append(os.path.join(parent_dir, "aimmo_runner"))
    os.chdir(ROOT_DIR_LOCATION)

    # Import minikube here, so we can install the dependencies first
    from aimmo_runner import minikube

    minikube.start(build_target=build_target)

    server_args.append("0.0.0.0:8000")
    os.environ["AIMMO_MODE"] = "minikube"

    run_command(
        ["python", _MANAGE_PY, "start_game_servers_for_running_games"],
        capture_output=capture_output,
    )


def run(server_wait=True, using_cypress=False, capture_output=False, test_env=False, build_target=None):
    logging.basicConfig()

    build_worker_package()

    if test_env:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")
    else:
        sys.path.insert(0, os.path.join(ROOT_DIR_LOCATION, "example_project"))
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    django.setup()

    if using_cypress:
        settings.DEBUG = False
        os.environ["LOAD_KUBE_CONFIG"] = "0"

    os.environ["NODE_ENV"] = "development" if settings.DEBUG else "production"

    build_frontend(using_cypress, capture_output)

    run_command(["pip", "install", "-e", ROOT_DIR_LOCATION], capture_output=capture_output)

    if not test_env:
        run_command(["python", _MANAGE_PY, "migrate", "--noinput"], capture_output=capture_output)
        run_command(["python", _MANAGE_PY, "collectstatic", "--noinput", "--clear"], capture_output=capture_output)

    server_args = []
    if not using_cypress:
        start_game_servers(build_target, server_args, capture_output)

    os.environ["SERVER_ENV"] = "local"
    server = run_command_async(["python", _MANAGE_PY, "runserver"] + server_args, capture_output=capture_output)
    PROCESSES.append(server)

    if server_wait:
        try:
            game.wait()
        except NameError:
            pass

        server.wait()

    return PROCESSES
coding: utf-8 --
from setuptools import find_packages, setup

setup(
    name="aimmo_runner",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "django==3.2.25",
        "django-forms-bootstrap",
        "django-js-reverse",
        "docker<6",
        "eventlet",
        "hypothesis",
        "kubernetes==26.1.0",
        "psutil",
        "requests",
        "six",
    ],
    zip_safe=False,
)

Import errno
import os
import platform
import stat
import subprocess
import sys
from subprocess import CalledProcessError

try:
    from urllib.request import urlretrieve, urlopen
except ImportError:
    from urllib import urlretrieve, urlopen

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(_file_)))
TEST_BIN = os.path.join(BASE_DIR, "test-bin")
OS = platform.system().lower()
FILE_SUFFIX = ".exe" if OS == "windows" else ""
KUBECTL = os.path.join(TEST_BIN, "kubectl%s" % FILE_SUFFIX)
MINIKUBE = os.path.join(TEST_BIN, "minikube%s" % FILE_SUFFIX)
FNULL = open(os.devnull, "w")


def log(message):
    sys.stderr.write(message + "\n")


def run_command(args, capture_output=False):
    try:
        if capture_output:
            return subprocess.check_output(args)
        else:
            subprocess.check_call(args)
    except CalledProcessError as e:
        log("Command failed with exit status %d: %s" % (e.returncode, " ".join(args)))
        raise


def run_command_async(args, capture_output=False):
    env = os.environ.copy()
    if capture_output is True:
        p = subprocess.Popen(args, stdout=FNULL, stderr=subprocess.STDOUT, env=env)
    else:
        p = subprocess.Popen(args, env=env)
    return p


def binary_exists(filename):
    # Check if binary is callable on our path
    try:
        run_command([filename], True)
        return True
    except OSError:
        return False


def download_exec(url, dest):
    dest = urlretrieve(url, dest)[0]
    make_exec(dest)


def make_exec(file):
    current_stat = os.stat(file)
    os.chmod(file, current_stat.st_mode | stat.S_IEXEC)


def get_latest_github_version(repo):
    result = urlopen("https://github.com/%s/releases/latest" % repo)
    return result.geturl().split("/")[-1]
[7:09 PM, 5/19/2024] Aaron Joel Cse Rec: from _future_ import absolute_import

from django.contrib import admin

from .models import Avatar, Game


class GameDataAdmin(admin.ModelAdmin):
    search_fields = ["id", "owner_username", "owner_email"]
    list_display = ["id", "owner", "game_class", "school", "worksheet_id", "status", "creation_time", "is_archived"]
    raw_id_fields = ["owner", "main_user", "can_play", "game_class"]
    readonly_fields = ["players", "auth_token"]

    def players(self, obj):
        teacher_user = obj.game_class.teacher.new_user
        players = f"{teacher_user.first_name} {teacher_user.last_name}\n"
        players += "\n".join([student.new_user.first_name for student in obj.game_class.students.all()])
        return players

    def school(self, obj):
        if obj.game_class:
            return obj.game_class.teacher.school
        else:
            return None


def stop_game(game_admin, request, queryset):
    for game in queryset:
        game.status = Game.STOPPED
        game.save()


stop_game.short_description = "Stop selected games"


class AvatarDataAdmin(admin.ModelAdmin):
    search_fields = ["owner_username", "owner_email"]
    list_display = ["id", "owner_name", "game_id"]
    raw_id_fields = ["game"]
    readonly_fields = ["owner", "auth_token"]

    def owner_name(self, obj):
        return obj.owner

    def game_id(self, obj):
        return obj.game


admin.site.register(Game, GameDataAdmin)
admin.site.register(Avatar, AvatarDataAdmin)

GameDataAdmin.actions.append(stop_game)
 from django.conf import settings

#: URL function for locating the game server, takes one parameter game
GAME_SERVER_URL_FUNCTION = getattr(settings, "AIMMO_GAME_SERVER_URL_FUNCTION", None)
GAME_SERVER_PORT_FUNCTION = getattr(settings, "AIMMO_GAME_SERVER_PORT_FUNCTION", None)
GAME_SERVER_SSL_FLAG = getattr(settings, "AIMMO_GAME_SERVER_SSL_FLAG", False)

# Hostname for django server to pass onto a game server
DJANGO_BASE_URL_FOR_GAME_SERVER = getattr(settings, "AIMMO_DJANGO_BASE_URL", "localhost")
