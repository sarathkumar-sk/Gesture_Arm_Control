import cv2
import mediapipe as mp
import time
import serial




# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Initialize OpenCV window
cap = cv2.VideoCapture(0)

# Define screen dimensions and threshold parameters for movements
screen_width = 640
screen_height = 480
depth_threshold = 0.2
left_threshold = 0.3
right_threshold = 0.7
forward_threshold = 0.3
backward_threshold = 0.7

def is_fist_closed(hand_landmarks):
    # Check if the tips of the fingers are close to their respective bases
    finger_tips = [
        mp_hands.HandLandmark.INDEX_FINGER_TIP,
        mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
        mp_hands.HandLandmark.RING_FINGER_TIP,
        mp_hands.HandLandmark.PINKY_TIP
    ]
    finger_dips = [
        mp_hands.HandLandmark.INDEX_FINGER_DIP,
        mp_hands.HandLandmark.MIDDLE_FINGER_DIP,
        mp_hands.HandLandmark.RING_FINGER_DIP,
        mp_hands.HandLandmark.PINKY_DIP
    ]

    for tip, dip in zip(finger_tips, finger_dips):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[dip].y:
            return False
    return True

# Variables to track consistency duration for fist status and movement
def hand_movement_detection():

    ser = serial.Serial('COM19', 9600)  
    time.sleep(2)  
    def send_command(command):
        if command in ['F', 'B', 'L', 'R', 'P', 'D']:  
            ser.write(command.encode())  
            print(f"Command sent: {command}")
        else:
            print("Invalid command.")
    end_effector = None
    act = None
    start_time = None
    last_fist_status = None
    last_movement = None
    consistency_duration = 2  # seconds

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Flip the frame for a selfie view
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Convert the frame to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process frame with MediaPipe Hands
        results = hands.process(rgb_frame)

        # Check if any hand is detected
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Get x, y, and z positions for the wrist landmark
                wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                x, y, z = wrist.x, wrist.y, wrist.z

                # Determine movements based on x, y, z position thresholds
                if x < left_threshold:
                    movement = "Moving Left"
                elif x > right_threshold:
                    movement = "Moving Right"
                elif y < forward_threshold:
                    movement = "Moving Forward"
                elif y > backward_threshold:
                    movement = "Moving Backward"
                else:
                    movement = "Neutral"

                # Show depth information for movement (based on z-axis)
                depth_effect = "Close" if abs(z) < depth_threshold else "Far"

                # Check if the hand is in a fist
                fist_status = "Fist Closed" if is_fist_closed(hand_landmarks) else "Hand Open"

                # Check if fist_status and movement have stayed the same
                if fist_status == last_fist_status and movement == last_movement:
                    if start_time is None:
                        start_time = time.time()
                    elif time.time() - start_time >= consistency_duration:
                        print(f"Consistent Movement: {movement}")
                        if movement == "Moving Left":
                            act = "L"
                        elif movement == "Moving Right":
                            act = "R"
                        elif movement == "Moving Forward":
                            act = "F"
                        elif movement == "Moving Backward":
                            act = "B"
                        print(act)
                        send_command(act)
                        if fist_status != end_effector:
                            end_effector = fist_status
                            if end_effector == "Fist Closed":
                                send_command('P')
                            else:
                                send_command('D')
                        print(f"Consistent Fist Status: {fist_status}")
                        start_time = None  # Reset the timer
                else:
                    # Reset if status or movement changes
                    start_time = time.time()  # Restart the timer
                    last_fist_status = fist_status
                    last_movement = movement

                # Display text on the screen
                cv2.putText(frame, f"Direction: {movement}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)
                cv2.putText(frame, f"Depth Effect: {depth_effect}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (9,0,0), 2)
                cv2.putText(frame, f"Fist Status: {fist_status}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

        # Show the frame with annotations
        cv2.imshow("Hand Control with Depth Effect", frame)

        # Exit on pressing 'q'
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()
