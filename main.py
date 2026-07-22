from core.engine import QwenEngine
from core.controller import Controller


def main():

    print("\nInitializing AI Software Engineer...\n")

    engine = QwenEngine()

    controller = Controller(engine)

    print("\n========================================")
    print("        AI SOFTWARE ENGINEER")
    print("========================================")

    while True:

        print("\n1. Create Project")
        print("2. Exit")

        choice = input("\nChoice > ").strip()

        if choice == "2":

            print("\nGoodbye!")

            break

        elif choice == "1":

            user_request = input(
                "\nDescribe your project:\n\n> "
            ).strip()

            if not user_request:

                print("\nProject description cannot be empty.")

                continue

            success = controller.run(user_request)

            if success:

                print("\n========================================")
                print("PROJECT COMPLETED SUCCESSFULLY")
                print("========================================")

            else:

                print("\n========================================")
                print("PROJECT FAILED")
                print("========================================")

        else:

            print("\nInvalid choice.")


if __name__ == "__main__":
    main()