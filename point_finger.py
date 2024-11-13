import cv2
import mediapipe as mp
import time
import serial


mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

def get_screen_section(finger_x, frame_width):
    section_width = frame_width // 6  
    section = (finger_x // section_width) + 1
    return int(section)

section_to_action = {
    1: 'D',  # Drop
    2: 'P',  # Pick
    3: 'F',  # Forward
    4: 'B',  # Backward
    5: 'L',  # Left
    6: 'R'   # Right
}

def run_point_finger():

    # Initialize serial communication
    ser = serial.Serial('COM19', 9600)  
    time.sleep(2)  

    def send_command(command):
        if command in ['F', 'B', 'L', 'R', 'P', 'D']:  
            ser.write(command.encode())  
            print(f"Command sent: {command}")
        else:
            print("Invalid command.")
    cap = cv2.VideoCapture(0)
    last_section = None
    last_section_time = None
    action_lock_time = None
    locked_action = None
    lock_duration = 2

    with mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7) as hands:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
            
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_height, frame_width, _ = frame.shape
            
            results = hands.process(frame_rgb)
            current_time = time.time()
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    index_finger_x = int(index_finger_tip.x * frame_width)
                    index_finger_y = int(index_finger_tip.y * frame_height)
                    
                    section = get_screen_section(index_finger_x, frame_width)
                    section_label = section_to_action.get(section, "")
                    
                    if action_lock_time and (current_time - action_lock_time < lock_duration):
                        cv2.putText(frame, f'Action Locked: {locked_action}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    else:
                        action_lock_time = None
                        locked_action = None
                        if section == last_section:
                            if last_section_time and (current_time - last_section_time > 2):
                                locked_action = section_to_action.get(section, None)
                                if locked_action:
                                    print(f"Action: {locked_action}")
                                    send_command(locked_action)
                                    action_lock_time = current_time
                        else:
                            last_section = section
                            last_section_time = current_time
                        cv2.putText(frame, f'Section: {section_label}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    cv2.circle(frame, (index_finger_x, index_finger_y), 10, (0, 0, 255), -1)

            for i in range(6):
                x = i * frame_width // 6
                cv2.line(frame, (x, 0), (x, frame_height), (255, 0, 0), 2)
                section_label = section_to_action.get(i + 1, "")
                cv2.putText(frame, section_label, (x + 10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
            cv2.imshow("Finger Position Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

# import cv2
# import mediapipe as mp
# import time

# mp_hands = mp.solutions.hands
# mp_drawing = mp.solutions.drawing_utils

# def get_screen_section(finger_x, frame_width):
#     section_width = frame_width // 6  
#     section = (finger_x // section_width) + 1
#     return int(section)

# section_to_action = {
#     1: 'D',  # Drop
#     2: 'P',  # Pick
#     3: 'F',  # Forward
#     4: 'B',  # Backward
#     5: 'L',  # Left
#     6: 'R'   # Right
# }

# cap = cv2.VideoCapture(0)

# last_section = None
# last_section_time = None
# action_lock_time = None
# locked_action = None
# lock_duration = 2  

# with mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7) as hands:
#     while cap.isOpened():
#         success, frame = cap.read()
#         if not success:
#             break
    
#         frame = cv2.flip(frame, 1)
#         frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         frame_height, frame_width, _ = frame.shape
        
#         results = hands.process(frame_rgb)
        
#         current_time = time.time()
        
#         if results.multi_hand_landmarks:
#             for hand_landmarks in results.multi_hand_landmarks:
#                 mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
#                 index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                
#                 index_finger_x = int(index_finger_tip.x * frame_width)
#                 index_finger_y = int(index_finger_tip.y * frame_height)
                
#                 section = get_screen_section(index_finger_x, frame_width)
#                 section_label = section_to_action.get(section, "")
#                 if action_lock_time and (current_time - action_lock_time < lock_duration):
#                     cv2.putText(frame, f'Action Locked: {locked_action}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
#                 else:
#                     action_lock_time = None
#                     locked_action = None

#                     if section == last_section:
#                         if last_section_time and (current_time - last_section_time > 2):
                        
#                             locked_action = section_to_action.get(section, None)
#                             if locked_action:
#                                 print(f"Action: {locked_action}")
#                                 action_lock_time = current_time
#                     else:
#                         last_section = section
#                         last_section_time = current_time
                    
#                     cv2.putText(frame, f'Section: {section_label}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
#                 cv2.circle(frame, (index_finger_x, index_finger_y), 10, (0, 0, 255), -1)

#         for i in range(6):
#             x = i * frame_width // 6
#             cv2.line(frame, (x, 0), (x, frame_height), (255, 0, 0), 2)
#             section_label = section_to_action.get(i + 1, "")
#             cv2.putText(frame, section_label, (x + 10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
#         cv2.imshow("Finger Position Detection", frame)
        
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

# cap.release()
# cv2.destroyAllWindows()
