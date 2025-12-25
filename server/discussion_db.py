from pymongo import MongoClient, ASCENDING, DESCENDING
from bson.objectid import ObjectId
from datetime import datetime
import sys
import os

# Add project root to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import MONGODB_URI, DATABASE_NAME


class DiscussionDB:
	"""Small helper to manage discussion messages collection."""
	def __init__(self, uri: str = None):
		uri = uri or MONGODB_URI
		self.client = MongoClient(uri)
		self.db = self.client[DATABASE_NAME]
		self.messages = self.db['messages']
		# Index to speed up queries by class and time
		try:
			self.messages.create_index([('class_id', ASCENDING), ('created_at', DESCENDING)])
		except Exception:
			# index creation is best-effort (already present is fine)
			pass

	def send_message(self, content: str, attachment, class_id: str, sent_by: str, timestamp=None, reply=None):
		"""Insert a message into `messages` collection and return the created document.

		Fields: msg_id (str), content (text), attachment (None or dict), class_id, sent_by, created_at (utc), reply
		"""
		if timestamp is None:
			timestamp = datetime.utcnow()

		doc = {
			'content': content,
			'attachment': attachment,
			'class_id': class_id,
			'sent_by': sent_by,
			'created_at': timestamp,
			'reply': reply,
		}
		res = self.messages.insert_one(doc)
		doc['_id'] = res.inserted_id
		doc['msg_id'] = str(res.inserted_id)
		return doc

	def fetch_messages(self, class_id: str, limit: int = 100):
		"""Fetch recent messages for a class (most recent first)."""
		query = {'class_id': class_id}
		cursor = self.messages.find(query).sort('created_at', DESCENDING).limit(limit)
		out = []
		for d in cursor:
			d['msg_id'] = str(d.get('_id'))
			# convert datetime to isoformat for safe JSON transfer
			if isinstance(d.get('created_at'), datetime):
				d['created_at'] = d['created_at'].isoformat()
			out.append(d)
		return out

