import requests
import sys
import time
import boto3
import meraki
import credentials
import io
import shutil
import os
from PIL import Image

api_key = credentials.api_key
base_url = credentials.base_url
org_id = credentials.organization_id
networks = credentials.networks
cams = credentials.cams
args = sys.argv
# Instantiate AWS Python SDK Clients
# Must configure AWS CLI for this to work
# See https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html
s3 = boto3.resource('s3')

# Record timestamp for snapshot name
timestr = time.strftime("%Y%m%d-%H%M%S")

if len(args)>1:
	if args[1]=='-mv':

		# Instantiate Meraki Python SDK Client
		dashboard = meraki.DashboardAPI(
				api_key=api_key,
				base_url=base_url,
				log_file_prefix='./logs/import/',
				print_console=False)

		i = 0
		input('Please look at the camera. Press Enter when ready.')
		while i != 1:
			print('Taking snapshot...')
			snapshot = dashboard.camera.generateDeviceCameraSnapshot(serial = cams[0])
			# Wait 10 seconds for response to avoid not getting the snapshot in
			# time for storing
			time.sleep(10)

			# Store snapshot
			resp = requests.get(snapshot['url'], stream=True)
			filename = './imports/{}.jpg'.format(timestr)
			local_file = open(filename, 'wb')
			resp.raw.decode_content = True
			shutil.copyfileobj(resp.raw, local_file)
			local_file.close()

			# Open stored snapshot and send to Rekognition
			print('Storing snapshot copy locally...')
			image = Image.open(filename)
			stream = io.BytesIO()
			image.save(stream,format="JPEG")

			image.show()
			txt = ''
			while txt != 'y' or 'n':
				txt = input('Keep snapshot? (y/n): ')
				if txt == 'y':
					i = 1
					name = input('What is the name of this person?: ')
					break
				elif txt == 'n':
					print('Retaking snapshot...')
					os.remove(filename)
					break
				else:
					continue

			images=[(filename,name)]
	elif args[1]=='-f':
		if len(args) < 4:
			print('When running with -f keyword, you must add the path to the image' +
				  ' folder and the labels like python -f c:\images Francisco')
		else:
			path = args[2]
			label = args[3]
			images = []
			for r, d, f in os.walk(path):
				for file in f:
					if '.jpg' or '.png' or '.jpeg' in file:
						images.append((os.path.join(r,file),label))

for image in images:
	print('Uploading snapshot to S3...')
	file = open(image[0],'rb')
	s3name = image[0].replace('./imports/','')
	object = s3.Object('faces-francisco-tello','index/'+ image[1] + '-' +s3name)
	ret = object.put(Body=file,
					Metadata={'FullName':image[1]}
					)
	print('Snapshot of {} uploaded successfully to S3!'.format(image[1]))
