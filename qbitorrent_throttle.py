#!/usr/bin/python3

import logging
import argparse
import qbittorrentapi

QBITTORRENT_USER	= "admin"
QBITTORRENT_PASS	= "adminadmin"
QBITTORRENT_HOST	= "localhost:8080"

IGNORE_SSL_CERT = False
DEBUG		= False

class throttle():
	def __init__(self):
		self.logger = logging.getLogger()
		if DEBUG:
			logging.basicConfig(level=logging.DEBUG, format='%(message)s')

		if IGNORE_SSL_CERT:
			self.qbt_client = qbittorrentapi.Client(host=QBITTORRENT_HOST, username=QBITTORRENT_USER, password=QBITTORRENT_PASS, DISABLE_LOGGING_DEBUG_OUTPUT=not DEBUG, VERIFY_WEBUI_CERTIFICATE=False)
		else:
			self.qbt_client = qbittorrentapi.Client(host=QBITTORRENT_HOST, username=QBITTORRENT_USER, password=QBITTORRENT_PASS, DISABLE_LOGGING_DEBUG_OUTPUT=not DEBUG)

	def log_msg(self, msg, is_exception=False):
		self.logger.debug(msg, exc_info=is_exception)

	def check_connection(self):
		try:
			self.log_msg("[*] Checking API server connection")
			self.qbt_client.auth_log_in()
			if self.qbt_client.is_logged_in:
				self.log_msg("[+] API server connection is OK")
				return True

			self.log_msg("[-] Failed connection to API server")
			return False
		except qbittorrentapi.exceptions.LoginFailed:
			self.log_msg("[-] Failed connection to API server. Login failed", is_exception=True)
			return False
		except qbittorrentapi.exceptions.APIConnectionError:
			self.log_msg("[-] Failed connection to API server", is_exception=True)
			return False

	def get_max_download_rate(self):
		return self.qbt_client.transfer_download_limit()

	def set_max_download_rate(self, rate):
		return self.qbt_client.transfer_set_download_limit(rate)

	def get_max_upload_rate(self):
		return self.qbt_client.transfer_upload_limit()

	def set_max_upload_rate(self, rate):
		return self.qbt_client.transfer_set_upload_limit(rate)

	def format_speed(self, rate):
		if rate == 0:
			return "Unlimited"
		return f"{int(rate/1024)}KB/s"

	def throttle_download(self, rate):
		before = self.get_max_download_rate()

		# If -1 set to unlimited
		if rate == -1:
			maxdownload = 0
		else:
			maxdownload = rate * 1024

		if maxdownload == before:
			self.log_msg(f"[*] New max upload rate is already set: {self.format_speed(maxdownload)}")
			return True

		self.log_msg(f"[+] Previous max download rate: {self.format_speed(before)}")
		self.log_msg(f"[*] Setting max download rate: {self.format_speed(maxdownload)}")
		self.set_max_download_rate(maxdownload)

		if before == self.get_max_download_rate():
			self.log_msg("[-] Failed setting max download rate. Rate didn't change")
			return False

		self.log_msg("[+] Sucessfully set max download rate")
		return True

	def throttle_upload(self, rate):
		before = self.get_max_upload_rate()

		# If -1 set to unlimited
		if rate == -1:
			maxupload = 0
		else:
			maxupload = rate * 1024

		if maxupload == before:
			self.log_msg(f"[*] New max upload rate is already set: {self.format_speed(maxupload)}")
			return True

		self.log_msg(f"[+] Previous max upload rate: {self.format_speed(before)}")
		self.log_msg(f"[*] Setting max upload rate: {self.format_speed(maxupload)}")
		self.set_max_upload_rate(maxupload)

		if before == self.get_max_upload_rate():
			self.log_msg("[-] Failed setting max upload rate. Rate didn't change")
			return False
		
		self.log_msg("[+] Sucessfully set max upload rate")
		return True
	
	def pause_all_torrents(self):
		self.qbt_client.torrents_pause(torrent_hashes='all')
		self.log_msg("[+] All torrents paused")
		return True

	def resume_all_torrents(self):
		self.qbt_client.torrents_resume(torrent_hashes='all')
		self.log_msg("[+] All torrents resumed")
		return True

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-D", "--maxdownload", type=int, required=False, help="Set max download speed [KBs]")
	parser.add_argument("-U", "--maxupload", type=int, required=False, help="Set max upload speed [KBs]")
	parser.add_argument("--stop", action='store_true', help="Stop all torrents")
	parser.add_argument("--start", action='store_true', help="Start all torrents")

	args = parser.parse_args()
	throttle_obj = throttle()

	if not throttle_obj.check_connection():
		return False
	
	if args.stop:
		if not throttle_obj.pause_all_torrents():
			return False

	if args.start:
		if not throttle_obj.resume_all_torrents():
			return False

	if args.maxdownload is not None:
		if not throttle_obj.throttle_download(args.maxdownload):
			return False

	if args.maxupload is not None:
		if not throttle_obj.throttle_upload(args.maxupload):
			return False
		
if __name__ == "__main__":
	main()
