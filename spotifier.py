# -*- coding: utf-8 -*-
"""
Module for registration/login to spotify.

This is specifically usefull for users from non-supported countries, because it
allows them to login / register with proxy with much more ease.

Functions supports http_proxy keyword. Only HTTP proxies are supported, HTTPS
aren't! If you wan't to use SOCK5 proxy, see IPtools:
https://github.com/Bystroushaak/IPtools

Author: Bystroushaak (bystrousak@kitakitsune.org)
Interpreter version: python 2.7
This work is licensed under a Creative Commons 3.0 Unported License
(http://creativecommons.org/licenses/by/3.0/).
"""
#= Imports ====================================================================
import sys
import json
import time



try:
	import dhtmlparser as html
except ImportError:
	sys.stderr.write(
		"This script requires pyDHTMLParser python module.\n"
		"You can download it from "
		"https://github.com/Bystroushaak/pyDHTMLParser\n"
	)
	sys.exit(1)

try:
	from httpkie import Downloader
except ImportError:
	sys.stderr.write(
		"This script requires httpkie python module.\n"
		"You can download it from "
		"https://github.com/Bystroushaak/httpkie\n"
	)
	sys.exit(1)



#= Functions & objects ========================================================
class SpotifierException(Exception):
	""
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return repr(self.value)


class InvalidUsernameException(SpotifierException):
	"Raised if username is considered invalid or is already used."
	def __init__(self, value):
		self.value = value


class InvalidPasswordException(SpotifierException):
	def __init__(self, value):
		self.value = value


class EmailTakenException(SpotifierException):
	"Raised when there is already account paired with this email."
	def __init__(self, value):
		self.value = value


class InvalidGenderException(SpotifierException):
	"Raised if there is unknown gender used."
	def __init__(self, value):
		self.value = value



def register(username, password, email, gender, date_of_birth_ts, http_proxy = None):
	"""
	Register new account, raise proper exceptions if there is a problem:
	 - InvalidUsernameException
	 - InvalidPasswordException
	 - EmailTakenException
	 - InvalidGenderException is raised when gender parameter is not "male"/"female"
	 - SpotifierException is raised in other cases (see .value for details from
	   server)

	Email is not verified, so you can use pretty much everything.

	Bevare of date_of_birth_ts timestamp - spotify won't let you register too
	much young accounts, so in case of trouble, try subtracting 567648000 for 18
	years.

	Function supports http_proxy parameter in format "http://server:port".
	"""
	d = Downloader(http_proxy = http_proxy)
	d.download(  # cookies
		"https://www.spotify.com/us/login/?forward_url=%2Fus%2F",
	)
	dom = html.parseString(
		d.download("https://www.spotify.com/us/signup/?forward_url=%2Fus%2F"),
	)

	# check username
	valid_username = d.download(
		"https://www.spotify.com/us/xhr/json/isUsernameAvailable.php",
		get = {"username": username}
	)
	if valid_username.strip() != "true":
		raise InvalidUsernameException(
			"Username '" + username + "' is invalid or already in use!"
		)

	# check password lenght
	min_password_len = dom.find("input", {"name": "password"})[0]
	min_password_len = int(min_password_len.params["data-rule-minlength"])
	if len(password) <= min_password_len:
		raise InvalidPasswordException("Password is too short.")

	# check email
	valid_email = d.download(
		"https://www.spotify.com/us/xhr/json/isEmailAvailable.php",
		get = {"email": email}
	)
	if valid_email.strip() != "true":
		raise EmailTakenException("Email is already used!")

	day, month, year = time.strftime(
		"%d %m %Y", time.localtime(int(date_of_birth_ts))
	).split()

	gender = gender.lower()
	if gender != "male" and gender != "female":
		raise InvalidGenderException(
			"Spotify doesn't support '" + gender + "' as gender!"
		)

	reg_form = {
		"form_token":    dom.find("input", {"name": "form_token"})[0].params["value"],
		"creation_flow": "",
		"forward_url":   "/us/",
		"username":      username,
		"password":      password,
		"email":         email,
		"confirm_email": email,
		"gender":        gender,
		"dob_month":     month,
		"dob_day":       day,
		"dob_year":      year,
		"signup_pre_tick_eula": "true",
	}

	data = d.download(
		"https://www.spotify.com/us/xhr/json/sign-up-for-spotify.php",
		post = reg_form,
	)

	jdata = json.loads(data)
	if jdata["status"] != 1:
		errors = []
		for error in jdata["errors"]:
			errors.append(error + ": " + jdata["errors"][error]["message"])
		raise SpotifierException(
			jdata["message"] + "\n" +
			"\n".join(errors)
		)


def login(username, password, http_proxy = None):
	"""
	Just login into spotify. This is usefull, because users from unsupported
	countries have to login thru IP from supported country every ~twoweeks, or
	their account is frozen until they do so.

	Function supports http_proxy parameter in format "http://server:port".

	Raise:
	 - SpotifierException if there is some problem.
	"""
	d = Downloader(http_proxy = http_proxy)
	dom = html.parseString(
		d.download(
			"https://www.spotify.com/us/login/?forward_url=%2Fus%2F",
		)
	)

	log_form = {
		"referrer": "",
		"utm-keywords": dom.find("input", {"name": "utm-keywords"})[0].params["value"],
		"user_name": username,
		"password": password
	}

	data = d.download(
		"https://www.spotify.com/us/xhr/json/login.php",
		post = log_form,
	)
	jdata = json.loads(data)

	if jdata["error"]:
		raise SpotifierException(jdata["msg"])
