import sys
from ui.gui import launch_gui
from core.repl import start_terminal
from ui.banner import show_banner


def main():

    if "--cli" in sys.argv:
        show_banner()
        start_terminal()
    else:
        launch_gui()


if __name__ == "__main__":
    main()