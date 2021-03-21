import cv2
import argparse
import yaml
import os
import numpy as np

def getFiles(path):
	image_list=[]
	for file in os.listdir(path):
		if file.endswith(".jpg") or file.endswith(".png"):
			image_list.append(os.path.join(path, file))
	return image_list

count = 0
refPt = []
bbPt = [(0,0),(0,0)]

def click_keypoint(event, x, y, flags, param):
	global refPt
	global bbPt
	global count
	global kp_names
	# if the left mouse button was clicked, record the starting
	# (x, y) coordinates
	if event == cv2.EVENT_LBUTTONDOWN:
		refPt.append({"id":count, "image_coords":{"u":x, "v":y}, "visible":1, "name":kp_names[count]})
		count += 1
		# draw a circle at clicked point (cycle colours)
		color_list = [(0,255,0), (0,0,255), (255,0,0), (0,255,255)]
		col = len(refPt) % 4
		cv2.circle(image, (x,y), 3, color_list[col], -1)
		cv2.imshow("image", image)
	if event == cv2.EVENT_RBUTTONDOWN:
		bbPt = [(x,y)]
	elif event == cv2.EVENT_RBUTTONUP:
		bbPt.append((x,y))
		cv2.rectangle(image,bbPt[0],bbPt[1],(0,255,0),2) # draw bounding box
		cv2.imshow("image", image)


parser = argparse.ArgumentParser(description='Label keypoints on images.')
parser.add_argument("-i", "--image_file", required=True,
                    help='path to folder contaning images')
args = parser.parse_args()

n_kps = 0
while True:
	n_kps = int(raw_input('How many keypoints are in each image? '))
	if n_kps < 1:
		print("requires an integer value > 1")
	else:
		break

kp_names = []
for n in range(n_kps):
	name = raw_input('Type name for keypoint {}: '.format(n+1))
	kp_names.append(name)

# extract list of images from folder
image_list = getFiles(args.image_file)
print(image_list)

keypoints = {"image_data": []}

print("INSTRUCTIONS\npress r to reset image,\npress c to capture keypoints and move to next image,\npress f to record non-visible key point")
print("click and drag right mouse button to draw bounding box for object")
print("select keypoints in order: {}".format(kp_names))

counter = 0
cont = True
while cont: 
	image_name = image_list[counter]
	refPt = [] # reset list for this image
	count = 0
	image = cv2.imread(image_name)
	clone = image.copy()
	cv2.namedWindow("image")
	cv2.setMouseCallback("image", click_keypoint)
	# keep looping until the 'q' key is pressed
	while True:
		# display the image and wait for a keypress
		cv2.imshow("image", image)
		key = cv2.waitKey(1) & 0xFF
		# if the 'r' key is pressed, reset the cropping region
		if key == ord("r"):
			image = clone.copy()
			refPt = []
			count = 0
		# if the 'c' key is pressed, break from the loop
		elif key == ord("c"):
			break
		# if 'f' key pressed record blank kepoint (not visible)
		elif key == ord("f"):
			refPt.append({"id":count, "image_coords":{"u":-1, "v":-1}, "visible":0, "name":kp_names[count]})
			count += 1
		if len(refPt) > n_kps:
			print("too many keypoints selected, please retry")
			image = clone.copy()
			refPt = []
			count = 0

	y_min, x_min = np.asarray(bbPt).min(axis=0)
	y_max, x_max = np.asarray(bbPt).max(axis=0)

	# add to dictionary
	zippered = {"image_id":image_name ,"keypoints":refPt,
	    "bounding_box":{ "x_max":int(x_max), "x_min":int(x_min), "y_max": int(y_max), "y_min":int(y_min)}}
	keypoints["image_data"].append(zippered)

	# close all open windows
	cv2.destroyAllWindows()
	print('saved keypoints for ...{}'.format(image_name[-14:]))
	print('{}/{}'.format(counter+1,len(image_list)))
	ok = raw_input("Continue? (y/n)")
	if ok == "n":
		cont = False

	counter += 1

	if counter == len(image_list):
		cont = False
		print('reached the end of the image set')

print('{} images labelled'.format(counter))


with open(args.image_file+'/keypoints.yaml', 'w+') as file:
    documents = yaml.dump(keypoints, file)

print("keypoint data saved to " + args.image_file +"/keypoints.yaml") 