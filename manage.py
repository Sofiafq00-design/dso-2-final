import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "biblioteca_project.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as error:
        raise ImportError(
            "No se pudo importar Django. Instale las dependencias con "
            "'pip install -r requirements.txt'."
        ) from error
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
