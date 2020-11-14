import facerec
import access_control
import credentials
import meraki
import snapshot
import boto3
import time
from termcolor import cprint
from webexteamssdk import WebexTeamsAPI

api_key = credentials.api_key
baseurl = credentials.base_url
org_id = credentials.organization_id
networks = credentials.networks
cams = credentials.cams
webex_email = credentials.webex_email
webex_token = credentials.webex_token

dashboard = meraki.DashboardAPI(
        api_key=api_key,
        base_url=baseurl,
		log_file_prefix='./logs/2faccess/',
        print_console=False)

# Instantiate AWS Python SDK Clients
# Must configure AWS CLI for this to work
# See https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html
rekognition = boto3.client('rekognition', region_name='us-east-2')
dynamodb = boto3.client('dynamodb', region_name='us-east-2')
webex = WebexTeamsAPI(access_token=webex_token)

# Record timestamp for snapshot name
timestr = time.strftime("%Y%m%d-%H%M%S")

time_stamp, access_code, badge_name = access_control.badge_reader()

r = dashboard.camera.getDeviceCameraVideoLink(serial=cams[0])

link = r['url']

file_name = snapshot.snap(
		dashboard_api_client=dashboard,
		time_string=timestr,
		networkIds=networks,
		organizationId=org_id,
		cameras=cams,
		base_url=baseurl,
		folder='access')

face_name, filename = facerec.face_rec(
		rekognition_api_client=rekognition,
		dynamodb_api_client=dynamodb,
		filename = file_name,
        badge_name = badge_name)

if face_name == badge_name:
	cprint("{} has successfully badged in.".format(face_name), "green")
	body = f"{face_name} has successfully badged in."
	webex.messages.create(toPersonEmail=webex_email, text=body, files=[filename])
else:
	filename = file_name
	subject = "ALERT - UNAUTHORIZED ACCESS"
	body = "ALERT: {} has used {}'s badge without authorization. ".format(face_name, badge_name)
	body = body + "\n\nAccess the video feed by following this link: {}".format(link)
	cprint("ALERT: {} has used {}'s badge without authorization.".format(face_name, badge_name), "red")
	print("Access the video feed by following this link: {}".format(link))
	webex.messages.create(toPersonEmail=webex_email, text=body, files=[filename])
