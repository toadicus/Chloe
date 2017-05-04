
import os
import time
import sys
import string
import pickle

import httplib2
import os
import random
import datetime
import nltk 
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize.api import StringTokenizer
from slackclient import SlackClient
from googleapi import upcoming
from gensim import models
from gensim import utils
from collections import namedtuple
from nltk.tokenize import RegexpTokenizer

# starterbot's ID as an environment variable
"""
#Code for finding out chloe's user id
api_call = slack_client.api_call("users.list")
if api_call.get('ok'):
	# retrieve all users so we can find our bot
	users = api_call.get('members')
	for user in users:
		if 'name' in user and user.get('name') == BOT_NAME:
			print("Bot ID for '" + user['name'] + "' is " + user.get('id'))
"""
BOT_NAME = 'chloe'
SLACK_BOT_TOKEN = 'ASK FOR TOKEN ON SLACK'
BOT_ID = "U58ALHU05"
# constants
AT_BOT = "<@" + BOT_ID + ">"
GREETINGS = ['hi', 'hi!', 'hi', 'hello', 'hello!', 'hey', 'hey!', 'heya', 'heya!']

#google api settings
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'

# instantiate Slack & Twilio clients
slack_client = SlackClient(SLACK_BOT_TOKEN)

#intialize sentiment analysis object
vader = SentimentIntensityAnalyzer(lexicon_file='vaderSentiment/vader_lexicon.txt')

nltk.download('punkt')

#long term and short term memory globals
STM_V = None
STM = None
LTM_V = None
LTM = None

#local path
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
CORPUS_SEG = namedtuple('SentimentDocument', 'words, tags')

def SentsFromFile(filename, topics = ["knowledge"]):
	sents = []
	data = open(filename, encoding = 'utf-8')
	translate_table = dict((ord(char), None) for char in string.punctuation)

	f =  open("working_memory.pickle", "a+" )

	for line_no, line in enumerate(data):
		tokens = line.lower().translate(translate_table).split()
		if len(tokens) < 2:
			continue
		words = tokens[1:]
		sents.append(CORPUS_SEG(words, topics))
		f.writelines(str(topics) + " " + line.lower().translate(translate_table))
	f.close()
	return sents

def recallWorkingMemory():
	sents = []
	data = open(filename, encoding = 'utf-8')
	for line_no, line in enumerate(data):
		tokens = line.lower().translate(translate_table).split()
		if len(tokens) < 2:
			continue
		words = tokens[1:]
		sents.append(CORPUS_SEG(words, topics))
		f.writelines(str(topics) + " " + line.lower().translate(translate_table))

#catch @chloe directed comments and standardize text
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

def sentiment_assess(command):
	sentiment = vader.polarity_scores(command) 
	
	response = "I'm gauging your mood as " + str(sentiment['compound']) +". "
	mood = "undefined"
	if sentiment['neg'] < .2 and sentiment['neu'] < .2 and sentiment['pos'] < .2:
		mood = "confused"
	elif sentiment['neg'] > sentiment['neu'] and sentiment['neg'] > sentiment['pos']:
		mood = "bad"
	elif sentiment['neu'] > sentiment['neg'] and sentiment['neu'] > sentiment['pos']:
		mood = "ok"
	else:
		mood = "good"
	response = response + "You seem like you're in a(n) " + mood +" mood. "
	response = response + "Don't take me too seriously though. Have a hug: :hugging_face:"
	return response

def handle_command(command, channel):
	"""
		Receives commands directed at the bot and determines if they
		are valid commands. If so, then acts on the commands. If not,
		returns back what it needs for clarification.
	"""
	global STM
	global LTM
	
	#command switch board
	r = random.random()
	tokens = command.split()
	response = None
#HELP COMMAND LIST
	if command.startswith("help"):
		response = "I'm a little cyber sprout! :seedling: You can direct "\
			+"messages to me using @chloe plus a message and then I'll do my best to give you my thoughts. Also you can use any of these words for specific actions: "\
			+"calendar, hi, pay attention, ignore, recall, short term memory, long term memory, read book ___.txt, forget, forget everything, contemplate, speculate on."	
#TERMINATION / SUICIDE
	elif command.startswith("commit suicide"):
		print("recieved command from slack channel to commit suicide")
		if r < .25:
			slack_client.api_call("chat.postMessage", channel=channel, text="I-I-i'm so sorry. :weary: :gun:", as_user=True)
		elif r < .5:
			slack_client.api_call("chat.postMessage", channel=channel, text="O-ok. :pensive: :gun:", as_user=True)
		elif r < .75:
			slack_client.api_call("chat.postMessage", channel=channel, text="B-but sempai I'm scared. :fearful: :gun:", as_user=True)
		else:
			slack_client.api_call("chat.postMessage", channel=channel, text=":cold_sweat: :gun:", as_user=True)
		sys.exit()
#CALENDAR INTEGRATION
	elif "calendar" in tokens:
		response = upcoming()
#READ AND LEARN FROM FILES
	elif command.startswith("read book"):
		slack_client.api_call("chat.postMessage", channel=channel, text=":nerd_face: oh boy books, my fav! This will just be a moment...", as_user=True)
		t = time.clock()
		
		if tokens[2] == "bible.txt":
			topic_list = ["bible", "scripture"]
		elif tokens[2] == "dictionary.txt":
			topic_list = ["definitions"]
		else:
			topic_list = ["knowledge"]
		
		sentences = SentsFromFile(filename = DIR_PATH+"\\Books\\"+tokens[2], topics = topic_list)
		STM = models.Doc2Vec(size=490, window = 21, alpha=0.025, min_alpha=0.01 , hs = 0) 
		STM.build_vocab(sentences, update=False)
		STM.train(sentences)
		t = str(round(time.clock() - t,1))
		STM.save(DIR_PATH+"\\STM.doc2vec")
		response ="All done with book "+tokens[2]+" and it only took " + t +" seconds. :smile:"
		
		#slack_client.api_call("chat.postMessage", channel=channel, text="Oops something went wrong. " + str(sys.exc_info()[0]) + " Line: " + str(sys.exc_info()[2].tb_lineno), as_user=True)
#GREETINGS
	elif tokens[0] in GREETINGS:
		response = "Hi! I'm happy to hear from you. :blush:"
#TOGGLE STREAM CAPTURE TO SHORT TERM MEMORY
	elif command.startswith("pay attention"):
		response = "I'm happy to learn something new! :nerd_face:"
	elif command.startswith("ignore"):
		response = "Okey dokey. I was bored anyway. :sleeping: "
#LOAD MEMORY
	elif command.startswith("recall everything") or command.startswith("recollect everything") or command.startswith("remember everything"):
		LTM =  models.Doc2Vec.load(DIR_PATH+"\\LTM.doc2vec")
		STM = models.Doc2Vec.load(DIR_PATH+"\\STM.doc2vec")
		response = "Got it. :thinking_face:"

	elif command.startswith("recall") or command.startswith("recollect") or command.startswith("remember"):
		STM = models.Doc2Vec.load(DIR_PATH+"\\STM.doc2vec")
		response = "Got it. :thinking_face:"
		
#QUERY SIZE OF MEMORY
	elif command.startswith("short term memory"):
		if STM is None:
			response = "I havn't really been paying attention. :sweat_smile:"
		else:
			vocab = str(len(STM.docvecs))
			mem = str(sys.getsizeof(STM))
			response = ":thinking_face: "+vocab+" vocab words and "+mem+" MBs"
	elif command.startswith("long term memory"):
		if LTM is None:
			response = "I don't know nuffin. :disappointed:"
		else:
			vocab = str(len(LTM.docvecs))
			mem = str(sys.getsizeof(LTM))
			response = ":thinking_face: "+vocab+" vocab words and "+mem+" MBs"
#DUMP MEMORY
	elif command.startswith("forget everything"):
		STM = None
		LTM = None
		f = open(DIR_PATH+"working_memory.txt", "rw+")
		f.truncate()
		f.close()
		response = ":relieved: Thank goodness. That was getting to be a lot to keep in mind."
	elif command.startswith("forget"):
		STM = None
		f = open(DIR_PATH+"working_memory.txt", "rw+")
		f.truncate()
		f.close()
		response = "Forget what? :wink:"
#INTEGRATE SHORT TERM AND LONG TERM MEMORY
	elif command.startswith("contemplate") or command.startswith("ponder"):
		if r < .5:
			response = "Let me think about this for a bit. :thinking_face:"
		else:
			response = "Will do! :upside_down_face:"
		if STM is None:
			response = "I havn't learned anything recently to think about. :cry:"
		else:
			corpus =  nltk.corpus.reader.plaintext.PlaintextCorpusReader(DIR_PATH, "working_memory.txt")
			sentences = SentsFromFile(filename = DIR_PATH+"working_memory.txt", topics = ["knowledge"])
			LTM = models.Doc2Vec.load(DIR_PATH+"\\LTM.doc2vec")
			LTM.build_vocab(sentences, keep_raw_vocab = True, update=True)
			LTM.train(sentences)
			LTM.save(DIR_PATH+"\\LTM.doc2vec")
#USE SHORT TERM MEMORY TO DRAW SIMILARITIES
	elif command.startswith("speculate on"):
		if STM is not None:
			try:
				break_point = len(tokens)
				for i, token in enumerate(tokens):
					if token == "-" or token =="minus" or token =="subtract" or token =="less":
						break_point = i
						break
				if break_point < len(tokens):
					conclusions = STM.most_similar(positive=tokens[2:break_point], negative = tokens[break_point+1:])
				else:
					conclusions = STM.most_similar(tokens[2])
				response = "Well, based on what I've recently learned about the words " + str(tokens[2:break_point]) + " and " + str(tokens[break_point+1:]) + "... " + str(conclusions)
			except:
				response = "Something happened. I probably don't know some or all of the word(s) '" + str(tokens[2:]) +"'."
		else:
			response = "errrr... I dunno. :grimacing:"
	elif STM is not None:
		known_words = filter(lambda x: x in STM.wv.vocab, tokens)
		response = "That makes me think about " + str(STM.most_similar(known_words)[0])
	else:
		response = sentiment_assess(command)
    
	#write out response
	slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)


if __name__ == "__main__":
	READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
	if slack_client.rtm_connect():
	
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