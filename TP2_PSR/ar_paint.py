#!/usr/bin/env python3
import cv2
import json
import argparse
import numpy as np
from colorama import Back, Fore, Style
from functools import partial
from math import sqrt
from time import ctime

def process_image(image, data, height, width, mask_color):
    # Extract color limits from data
    bmin, bmax = data['limits']['B']['min'], data['limits']['B']['max']
    gmin, gmax = data['limits']['G']['min'], data['limits']['G']['max']
    rmin, rmax = data['limits']['R']['min'], data['limits']['R']['max']

    # Create mask
    mask = cv2.inRange(image, (bmin, gmin, rmin), (bmax, gmax, rmax))
    green_mask = np.zeros((height, width, 3), np.uint8)
    green_mask[mask > 0] = mask_color

    # Apply mask to the image
    mask_image = cv2.add(green_mask, image)
    
    return mask_image, green_mask

def get_connected_components(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Threshold to binary image
    _, binary_image = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Find connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_image, connectivity=4)
    return num_labels, labels, stats, centroids

def mouse_callback(event, x, y, flags, *userdata, image_canvas, drawing_data):
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing_data['pencil_down'] = True
        print(Fore.BLUE + 'Pencil down set to True' + Fore.RESET)
    elif event == cv2.EVENT_LBUTTONUP: 
        drawing_data['pencil_down'] = False
        print(Fore.RED + 'Pencil down released' + Fore.RESET)

    if drawing_data['pencil_down']:
        cv2.line(image_canvas, (drawing_data['previous_x'], drawing_data['previous_y']), (x, y), drawing_data['color'], drawing_data['size']) 

    drawing_data['previous_x'] = x
    drawing_data['previous_y'] = y

def main():
    parser = argparse.ArgumentParser(description='Definition of ' + Fore.BLUE + 'test ' + Fore.RESET + 'mode')
    parser.add_argument('-j', '--json', type=str, required=True, help='Full path to' + Fore.YELLOW + ' json ' + Fore.RESET + 'file.')
    parser.add_argument('-mc', '--mask_color', type=str, choices=['green', 'red', 'blue'], required=False, help='Choose the color of the mask.')
    parser.add_argument('-usp', '--use_shake_prevention', required=False, action='store_true', help="Use Shake prevention for more perfect lines.")
    parser.add_argument('-um', '--use_mouse', default=False, action='store_true', help="Use the mouse instead of the red point.")
    parser.add_argument('-cam', '--use_camera', action='store_true', help="Draw directly in the image given by the camera.")
    parser.add_argument('-z', '--zones', action='store_true', required=False, help='Display a blank canvas with numbered zones')
    args = vars(parser.parse_args())

    print('Welcome to the drawing game!')
    print('To change your drawing color to blue, red or green, press ' + Back.BLUE + '"B"' + Style.RESET_ALL + ', ' + Back.RED + '"R"' + Style.RESET_ALL + 
          ' or ' + Back.GREEN + '"G"' + Style.RESET_ALL + ', respectively.')
    print('If you want to change your pencil size, press ' + Fore.BLACK + Back.LIGHTYELLOW_EX +  '"+"' + Style.RESET_ALL + ' or '+ Fore.BLACK  + Back.LIGHTYELLOW_EX +  '"-"' + Style.RESET_ALL + ' to increase and decrease its size, respectively!')
    print('Hate what you\'re drawing? Press '+ Fore.BLACK  + Back.LIGHTGREEN_EX +  '"C"' + Style.RESET_ALL + 
          ' to clear the board! Want to boast about your drawing skills instead? Press '+ Fore.BLACK + Back.LIGHTGREEN_EX +'"w"' + Style.RESET_ALL + ' to save the drawing board')
    print('When you\'re done creating the masterpiece of a lifetime, press ' + Back.LIGHTRED_EX + '"Q"' + Style.RESET_ALL + ' to quit the game.')

    drawing_data = {'pencil_down': False, 'previous_x': 0, 'previous_y': 0, 'color': (0, 0, 0), 'size': 5}
    
    capture = cv2.VideoCapture(0)
    
    mask_color = {'green': (0, 255, 0), 'red': (0, 0, 255), 'blue': (255, 0, 0)}.get(args['mask_color'], (0, 255, 0))

    cv2.namedWindow('Canva Draw')

    _, image = capture.read()  # get an image from the camera
    height, width, channels = image.shape

    if args['use_mouse']:
        cv2.setMouseCallback("Canva Draw", partial(mouse_callback, image_canvas=image, drawing_data=drawing_data))

    flag_first = True
    drawing_data['last_point'] = None 
    
    while True:
        ret, image_base = capture.read()

        if not ret:
            print('No image from the camera')
            break

        image = cv2.flip(image_base, 1)

        open_file = open(args['json'])
        data = json.load(open_file)
        open_file.close()

        mask_image, mask = process_image(image, data, height, width, mask_color)

        if args['use_mouse']:
            pass  # Handle mouse drawing in the callback
        else:
            num_labels, labels, stats, centroids = get_connected_components(mask)
            if num_labels > 1:
                max_label, _ = max([(i, stats[i, cv2.CC_STAT_AREA]) for i in range(1, num_labels)], key=lambda x: x[1])
                centroids = (int(centroids[max_label][0]), int(centroids[max_label][1]))
                m = np.equal(labels, max_label)
                b, g, r = cv2.split(mask_image)
                b[m] = 0
                r[m] = 0
                g[m] = 0
                mask_image = cv2.merge((b, g, r))
                cv2.line(mask_image, (centroids[0] + 5, centroids[1]), (centroids[0] - 5, centroids[1]), (0, 0, 255), 5, -1)
                cv2.line(mask_image, (centroids[0], centroids[1] + 5), (centroids[0], centroids[1] - 5), (0, 0, 255), 5, -1)
                drawing_data['pencil_down'] = True
            else:
                print("No color")
                drawing_data['pencil_down'] = False
            
            if drawing_data['pencil_down']:        
                if drawing_data['last_point'] is not None and centroids is not None:
                    distance = (drawing_data['last_point'][0] - centroids[0]) ** 2 + (drawing_data['last_point'][1] - centroids[1]) ** 2

                    if args['use_shake_prevention']:
                        if distance > 1600:
                            cv2.circle(image, centroids, 1, drawing_data['color'], -1)
                    x, y = centroids
                    x += 1
                    y += 1
                    if flag_first:
                        cv2.line(image, (x, y), centroids, drawing_data['color'], drawing_data['size'], -1)
                    else:
                        cv2.line(image, drawing_data['last_point'], centroids, drawing_data['color'], drawing_data['size'], -1)

                    drawing_data['last_point'] = centroids

            if args["use_camera"]:
                mask_camera = np.not_equal(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), 255)
                mask_camera = np.repeat(mask_camera[:, :, np.newaxis], 3, axis=2)
                output = image.copy()
                
                output[mask_camera] = image[mask_camera]

            else:
                output = image

        if args['use_mouse']:
            cv2.imshow("Canva Draw", image)
        else:
            cv2.imshow("Canva Draw", mask_image)

        if not args['use_mouse']:
            cv2.imshow("Camera", mask)

        flag_first = False
        key = cv2.waitKey(25)
        
        if key == ord('q'):
            print('Quitting the game...')
            break

        elif key == ord('r'): 
            print('Setting pencil to red color')
            drawing_data['color'] = (0, 0, 255)

        elif key == ord('g'): 
            print('Setting pencil to green color')
            drawing_data['color'] = (0, 255, 0)

        elif key == ord('b'): 
            print('Setting pencil to blue color')
            drawing_data['color'] = (255, 0, 0)

        elif key == ord('-'): 
            print('Decreasing pencil size')
            if drawing_data['size'] > 1:
                drawing_data['size'] -= 1
                print("Decreased to " + str(drawing_data['size']))

        elif key == ord('+'): 
            print('Increasing pencil size')
            if drawing_data['size'] < 50:
                drawing_data['size'] += 1
                print("Increased to " + str(drawing_data['size']))

        elif key == ord('c'): 
            print('Clearing canvas')
            image = np.ones((height, width, 3), dtype=np.uint8) * 255

        elif key == ord('w'): 
            print('Saving image')
            new_name = ctime().replace(' ', '_')
            cv2.imwrite(f'drawing_{new_name}.png', image)

    capture.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()