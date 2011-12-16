#!/usr/bin/python

import sys

from flask import Flask, render_template, jsonify
app = Flask(__name__)

import socket

def check_mask(n):
	if not n: 
		return True
	try:
		mask = int(n)
		return ( mask > 1 and mask < 128)
	except:
		return False

def check_ipv4(n):
    try:
        socket.inet_pton(socket.AF_INET, n)
        return True
    except socket.error:
        return False

def check_ipv6(n):
    try:
        socket.inet_pton(socket.AF_INET6, n)
        return True
    except socket.error:
        return False

@app.route("/")
def hello():
	return render_template('index.html')

@app.route("/<host>/<proto>/prefix/<prefix>")
@app.route("/<host>/<proto>/prefix/<prefix>/<mask>")
def prefix(host, proto, prefix, mask=""):
	output = '<h3>' + host + '(' + proto + ') show route for ' + prefix + '/' + mask + '</h3>'

	# security check
	if ( (proto == "ipv6" and check_ipv6(prefix)) or (proto == "ipv4" and check_ipv4(prefix)) ) and check_mask(mask):
		if mask: prefix = prefix +"/"+mask
		ok, string = get_cmd_result(host , proto, "show route for " + prefix)
		if ok:
			string = "\n".join([ s.replace("1007-"," ") for s in string.split("\n") if not s.startswith("0000") ])
			output +='<pre>' + string + '</pre>'
		else:
			output += string
	else:
		output += prefix + ' not allowed'
	return render_template('index.html', output=output, typ="prefix", host=host+"/"+proto, prefix=prefix)

@app.route("/<host>/<proto>/detail/<name>")
def detail(host, proto, name):
	output = '<h3>' + host + '(' + proto + ') show protocols all ' + name + '</h3>'

	ok, string = get_cmd_result(host , proto, "show protocols all " + name)
	if ok:
		string = "\n".join([ s.strip() for s in string.split("\n") if s.startswith(" ")])
		output +='<pre>' + string + '</pre>'
	else:
		output += string
	return render_template('index.html', output=output, typ="detail", host=host+"/"+proto, name=name)

@app.route("/<host>/<proto>/summary")
def summary(host, proto):
	output = '<h3>' + host + '(' + proto + ') show protocols</h3>'

	ok, string = get_cmd_result(host , proto, "show protocols")
	if ok:
		output += '<pre><table>'
		for infos in string.split("\n"):
			if not infos.startswith(" "): continue
			d = infos.split()
			name = d[0]
			typ = d[1]
			if typ == "BGP":
				output += '<tr><td><a href="/%s/%s/detail/%s">%s</a><td><td>%s</td></tr>'%(host,proto,name,name,infos.replace(name,"").strip())
		output += '</table></pre>'
	else:
		output += string
	return render_template('index.html', output=output, typ="summary", host=host+"/"+proto)

@app.route("/<host>/<proto>/status")
def status(host, proto):
	string = get_cmd_result(host, proto, "show status")
	output = '<pre>' + string + '</pre>'
	return render_template('index.html', output=output, host=host+"/"+proto)

def get_cmd_result(host, proto, cmd):

	ret = True
	if proto == "ipv4":
		port = 9994
	else:
		port = 9996

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout(3.0)
#	sock.setblocking(0)
	try:
		sock.connect((host, port))
		app.logger.info("open socket on %s:%d", host, port)

		sock.send(cmd + "\n")
		app.logger.info("send %s socket on %s:%d", cmd, host, port)

		bufsize = 4096
		data = sock.recv(bufsize)
		string = data
		app.logger.info("read %s (%d)", data, len(data))
		code = string.split("\n")[-2][0:4]
		while not code[0] in ["0", "9", "8"]:
			data = sock.recv(bufsize)
			string = string + data
			app.logger.info("read %s (%d)", data, len(data))
			code = string.strip()[len(string.strip())-4:]

		if code[0] in [ "9", "8" ]:
			ret = False

		app.logger.info("return %s",string)
	except Exception as detail:
		ret = False
		string = "Failed connect to %s:%d (%s)"%(host, port, detail)
		app.logger.error(string)
	sock.close()
	return (ret, string)

if __name__ == "__main__":
	app.debug = True
	app.run()
