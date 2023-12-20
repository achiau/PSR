import cv2
import numpy as np
import json
import datetime

# Function to draw a cross at the centroid
def draw_cross(img, centroid, color):
    x, y = centroid
    cv2.line(img, (x - 10, y), (x + 10, y), color, 2)
    cv2.line(img, (x, y - 10), (x, y + 10), color, 2)

# Function to draw a dot at the centroid
def draw_dot(img, centroid, color, size):
    cv2.circle(img, centroid, size, color, -1)

# Function to clear the canvas
def clear_canvas(canvas):
    canvas[:] = 255  # Fill with white

# Function to save the current canvas with a timestamp
def save_canvas(canvas):
    timestamp = datetime.datetime.now().strftime("%a_%b_%d_%H:%M:%S_%Y")
    filename = f"drawing_{timestamp}.png"
    cv2.imwrite(filename, canvas)
    print(f"Saved {filename}")

# Initialize canvas
canvas = np.ones((480, 640, 3), np.uint8) * 255  # White canvas

# Read color limits from JSON file
with open('limits.json', 'r') as json_file:
    limits = json.load(json_file)

# Convert limits to numpy array
lower_bound = np.array([limits['limits']['B']['min'], limits['limits']['G']['min'], limits['limits']['R']['min']])
upper_bound = np.array([limits['limits']['B']['max'], limits['limits']['G']['max'], limits['limits']['R']['max']])

# Create VideoCapture object
cap = cv2.VideoCapture(0)

while True:
    # Capture frame-by-frame
    _, frame = cap.read()

    # Blur for better object detection
    blurred = cv2.GaussianBlur(frame, (11, 11), 0)

    # Convert to HSV color space
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # Create a mask
    mask = cv2.inRange(hsv, lower_bound, upper_bound)

    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Find the contour with the largest area
        largest_contour = max(contours, key=cv2.contourArea)

        # Draw the largest contour on the frame
        cv2.drawContours(frame, [largest_contour], -1, (0, 255, 0), 2)

        # Calculate centroid of the largest contour
        M = cv2.moments(largest_contour)
        if M["m00"] != 0:
            centroid_x = int(M["m10"] / M["m00"])
            centroid_y = int(M["m01"] / M["m00"])
            centroid = (centroid_x, centroid_y)

            # Draw a cross at the centroid
            draw_cross(frame, centroid, (0, 0, 255))

            # Get keyboard input
            key = cv2.waitKey(1) & 0xFF

            # Change pencil color
            if key == ord('r'):
                color = (0, 0, 255)  # Red
            elif key == ord('g'):
                color = (0, 255, 0)  # Green
            elif key == ord('b'):
                color = (255, 0, 0)  # Blue

            # Change pencil size
            elif key == ord('+'):
                size += 1
            elif key == ord('-'):
                size = max(1, size - 1)

            # Clear canvas
            elif key == ord('c'):
                clear_canvas(canvas)

            # Save canvas
            elif key == ord('w'):
                save_canvas(canvas)

            # End program
            elif key == ord('q'):
                break

            # Draw with the pencil
            draw_dot(canvas, centroid, color, size)

    # Display the resulting frame and canvas
    cv2.imshow("AR Paint", frame)
    cv2.imshow("Canvas", canvas)

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
