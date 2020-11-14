# Based off of https://aws.amazon.com/blogs/machine-learning/build-your-own-face-recognition-service-using-amazon-rekognition/
# Using Meraki Python SDK at https://github.com/meraki/dashboard-api-python

import requests
import time
import shutil
import credentials
import meraki

def draw_bounding_box(image, box):

	img_width, img_height = image.size

	left = img_width * box['Left']
	top = img_height * box['Top']
	width = img_width * box['Width']
	height = img_height * box['Height']

	points = (
		(left, top),
		(left + width, top),
		(left + width, top + height),
		(left , top + height),
		(left, top)
	)

	return points, left, top

def snap(dashboard_api_client, time_string,	networkIds,	organizationId,
			cameras, base_url, folder):
	print('Taking snapshot...')
	snapshot = dashboard_api_client.camera.generateDeviceCameraSnapshot(
		serial = cameras[0])
	# Wait 10 seconds for response
	time.sleep(5)
	# Store snapshot
	print('Storing snapshot locally...')
	resp = requests.get(snapshot['url'], stream=True)
	filename = './{}/{}.jpg'.format(folder, time_string)
	local_file = open(filename, 'wb')
	resp.raw.decode_content = True
	shutil.copyfileobj(resp.raw, local_file)
	local_file.close()

	return filename

if __name__ == "__main__":
	api_key = credentials.api_key
	baseurl = credentials.base_url
	org_id = credentials.organization_id
	networks = credentials.networks
	cams = credentials.cams

	# Instantiate Meraki Python SDK Client
	dashboard = meraki.DashboardAPI(
			api_key=api_key,
			base_url=baseurl,
			log_file_prefix='./logs/snaps',
			print_console=False)

	# Record timestamp for snapshot name
	timestr = time.strftime("%Y%m%d-%H%M%S")

	file_name = snap(
			dashboard_api_client=dashboard,
			time_string=timestr,
			networkIds=networks,
			organizationId=org_id,
			cameras=cams,
			base_url=baseurl,
			folder='snaps')
