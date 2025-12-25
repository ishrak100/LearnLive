import sys
import os
from typing import Optional
import json

# allow importing project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server.discussion_db import DiscussionDB

RESP_SUCCESS = 'SUCCESS'
RESP_ERROR = 'ERROR'

# Optional notifier instance (set by NotificationHandler.register_client)
_notifier = None

def set_notifier(notifier):
	"""Set a NotificationHandler-like object so we can broadcast messages.

	The notifier must expose `online_clients` mapping of user_id -> (socket, user_data).
	"""
	global _notifier
	_notifier = notifier


class DiscussionHandler:
	"""Handlers for discussion-related requests.

	These accept and return plain dicts so the server can call them directly.
	"""

	def __init__(self, db: DiscussionDB= None):
		# Always use the dedicated DiscussionDB implementation for discussion
		# operations to ensure `send_message` and `fetch_messages` exist.
		# Ignore any generic Database passed in.
		self.db = DiscussionDB()

	def send_message_handler(self, data: dict) -> dict:
		"""Handle send-message request and persist it to the messages collection.

		Expected `data` keys:
		- content: optional text content
		- attachment: optional dict with attachment info (name/path)
		- class_id: required class identifier
		- sent_by: required sender identifier (email or user id)
		- timestamp: optional (ignored if not provided)
		- reply: optional message id being replied to
		"""
		try:
			content = data.get('content')
			attachment = data.get('attachment')
			class_id = data.get('class_id')
			sent_by = data.get('sent_by')
			timestamp = data.get('timestamp')
			reply = data.get('reply')

			if not class_id or not sent_by:
				return {'type': RESP_ERROR, 'error': 'class_id and sent_by required'}

			doc = self.db.send_message(content, attachment, class_id, sent_by, timestamp, reply)

			# Make a JSON-serializable copy of the document for response/broadcast
			safe_doc = dict(doc)
			if '_id' in safe_doc:
				try:
					safe_doc['_id'] = str(safe_doc['_id'])
				except Exception:
					pass
			created = safe_doc.get('created_at')
			if hasattr(created, 'isoformat'):
				safe_doc['created_at'] = created.isoformat()
			# Ensure msg_id present
			if 'msg_id' not in safe_doc:
				safe_doc['msg_id'] = str(safe_doc.get('_id', ''))

			# Broadcast to connected clients (best-effort).
			try:
				if _notifier is not None:
					payload = {'type': 'MESSAGE', 'message': safe_doc}
					data_bytes = json.dumps(payload).encode()
					length_prefix = len(data_bytes).to_bytes(4, byteorder='big')
					# Send to all online sockets
					for user_id, (sock, user_data) in list(_notifier.online_clients.items()):
						try:
							sock.sendall(length_prefix + data_bytes)
						except Exception:
							# If sending fails, unregister that client from notifier
							try:
								_notifier.unregister_client(user_id)
							except Exception:
								pass
			except Exception:
				# broadcasting should not break the handler
				pass

			return {'type': RESP_SUCCESS, 'message': safe_doc}

		except Exception as e:
			return {'type': RESP_ERROR, 'error': str(e)}

	def fetch_messages_handler(self, data: dict) -> dict:
		"""Handle fetch-messages request.

		Expected `data` keys:
		- class_id: required
		- limit: optional int
		"""
		try:
			class_id = data.get('class_id')
			limit = int(data.get('limit', 100))

			if not class_id:
				return {'type': RESP_ERROR, 'error': 'class_id required'}

			msgs = self.db.fetch_messages(class_id, limit)
			return {'type': RESP_SUCCESS, 'messages': msgs}

		except Exception as e:
			return {'type': RESP_ERROR, 'error': str(e)}

