# combined_detection.py
import cv2
import mediapipe as mp
import time
import serial

# Uncomment if you want to use serial communication


mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

def detect_thumb_direction(landmarks):
    wrist = landmarks[0]
    thumb_tip = landmarks[4]
    thumb_mcp = landmarks[2]
    thumb_vector_x = thumb_tip.x - thumb_mcp.x
    thumb_vector_y = thumb_tip.y - thumb_mcp.y

    if abs(thumb_vector_x) > abs(thumb_vector_y) or (thumb_vector_x < 0 and thumb_vector_y < 0):
        if thumb_tip.x < wrist.x:
            return "Thumb pointing Left"
        else:
            return "Thumb pointing Right"
    else:
        if thumb_tip.y < thumb_mcp.y:
            return "Thumb pointing Up"
        else:
            return "Thumb pointing Down"

def detect_pick_drop(landmarks):
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    middle_tip = landmarks[12]
    ring_tip = landmarks[16]
    pinky_tip = landmarks[20]

    thumb_mcp = landmarks[2]
    index_mcp = landmarks[5]
    middle_mcp = landmarks[9]
    ring_mcp = landmarks[13]
    pinky_mcp = landmarks[17]

    is_thumb_open = thumb_tip.x > thumb_mcp.x
    is_index_open = index_tip.y < index_mcp.y
    is_middle_open = middle_tip.y < middle_mcp.y
    is_ring_open = ring_tip.y < ring_mcp.y
    is_pinky_open = pinky_tip.y < pinky_mcp.y

    if is_thumb_open and is_index_open and is_middle_open and is_ring_open and is_pinky_open:
        return "Pick"
    if not is_thumb_open and is_index_open and is_middle_open and not is_ring_open and not is_pinky_open:
        return "Drop"
    return None

def run_combined_detection():
        
    ser = serial.Serial('COM19', 9600)  
    time.sleep(2)  

    def send_command(command):
        if command in ['F', 'B', 'L', 'R', 'P', 'D']:  
            ser.write(command.encode())  
            print(f"Command sent: {command}")
        else:
            print("Invalid command.")
    cap = cv2.VideoCapture(0)

    current_action = None
    start_time = None
    action_locked = False
    lock_start_time = None
    lock_duration = 2  

    with mp_hands.Hands(
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as hands:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)  # Fixed typo
                    
                    gesture = detect_pick_drop(hand_landmarks.landmark)
                    if gesture:
                        detected_action = gesture
                    else:
                        detected_action = detect_thumb_direction(hand_landmarks.landmark)
                    
                    if detected_action == current_action:
                        if not action_locked and start_time and (time.time() - start_time >= 2):
                            print(current_action)
                            action_locked = True
                            lock_start_time = time.time()  
                            
                            act = None
                            match current_action:
                                case "Thumb pointing Up":
                                    act = "B"
                                case "Thumb pointing Down":
                                    act = "F"
                                case "Thumb pointing Left":
                                    act = "L"
                                case "Thumb pointing Right":
                                    act = "R"
                                case "Pick":
                                    act = "P"
                                case "Drop":
                                    act = "D"
                            print(act)
                            send_command(act)  
                            
                    elif action_locked and time.time() - lock_start_time >= lock_duration:
                        current_action = detected_action
                        start_time = time.time()
                        action_locked = False
                    elif not action_locked:
                        current_action = detected_action
                        start_time = time.time()
                   
                    if action_locked:
                        cv2.putText(frame, f"Locked Action: {current_action}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                        time_remaining = lock_duration - int(time.time() - lock_start_time)
                        cv2.putText(frame, f"Timer: {time_remaining}s", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

                        if time.time() - lock_start_time >= lock_duration:
                            action_locked = False
                            current_action = None
                            start_time = None
                    else:
                        cv2.putText(frame, f"Current Action: {detected_action}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

            cv2.imshow("Thumb Direction and Pick/Drop Detection", frame)

            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
