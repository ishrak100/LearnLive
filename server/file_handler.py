# File Transfer Handler for LearnLive

import os
import json
import sys
import base64

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import *


class FileHandler:
    def __init__(self):
        """Initialize file handler"""
        # Create uploads directory if it doesn't exist
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        
        self.active_transfers = {}  # transfer_id -> file_info
        self.chunk_size = 8192  # 8KB chunks
        print("📁 File handler initialized")
    
    def handle_file_upload_start(self, data, client_socket):
        """Handle file upload initiation"""
        try:
            filename = data.get('filename')
            filesize = data.get('filesize')
            file_type = data.get('file_type')
            transfer_id = data.get('transfer_id')
            
            # Validate file size
            if filesize > MAX_FILE_SIZE:
                return {
                    'type': RESP_ERROR,
                    'success': False,
                    'error': f'File too large. Max size: {MAX_FILE_SIZE / (1024*1024)} MB'
                }
            
            # Validate file extension
            ext = filename.split('.')[-1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                return {
                    'type': RESP_ERROR,
                    'success': False,
                    'error': f'File type not allowed. Allowed: {ALLOWED_EXTENSIONS}'
                }
            
            # Generate unique filename
            import time
            unique_filename = f"{int(time.time())}_{filename}"
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            
            # Calculate total chunks
            total_chunks = (filesize + self.chunk_size - 1) // self.chunk_size
            
            # Store transfer info
            self.active_transfers[transfer_id] = {
                'filename': filename,
                'unique_filename': unique_filename,
                'filepath': file_path,
                'filesize': filesize,
                'file_type': file_type,
                'received': 0,
                'file_handle': open(file_path, 'wb'),
                'expected_chunk': 0,
                'total_chunks': total_chunks,
                'chunks_received': []
            }
            
            print(f"\n📤 ╔══════════════════════════════════════════╗")
            print(f"📤 ║   FILE UPLOAD STARTED                    ║")
            print(f"📤 ╚══════════════════════════════════════════╝")
            print(f"   Transfer ID: {transfer_id}")
            print(f"   Filename: {filename}")
            print(f"   Size: {filesize / 1024:.2f} KB")
            print(f"   Type: {file_type}")
            print(f"   Total Chunks Expected: {total_chunks}")
            print(f"   Chunk Size: {self.chunk_size} bytes")
            print(f"   Sequence Numbers: 0 to {total_chunks - 1}")
            
            # Send ready acknowledgment
            return {
                'type': RESP_SUCCESS,
                'success': True,
                'message': 'Ready to receive file',
                'transfer_id': transfer_id,
                'chunk_size': self.chunk_size,
                'total_chunks': total_chunks
            }
            
        except Exception as e:
            return {
                'type': RESP_ERROR,
                'success': False,
                'error': str(e)
            }
    
    def handle_file_chunk(self, data):
        """Handle incoming file chunk with metadata"""
        try:
            transfer_id = data.get('transfer_id')
            chunk_number = data.get('chunk_number')
            chunk_size = data.get('chunk_size')
            filename = data.get('filename')
            file_type = data.get('file_type')
            chunk_data_b64 = data.get('chunk_data')
            
            if transfer_id not in self.active_transfers:
                print(f"   ❌ Invalid transfer ID: {transfer_id}")
                return {
                    'type': RESP_ERROR,
                    'success': False,
                    'error': 'Invalid transfer ID',
                    'chunk_number': chunk_number
                }
            
            transfer_info = self.active_transfers[transfer_id]
            
            # Decode chunk data
            chunk_data = base64.b64decode(chunk_data_b64)
            
            # Verify chunk size
            if len(chunk_data) != chunk_size:
                print(f"   ⚠️  Chunk size mismatch: expected {chunk_size}, got {len(chunk_data)}")
            
            # Write chunk
            file_handle = transfer_info['file_handle']
            file_handle.write(chunk_data)
            transfer_info['received'] += len(chunk_data)
            transfer_info['chunks_received'].append(chunk_number)
            
            progress = (transfer_info['received'] / transfer_info['filesize']) * 100
            
            print(f"   📦 ═══════════════════════════════════════════")
            print(f"   📥 RECEIVED CHUNK: SEQ #{chunk_number}")
            print(f"   📦 ═══════════════════════════════════════════")
            print(f"      Filename: {filename}")
            print(f"      File Type: {file_type}")
            print(f"      Chunk Size: {chunk_size} bytes")
            print(f"      Received: {len(chunk_data)} bytes")
            print(f"      Progress: {progress:.1f}% ({transfer_info['received']}/{transfer_info['filesize']} bytes)")
            print(f"      Total Chunks Received: {len(transfer_info['chunks_received']) + 1}/{transfer_info['total_chunks']}")
            
            # Send acknowledgment for this chunk
            ack_response = {
                'type': 'CHUNK_ACK',
                'success': True,
                'transfer_id': transfer_id,
                'chunk_number': chunk_number,
                'received': transfer_info['received'],
                'progress': progress
            }
            
            print(f"   ✅ ─────────────────────────────────────────")
            print(f"   ✅ SENDING ACK: SEQ #{chunk_number}")
            print(f"   ✅ ─────────────────────────────────────────")
            
            return ack_response
            
        except Exception as e:
            print(f"   ❌ Error processing chunk: {e}")
            return {
                'type': RESP_ERROR,
                'success': False,
                'error': str(e),
                'chunk_number': chunk_number
            }
    
    def handle_file_upload_complete(self, data):
        """Handle file upload completion"""
        try:
            transfer_id = data.get('transfer_id')
            
            if transfer_id not in self.active_transfers:
                return {
                    'type': RESP_ERROR,
                    'success': False,
                    'error': 'Invalid transfer ID'
                }
            
            transfer_info = self.active_transfers[transfer_id]
            
            # Close file
            transfer_info['file_handle'].close()
            
            print(f"\n✅ ╔══════════════════════════════════════════╗")
            print(f"✅ ║   FILE UPLOAD COMPLETE                   ║")
            print(f"✅ ╚══════════════════════════════════════════╝")
            print(f"   Filename: {transfer_info['filename']}")
            print(f"   Unique Filename: {transfer_info['unique_filename']}")
            print(f"   Total Size: {transfer_info['received'] / 1024:.2f} KB")
            print(f"   Total Chunks Received: {len(transfer_info['chunks_received'])}/{transfer_info['total_chunks']}")
            print(f"   All Sequence Numbers: {sorted(transfer_info['chunks_received'])}")
            print(f"   Path: {transfer_info['filepath']}")
            print(f"\n🎉 ═══════════════════════════════════════════")
            print(f"🎉 FINAL ACK SENT - UPLOAD SUCCESS")
            print(f"🎉 ═══════════════════════════════════════════\n")
            
            # Get file path
            file_path = transfer_info['filepath']
            
            # Cleanup
            del self.active_transfers[transfer_id]
            
            # Send final acknowledgment
            return {
                'type': 'UPLOAD_COMPLETE_ACK',
                'success': True,
                'transfer_id': transfer_id,
                'filepath': file_path,
                'filename': transfer_info['unique_filename'],
                'total_chunks': len(transfer_info['chunks_received']),
                'total_bytes': transfer_info['received']
            }
            
        except Exception as e:
            print(f"   ❌ Error completing upload: {e}")
            return {
                'type': RESP_ERROR,
                'success': False,
                'error': str(e)
            }
    
    def get_file_for_download(self, filepath):
        """Get file data for download"""
        try:
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'rb') as f:
                file_data = f.read()
            
            return {
                'data': file_data,
                'filename': os.path.basename(filepath),
                'size': len(file_data)
            }
            
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return None
