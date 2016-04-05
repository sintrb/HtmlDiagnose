#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date	: 2014-11-26 15:34:50
# @Author  : RobinTang
# @Link	: https://github.com/sintrb/HtmlDiagnose
# @Version : 1.0

from HTMLParser import HTMLParser
from urlparse import urljoin
import urllib2
import sys
import re

class HTMLSyntax(HTMLParser):
	'''
	HTML文档解析器
	'''
	def __init__(self):
		HTMLParser.__init__(self)
		self.error = None
		self.stack = []

		# 忽略的标签，这些标签不需要配对
		self.singleline = ['input', 'br', 'meta', 'link', 'img', 'base']

	def handle_starttag(self, tag, attrs):
		'''
		处理标签起始
		'''
		if self.error:
			return
		if tag not in self.singleline:
			# print '>%s'%tag
			self.stack.append({
				'tag':tag,
				'attrs':attrs,
				'line':self.lineno,
				'offset':self.offset,
			})
			
	def handle_endtag(self, tag):
		'''
		处理标签结束
		'''
		if self.error:
			return
		if tag not in self.singleline:
			# print '<%s'%tag
			if self.stack:
				t = self.stack.pop()
				if t['tag'] == tag:
					return
				self.error = '<%s>(line:%d offset:%d) not match </%s>(line:%d offset:%d)'%(t['tag'], t['line'], t['offset'], tag, self.lineno, self.offset)
			else:
				self.error = 'no match for </%s>(line:%d offset:%d) '%(tag, self.lineno, self.offset)
	def getError(self):
		if not self.error and self.stack:
			self.error = ', '.join(['<%s>(line:%d offset:%d)'%(t['tag'], t['line'], t['offset']) for t in self.stack])
		return self.error

def getErrorTag(html):
	'''
	判断该html格式是否正确，正确返回None，否则返回错误描述
	'''
	syt =HTMLSyntax()
	syt.feed(html)
	return syt.getError()

def getAllLinks(path, html):
	'''
	获取HTML文档中的所有A标签链接
	'''
	links = []
	for h in re.findall(r'<a [^/]*href="([^"]+)"', html):
		url = urljoin(path,  h).replace('/../', '/')
		if url not in links:
			links.append(url)
	return links


def getHtmlOfUrl(url):
	'''
	获取url对应的html文档，根据需要替换该方法
	'''
	try:
		# use requests
		import requests
		return requests.get(url).text
	except:
		pass
	try:
		html = urllib2.urlopen(url).read()
		try:
			html = html.decode('utf-8')
		except:
			try:
				html = html.decode('gbk')
			except:
				html = None
		return html
	except:
		return None


if __name__ == '__main__':
	import pickle	# 用于状态持久化

	savestatus = {}
	try:
		with open('savestatus', 'r+') as f:
			savestatus = pickle.load(f)
	except:
		# print 'load failed'
		pass

	if 'urls' in savestatus:
		urls = savestatus['urls']
	else:
		urls = savestatus['urls'] = []

	if 'doneurls' in savestatus:
		doneurls = savestatus['doneurls']
	else:
		doneurls = savestatus['doneurls'] = []

	rooturl = None
	isnew = 'new' in sys.argv
	goon = 'goon' in sys.argv
	withlast = 'last' in sys.argv
	if withlast and doneurls:
		urls.append(doneurls.pop())
	if isnew:
		del urls[:]
		del doneurls[:]

	for arg in  sys.argv[1:]:
		if arg.startswith('http://') or arg.startswith('https://'):
			urls.append(arg)

	if not urls:
		print 'not url to fetch'
		print 'usage: python HtmlDiagnose.py [new] [goon] url1 url2 ...'
		exit()

	if not rooturl and 'rooturl' in savestatus:
		rooturl = savestatus['rooturl']
	else:
		savestatus['rooturl'] = rooturl

	def printerr(e, url, preurl):
		if not preurl:
			sys.stderr.write(u' %s in %s\n'%(e, url))
		else:
			sys.stderr.write(u' %s in %s (from %s)\n'%(e, url, preurl))
		if not goon:
			with open('savestatus', 'w+') as f:
				pickle.dump(savestatus, f)
			exit()
	try:
		while urls:
			url = urls.pop()
			preurl = None
			if type(url) == tuple:
				url, preurl = url
			if url and url not in doneurls and url.startswith('http'):
				print '%s'%url
				html = None
				try:
					html = getHtmlOfUrl(url)
				except Exception, e:
					printerr(e, url, preurl)
				if not html:
					continue
				doneurls.append(url)
				for u in getAllLinks(url, html):
					if rooturl in u and u not in urls and u not in doneurls:
						nurl = u
						if '#' in u:
							nurl = u[0:u.index('#')]
						urls.append((nurl, url))
				err = getErrorTag(html)
				if err:
					printerr(err, url, preurl)

		print 'finish!'
	except Exception, e:
		print e

	with open('savestatus', 'w+') as f:
		pickle.dump(savestatus, f)
