# Based off of https://aws.amazon.com/blogs/machine-learning/build-your-own-face-recognition-service-using-amazon-rekognition/
# Using Meraki Python SDK at https://github.com/meraki/dashboard-api-python

import time
import boto3
import io
import credentials
import meraki
import snapshot
from PIL import Image, ImageDraw, ImageFont
from webexteamssdk import WebexTeamsAPI


def face_rec(rekognition_api_client, dynamodb_api_client, filename, badge_name=None):
	# Open stored image and send to Rekognition
	image = Image.open(filename)
	stream = io.BytesIO()
	image.save(stream,format="JPEG")
	image_binary = stream.getvalue()
	draw = ImageDraw.Draw(image)

	print('Detecting faces...')

	response = rekognition_api_client.search_faces_by_image(
			CollectionId='faces',
			Image={'Bytes':image_binary}
			)

	# Initialize averages
	confidence_avg = 0
	similarity_avg = 0
	name =""
	if response['FaceMatches'] == []:
		print("Face did not match anything in the database.")
	else:
		for match in response['FaceMatches']:
			confidence_avg = confidence_avg + match['Face']['Confidence']
			similarity_avg = similarity_avg + match['Similarity']

			face = dynamodb_api_client.get_item(
				TableName='faces',
				Key={'RekognitionId': {'S': match['Face']['FaceId']}}
				)
			if len(face)==2:
				name = face['Item']['FullName']['S']
		if not name:
			name = ""
		box = response['SearchedFaceBoundingBox']

		points, left, top = snapshot.draw_bounding_box(image, box)
		imgfont = ImageFont.truetype(font='Arial Unicode.ttf', size=20)
		if badge_name==None or (badge_name==name):
			draw.line(points, fill='#00d400', width=5)
			draw.text(xy=(left,top), text=name, fill='#00d400', font=imgfont)
		else:
			draw.line(points, fill='#ff0000', width=5)
			draw.text(xy=(left,top), text=name, fill='#ff0000', font=imgfont)

		confidence_avg = confidence_avg/len(response['FaceMatches'])
		similarity_avg = similarity_avg/len(response['FaceMatches'])

		print('This image is of {} with {} percent confidence and {} percent similarity.'.format(name,confidence_avg,similarity_avg))
		image.save(filename, "JPEG")
		image.show()
	if name=="":
		name = 'Unknown person'
		box = response['SearchedFaceBoundingBox']

		points, left, top = snapshot.draw_bounding_box(image, box)
		imgfont = ImageFont.truetype(font='arial.ttf', size=20)
		draw.line(points, fill='#ff0000', width=5)
		draw.text(xy=(left, top), text=name, fill='#ff0000', font=imgfont)
		image.save(filename, "JPEG")
		image.show()
	return name, filename

if __name__ == "__main__":
	# Importing variables
	api_key = credentials.api_key
	baseurl = credentials.base_url
	org_id = credentials.organization_id
	networks = credentials.networks
	cams = credentials.cams
	webex_email = credentials.webex_email
	webex_token = credentials.webex_token

	# Instantiate Meraki Python SDK Client
	dashboard = meraki.DashboardAPI(
			api_key=api_key,
			base_url=baseurl,
			log_file_prefix='./logs/facerec/',
			print_console=False)
	# Instantiate AWS Python SDK Clients
	# Must configure AWS CLI for this to work
	# See https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html
	rekognition = boto3.client('rekognition', region_name='us-east-2')
	dynamodb = boto3.client('dynamodb', region_name='us-east-2')
	webex = WebexTeamsAPI(access_token=webex_token)

	# Record timestamp for snapshot name
	timestr = time.strftime("%Y%m%d-%H%M%S")

	file_name = snapshot.snap(
			dashboard_api_client=dashboard,
			time_string=timestr,
			networkIds=networks,
			organizationId=org_id,
			cameras=cams,
			base_url=baseurl,
			folder='faces')

	name, filename = face_rec(
			rekognition_api_client=rekognition,
			dynamodb_api_client=dynamodb,
			filename = file_name)

	text = f'{name} was detected!'
	webex.messages.create(toPersonEmail=webex_email, text=text, files=[filename])
