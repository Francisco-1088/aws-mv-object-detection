# Based off of https://aws.amazon.com/blogs/machine-learning/build-your-own-face-recognition-service-using-amazon-rekognition/
# Using Meraki Python SDK at https://github.com/meraki/dashboard-api-python

import time
from datetime import date
import boto3
import io
import credentials
import meraki
import snapshot
import student_list
from PIL import Image, ImageDraw, ImageFont
from webexteamssdk import WebexTeamsAPI

def attendance(rekognition_api_client, dynamodb_api_client, filename):
	# Open stored image and send to Rekognition
	image = Image.open(filename)

	stream = io.BytesIO()
	image.save(stream,format="JPEG")
	image_binary = stream.getvalue()

	response = rekognition_api_client.detect_faces(
	    Image={'Bytes':image_binary}
	        )

	all_faces=response['FaceDetails']

	draw = ImageDraw.Draw(image)

	print('Avengers Assembling...')
	attendees = []
	for face in all_faces:
		box = face['BoundingBox']
		x1 = int(box['Left'] * image.size[0]) * 0.9
		y1 = int(box['Top'] * image.size[1]) * 0.9
		x2 = int(box['Left'] * image.size[0] + box['Width'] * image.size[0]) * 1.10
		y2 = int(box['Top'] * image.size[1] + box['Height']  * image.size[1]) * 1.10
		image_crop = image.crop((x1,y1,x2,y2))

		stream = io.BytesIO()
		image_crop.save(stream,format="JPEG")
		image_crop_binary = stream.getvalue()

		#print('Detecting faces...')
		#image_crop.show()
		try:
			response = rekognition_api_client.search_faces_by_image(
					CollectionId='faces',
					Image={'Bytes':image_crop_binary}
					)

			# Initialize averages
			confidence_avg = 0

			if response['FaceMatches'] == []:
				print ("Someone unknown Assembled.")
				name = 'Unknown Avenger'

				imgfont = ImageFont.truetype(font='Arial Unicode.ttf', size=20)
				points, left, top = snapshot.draw_bounding_box(image=image, box=box)
				draw.line(points, fill='#00d400', width=5)
				draw.text(xy=(left,top), text=name, fill='#00d400', font=imgfont)

			else:
				for match in response['FaceMatches']:
					confidence_avg = confidence_avg + match['Face']['Confidence']

					face = dynamodb_api_client.get_item(
						TableName='faces',
						Key={'RekognitionId': {'S': match['Face']['FaceId']}}
						)

					if len(face) == 2:
						name = face['Item']['FullName']['S']


					imgfont = ImageFont.truetype(font='Arial Unicode.ttf', size=20)
					points, left, top = snapshot.draw_bounding_box(image=image, box=box)
					draw.line(points, fill='#00d400', width=5)
					draw.text(xy=(left,top), text=name, fill='#00d400', font=imgfont)

				confidence_avg = confidence_avg/len(response['FaceMatches'])
				attendees += [str(name)]
				if name=='Thanos':
					print('Thanos is here.')
				else:
					print('{} Assembled with {} percent confidence.'.format(name,confidence_avg))
		except:
			print("Something went wrong!")

	print('There are {} total Avengers Assembled against Thanos.'.format(len(all_faces)-1))

	image.save(filename, "JPEG")
	image.show()

	return attendees, filename

if __name__ == "__main__":
	# Importing variables
	api_key = credentials.api_key
	baseurl = credentials.base_url
	org_id = credentials.organization_id
	networks = credentials.networks
	cams = credentials.cams
	students = student_list.student_list
	webex_email = credentials.webex_email
	webex_token = credentials.webex_token

	# Instantiate Meraki Python SDK Client
	dashboard = meraki.DashboardAPI(
			api_key=api_key,
			base_url=baseurl,
			log_file_prefix='./logs/attendance/',
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
			folder='attendance')

	attendees, filename = attendance(
			rekognition_api_client=rekognition,
			dynamodb_api_client=dynamodb,
			filename = file_name)

	x = set(attendees)
	y = set(students)

	z = y.difference(x)

	# Generate Attendance Report
	filename = file_name
	body = "These are the Avengers who Assembled on {}.".format(date.today().isoformat())
	body = body + "\n\nAssembled:\n{}".format(x)
	body = body + "\n\nDidn't Assemble:\n{}".format(z)

	print("Assembled: \n{}".format(x))
	print("Didn't Assemble: \n{}".format(z))

	webex.messages.create(toPersonEmail=webex_email, text=body, files=[filename])