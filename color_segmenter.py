#!/usr/bin/env python3
import cv2
import json
import argparse

def nothing(x):
    pass

def main():
    parser = argparse.ArgumentParser(description='Definition of test mode')
    parser.add_argument('-j', '--json', type=str, required=True, help='Full path to json file.')
    args = vars(parser.parse_args())

    cv2.namedWindow('Color Segmenter')

    cv2.createTrackbar('min B', 'Color Segmenter', 0, 255, nothing)
    cv2.createTrackbar('max B', 'Color Segmenter', 255, 255, nothing)
    cv2.createTrackbar('min G', 'Color Segmenter', 0, 255, nothing)
    cv2.createTrackbar('max G', 'Color Segmenter', 255, 255, nothing)
    cv2.createTrackbar('min R', 'Color Segmenter', 0, 255, nothing)
    cv2.createTrackbar('max R', 'Color Segmenter', 255, 255, nothing)

    while True:
        # Read image from camera
        cap = cv2.VideoCapture(0)
        _, image = cap.read()
        cap.release()

        # Get trackbar positions
        min_b = cv2.getTrackbarPos('min B', 'Color Segmenter')
        max_b = cv2.getTrackbarPos('max B', 'Color Segmenter')
        min_g = cv2.getTrackbarPos('min G', 'Color Segmenter')
        max_g = cv2.getTrackbarPos('max G', 'Color Segmenter')
        min_r = cv2.getTrackbarPos('min R', 'Color Segmenter')
        max_r = cv2.getTrackbarPos('max R', 'Color Segmenter')

        # Create mask
        mask = cv2.inRange(image, (min_b, min_g, min_r), (max_b, max_g, max_r))
        result = cv2.bitwise_and(image, image, mask=mask)

        cv2.imshow('Color Segmenter', result)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('w'):
            # Save limits to json
            limits = {
                'limits': {
                    'B': {'min': min_b, 'max': max_b},
                    'G': {'min': min_g, 'max': max_g},
                    'R': {'min': min_r, 'max': max_r}
                }
            }
            with open(args['json'], 'w') as json_file:
                json.dump(limits, json_file)
            print("Limits saved to", args['json'])
        elif key == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
