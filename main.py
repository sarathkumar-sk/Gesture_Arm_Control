# main.py
import point_finger
import movement_detection
import thumb_detection

def main():
    print("Choose which function to run:")
    print("1. Run point_finger function")
    print("2. Run movement_detection function")
    print("3. Run thumb based detection function")

    choice = input("Enter 1, 2, or 3: ")
    if choice == '1':
        point_finger.run_point_finger()
    elif choice == '2':
        movement_detection.hand_movement_detection()
    elif choice == '3':
        thumb_detection.run_combined_detection()
    else:
        print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
