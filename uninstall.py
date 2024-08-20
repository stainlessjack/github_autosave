import os
import subprocess
import sys
import platform

def remove_task_scheduler():
    task_name = "Github Autosave"
    subprocess.run(f'schtasks /delete /tn "{task_name}" /f', shell=True)
    print(f"Task removed: {task_name}")

def remove_env_variable(var_name):
    subprocess.run(f'reg delete "HKCU\\Environment" /F /V {var_name}', shell=True)
    print(f"Environment variable removed: {var_name}")

def remove_config_file():
    config_file = os.environ.get('GITHUB_AUTOSAVE_CONFIG_FILE')
    if config_file and os.path.exists(config_file):
        os.remove(config_file)
        print(f"Config file removed: {config_file}")
    else:
        print("Config file not found or already removed")

def main():
    # Gather OS information
    os_name = platform.system()
    print(f"OS: {os_name}")

    if os_name == "Windows":
        # Remove scheduled task
        remove_task_scheduler()

        # Remove config file
        remove_config_file()

        # Remove environment variables
        remove_env_variable("GITHUB_AUTOSAVE_PROJECTS_DIR")
        remove_env_variable("GITHUB_AUTOSAVE_CONFIG_FILE")
    else:
        print("Unsupported OS for uninstallation")
        sys.exit(1)

    print("Uninstallation complete!")

if __name__ == "__main__":
    main()