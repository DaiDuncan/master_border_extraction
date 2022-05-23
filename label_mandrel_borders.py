import json
import os.path
import sys
import time
from datetime import datetime

import cv2
import numpy as np
from matplotlib import pyplot as plt

PATH_LABELS_FILE = 'labels_reduced.json'
PATH_IMAGES = '\\\\os.lsdf.kit.edu\\itiv-projects\\Stents4Tomorrow\\Data\\2022-04-28\\Data\\Images'  # TODO


def _get_labels():
    with open(PATH_LABELS_FILE, 'r') as f:
        labels = json.load(f)
    return labels


def _get_num_entries(labels):
    return sum([
        len(list(labels[folder].keys())) for folder in labels.keys()
    ])


def _load_image(folder, image):
    image_record = image
    loaded = False
    while not loaded:
        ### Problem: always shows 'Error loading...' 
        ### cv2.cvtColor() returns None  2022.05.23
        try:
            image = cv2.imread(os.path.join(
                PATH_IMAGES, folder, image + '.png'))
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            loaded = True
        except:
            loaded = False
            print('{}: Error loading image - retrying..'.format(datetime.now())) 
            print('The number of error image is {}'.format(image_record))
            time.sleep(1)

        if image is None:
            return None
    return image


def save_dict(labels):
    saved = False
    while not saved:
        try:
            with open(PATH_LABELS_FILE, 'w') as f:
                json.dump(labels, f)
            saved = True
        except:
            saved = False
            time.sleep(1)


def update_labels(labels, control_dict):
    labels[control_dict['folder']][control_dict['image']] = {
        'height': control_dict['height'],
        'width': control_dict['width'],
        'coords': [
            control_dict['x1'], control_dict['x2']
        ]
    }
    return labels


labels = None
image_counter = 0
starting = None


def label_borders():
    global starting
    starting = datetime.now()
    global image_counter
    global labels
    labels = _get_labels()   # "labels" is json data
    num_labels = _get_num_entries(labels)   # number of all images from selected folders in JSON

    index = 0
    control_dict = dict()
    for folder in labels.keys():
        for image_nr in labels[folder].keys():   # the name/number of image
            index += 1
            if labels[folder][image_nr] is not None:
                continue
            image_counter += 1
            image = _load_image(folder, image_nr)   # one folder each time 
            ### For IO device error to the image to be loaded  2022.05.23
            if image is None:
                continue
            control_dict['finished'] = False
            control_dict['skip'] = False
            control_dict['x1'] = None
            control_dict['x2'] = None
            control_dict['height'] = None
            control_dict['width'] = None
            control_dict['folder'] = folder
            control_dict['image'] = image_nr

            t = datetime.now()
            sec_per_img = (t - starting).seconds / image_counter
            remaining = ((num_labels - index) * sec_per_img) / 3600

            while not control_dict['finished']:   # keep running before 'finished'
                plt.close()
                fig = plt.figure()
                plt.title(
                    '{}/{}/{} - img/pers={}, remaining={}h, r=skip, e=exit, t=save&next, f=reset last'.format(
                        index, num_labels,
                        round((index / num_labels) * 100, 2),
                        round(sec_per_img, 2),
                        round(remaining, 2)
                    ))
                height, width, channels = image.shape   # "image" is used here
                control_dict['height'] = height
                control_dict['width'] = width
                plt.imshow(image, interpolation='none')

                if control_dict['x1'] is not None:
                    plt.axvline(control_dict['x1'])
                if control_dict['x2'] is not None:
                    plt.axvline(control_dict['x2'])

                def onKey(event):
                    global labels
                    if event.key == 'e':
                        plt.close()
                        print('Exiting..')
                        save_dict(labels)   # save until exiting!!!
                        sys.exit(0)
                    elif event.key == 'r':
                        plt.close()
                        control_dict['finished'] = True
                        control_dict['skip'] = True
                        control_dict['x1'] = None
                        control_dict['x2'] = None
                        labels = update_labels(labels, control_dict)
                    elif event.key == 't':
                        if (control_dict['x1'] is None) or (
                                control_dict['x2'] is None):
                            pass
                        else:
                            plt.close()
                            labels = update_labels(labels, control_dict)
                            control_dict['finished'] = True
                            control_dict['x1'] = None
                            control_dict['x2'] = None
                    elif event.key == 'f':   # always change the x2, not the latest double clicked => I should choose x1 first
                        plt.close()
                        if control_dict['x2'] is not None:
                            control_dict['x2'] = None
                        elif control_dict['x1'] is not None:
                            control_dict['x1'] = None

                def onClick(event):
                    if event.dblclick:
                        if control_dict['x1'] is None:
                            control_dict['x1'] = int(event.xdata)
                        else:
                            tmp = control_dict['x1']
                            tmp2 = int(event.xdata)
                            if tmp > tmp2:   # make sure x1 is in the left: but the third double click always compared with x1(x2 is ignored)
                                control_dict['x1'] = tmp2
                                control_dict['x2'] = tmp
                            else:
                                control_dict['x1'] = tmp
                                control_dict['x2'] = tmp2
                        plt.close()

                fig.canvas.mpl_connect('button_press_event', onClick)
                fig.canvas.mpl_connect('key_press_event', onKey)
                fig.canvas.mpl_connect('key_event', onKey)
                plt.grid()
                wm = plt.get_current_fig_manager()
                wm.window.showMaximized()
                plt.show()


if __name__ == '__main__':
    label_borders()
