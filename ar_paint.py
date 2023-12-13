#!/usr/bin/env python3
import cv2
import json
import argparse
import numpy as np
from time import ctime
from functools import partial
from math import sqrt

def mouseCallback(event, x, y, flags, *userdata, image_canvas, drawing_data):
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing_data['pencil_down'] = True
        print('Pencil down set to True')
    elif event == cv2.EVENT_LBUTTONUP:
        drawing_data['pencil_down'] = False
        print('Pencil down released')

    if drawing_data['pencil_down'] == True:
        cv2.line(image_canvas, (drawing_data['previous_x'], drawing_data['previous_y']), (x, y),
                 drawing_data['color'], drawing_data['size'])

    drawing_data['previous_x'] = x
    drawing_data['previous_y'] = y

def main():
    parser = argparse.ArgumentParser(description='Definition of test mode')
    parser.add_argument('-j', '--json', type=str, required=True, help='Full path to json file.')
    args = vars(parser.parse_args())

    cv2.namedWindow('AR Paint')

    # Read data from the json file
    with open(args['json'], 'r') as json_file:
        data = json.load(json_file)

    # Setup video capture
    cap = cv2.VideoCapture(0)

    # Create a white canvas
    _, image_canvas = cap.read()
    image_canvas = np.ones_like(image_canvas) * 255

    drawing_data = {'pencil_down': False, 'previous_x': 0, 'previous_y': 0, 'color': (0, 0, 255), 'size': 1}

    cv2.setMouseCallback("AR Paint", partial(mouseCallback, image_canvas=image_canvas, drawing_data=drawing_data))

    while True:
        # Acquire an image from the camera
        _, image = cap.read()

        # Process the image to create a mask based on color limits
        mask = cv2.inRange(image, (data['limits']['B']['min'], data['limits']['G']['min'], data['limits']['R']['min']),
                           (data['limits']['B']['max'], data['limits']['G']['max'], data['limits']['R']['max']))

        # Find connected components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=4)

        # Use connectedComponentsWithStats to label connected components
        if num_labels > 1:
            max_label, _ = max([(i, stats[i, cv2.CC_STAT_AREA]) for i in range(1, num_labels)], key=lambda x: x[1])
            centroids = (int(centroids[max_label][0]), int(centroids[max_label][1]))
            m = np.equal(labels, max_label)
            b, g, r = cv2.split(image_canvas)
            b[m] = 0
            r[m] = 0
            g[m] = 0
            image_canvas = cv2.merge((b, g, r))
            cv2.line(image_canvas, (centroids[0] + 5, centroids[1]), (centroids[0] - 5, centroids[1]), (0, 0, 255), 5, -1)
            cv2.line(image_canvas, (centroids[0], centroids[1] + 5), (centroids[0], centroids[1] - 5), (0, 0, 255), 5, -1)
            drawing_data['pencil_down'] = True
        else:
            print("No color")
            drawing_data['pencil_down'] = False

        if drawing_data['pencil_down']:
            x, y = centroids
            x += 1
            y += 1
            cv2.line(image_canvas, (x, y), (drawing_data['previous_x'], drawing_data['previous_y']),
                     drawing_data['color'], drawing_data['size'], -1)

        drawing_data['previous_x'] = x
        drawing_data['previous_y'] = y

        cv2.imshow("AR Paint", image_canvas)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('r'):
            drawing_data['color'] = (0, 0, 255)  # Red
        elif key == ord('g'):
            drawing_data['color'] = (0, 255, 0)  # Green
        elif key == ord('b'):
            drawing_data['color'] = (255, 0, 0)  # Blue
        elif key == ord('+'):
            drawing_data['size'] += 1
        elif key == ord('-'):
            drawing_data['size'] = max(1, drawing_data['size'] - 1)
        elif key == ord('c'):
            image_canvas = np.ones_like(image_canvas) * 255
        elif key == ord('w'):
            filename = f'drawing_{ctime().replace(" ", "_")}.png'
            cv2.imwrite(filename, image_canvas)
            print(f"Canvas saved as {filename}")
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
