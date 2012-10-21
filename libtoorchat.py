import os
import httplib
from threading import Thread

USER_NAME_SIZE = 9

def string_into_even_peices(string, size):
	peices = len(string)/size
	result = []
	if len(string) % size:
		peices +=1
	for index in range(peices):
		result.append(string[index*size:(index*size)+size])
	return result

def get_web_site(visual, site):
	''' This is a threaded message to query a website and create message to pass back '''
	try:
		connection = httplib.HTTPConnection(site)
		connection.request("GET", "/")
		result = connection.getresponse().read()
		result_list = string_into_even_peices(result, 100)
		site_xid = os.urandom(8)
		for index, item in enumerate(result_list):
			msg = ToorMessage(item, None, ToorChatProtocol.get_web_response_type(), site_xid, str(index), )
			# visual.message_queue.append(msg)
	except Exception as e:
		print e


class ToorChatProtocol():
	''' This is a class to allow for easy of use with anything to do with messaging '''
	def __init__(self, device):
		self.PACKET_START = "\xFF\xDE\xAD\xFF"
		self.PACKET_END = "\xFF\xBE\xEF\xFF"
		self.device = device

	def send_chat_message(self, message = "", user = None):
		''' This is used to send a simple message over the toorchat protocol '''
		msg = ToorMessage(message, user)
		self.device.RFxmit(msg.to_string())
		return msg

	def change_channel(self, channel):
		''' This is used to change the channel that the user operates in '''
		if isinstance(channel, int):
			self.device.setChannel(int(channel))


	def change_frequency(self, frequency):
		''' This is used to change the frequency that the user operates in '''
		if isinstance(frequency, int):
			self.device.setFreq(int(frequency))

	def send_web_request(self, site = ""):
		'''This is used to attempt to get anyone who is registered as a server to load a website on your behalf '''
		if site != "":
			request = ToorMessage(site, None, ToorChatProtocol.get_web_request_type())
			self.device.RFxmit(request.to_string())

	@classmethod
	def parse_message(cls, raw_message):
		message = ToorMessage()
		message.raw = raw_message
		start_index = raw_message.find(ToorChatProtocol.get_packet_start())
		end_index = raw_message.find(ToorChatProtocol.get_packet_end())
		if start_index == -1 or end_index == -1:
			return None
		message.start = raw_message[start_index:start_index + 4]
		message.xid = raw_message[start_index + 4: start_index + 12]
		message.type = raw_message[start_index + 12: start_index + 14]
		message.index = raw_message[start_index + 14: start_index + 16]
		message.last = raw_message[start_index + 16: start_index + 18]
		message.user = raw_message[start_index + 18: start_index + 26]
		message.data = raw_message[start_index + 26: end_index]
		message.end = raw_message[end_index: end_index+4]
		return message

	@classmethod
	def get_web_messages(cls, site, visual):
		'''This is query the webpage and make thoose messages '''
		thread = Thread(target=get_web_site, args=(visual, site))
		thread.start()

	@classmethod
	def get_packet_start(cls):
		return "\xFF\xDE\xAD\xFF"
	
	@classmethod
	def get_packet_end(cls):
		return "\xFF\xBE\xEF\xFF"

	@classmethod
	def get_chat_type(cls):
		return "01"

	@classmethod
	def get_web_request_type(cls):
		return "02"

	@classmethod
	def get_web_response_type(cls):
		return "03"

class ToorMessage():
	''' This is a simple Message object wrapper to make things cleaner '''

	''' This is confusing as shit so here is a diagram to attempt to help us all out '''
	''' ___________________________________________________________________________  '''
	'''| Start | XID | Type | Index | Last | User |          Data            | End |  '''
	'''|___4___|__8__|__2___|___2___|__2___|__8___|_________100-200__________|__4__|  '''

	''' The numbers represent the number of byte in a given message '''
	''' Note: The more data bytes we use, the harder it is to catch over the air '''


	def __init__(self, message = "", user = None, protocol_type=ToorChatProtocol.get_chat_type(), xid=None, index="00", last="00"):
		self.raw = None
		self.start = ToorChatProtocol.get_packet_start()
		if xid == None:
			self.xid = self.get_random_xid()
		else:
			self.xid = xid

		self.type = protocol_type
		self.index = index
		self.last = last
		if user != None:
			self.user = user
			if len(self.user) < USER_NAME_SIZE:
				self.user = self.user + " "* (USER_NAME_SIZE-len(self.user))
		else:
			self.user = "--NONE--"
		self.data = message
		self.end = ToorChatProtocol.get_packet_end()

	def get_random_xid(self):
		return os.urandom(8)

	def __str__(self):
		return self.start + self.xid + self.type + self.index + self.last + self.user + self.data + self.end

	def to_string(self):
		return self.__str__()
