import os
import time
import sys
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from slackclient import SlackClient


# starterbot's ID as an environment variable
BOT_NAME = 'chloe'
SLACK_BOT_TOKEN = 'xoxb-178360606005-xcNQP0n1GNNS8OQtQ7v8lZle'
BOT_ID = "U58ALHU05"
# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "do"
GREETINGS = ['hi ', 'hi!', 'hi', 'hello ', 'hello!', 'hey ', 'hey!', 'heya ', 'heya!']


# instantiate Slack & Twilio clients
slack_client = SlackClient(SLACK_BOT_TOKEN)

#intialize sentiment analysis object
vader = SentimentIntensityAnalyzer(lexicon_file='vaderSentiment/vader_lexicon.txt')

def sentiment_assess(command):
	return vader.polarity_scores(command) 

def handle_command(command, channel):
	"""
		Receives commands directed at the bot and determines if they
		are valid commands. If so, then acts on the commands. If not,
		returns back what it needs for clarification.
	"""
	sentiment = sentiment_assess(command)
	
	response = "I'm gauging your mood as " + str(sentiment['compound']) +". "
	mood = "undefined"
	if sentiment['compound'] < .2:
		mood = "confused"
	elif sentiment['neg'] > sentiment['neu'] and sentiment['neg'] > sentiment['pos']:
		mood = "bad"
	elif sentiment['neu'] > sentiment['neg'] and sentiment['neu'] > sentiment['pos']:
		mood = "ok"
	else:
		mood = "good"
	response = response + "You seem like you're in a(n) " + mood +" mood. "
	response = response +"Don't take me too seriously though. Have a hug: :hugging_face:"
	if command.startswith(EXAMPLE_COMMAND):
		response = "I can't really do anything right now... I'm just sprouting! :seedling:"
	else:
		for greet in GREETINGS:
			if command.startswith(greet):
				response = "Hi! I'm happy to hear from you. :blush:"
    
	slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
	"""
		The Slack Real Time Messaging API is an events firehose.
		this parsing function returns None unless a message is
		directed at the Bot, based on its ID.
	"""
	output_list = slack_rtm_output
	if output_list and len(output_list) > 0:
		for output in output_list:
			if output and 'text' in output and AT_BOT in output['text']:
				#return text after the @ mention, whitespace removed
				return output['text'].split(AT_BOT)[1].strip().lower()+" ", output['channel']
	return None, None


if __name__ == "__main__":
	READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
	if slack_client.rtm_connect():

		api_call = slack_client.api_call("users.list")
		
		"""
		#Code for finding out chloe's user id
		if api_call.get('ok'):
			# retrieve all users so we can find our bot
			users = api_call.get('members')
			for user in users:
				if 'name' in user and user.get('name') == BOT_NAME:
					print("Bot ID for '" + user['name'] + "' is " + user.get('id'))
		"""
	
		slack_client.api_call("chat.postMessage", channel="#chloe_dev", text="I've been woken up. Good morning!", as_user=True)
		print("Chloe-Bot connected and running!")
		while True:
			try:
				command, channel = parse_slack_output(slack_client.rtm_read())
				if command and channel:
					#this line echoes commands for debugging.
					#slack_client.api_call("chat.postMessage", channel="#chloe_dev", text="Echoing: " + command, as_user=True)
					handle_command(command, channel)
				time.sleep(READ_WEBSOCKET_DELAY)
			except KeyboardInterrupt:
				slack_client.api_call("chat.postMessage", channel="#chloe_dev", text="I've been told to go to bed now. Goodnight!", as_user=True)
				print("I've been told to go to bed now. Goodnight!")
				sys.exit()
	else:
		print("Connection failed. Invalid Slack token or bot ID?")