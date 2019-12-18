#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date	: 2014-11-26 15:34:50
# @Author  : RobinTang
# @Link	: https://github.com/sintrb/HtmlDiagnose
from __future__ import print_function
import sys
import re

try:
    # python3
    from html.parser import HTMLParser
    from urllib.parse import urljoin
except:
    # python2
    from HTMLParser import HTMLParser
    from urlparse import urljoin

__version__ = "1.0.2"
__description__ = "A web page HTML format diagnoser."


class HTMLSyntax(HTMLParser):
    '''
    HTML文档解析器
    '''

    def __init__(self):
        HTMLParser.__init__(self)
        self.error = None
        self.stack = []

        # 忽略的标签，这些标签不需要配对
        self.singleline = ['input', 'br', 'meta', 'link', 'img', 'base', 'hr']

    def handle_starttag(self, tag, attrs):
        '''
        处理标签起始
        '''
        if self.error:
            return
        if tag not in self.singleline:
            # print '>%s'%tag
            self.stack.append({
                'tag': tag,
                'attrs': attrs,
                'line': self.lineno,
                'offset': self.offset,
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
                self.error = '<%s>(line:%d offset:%d) not match </%s>(line:%d offset:%d)' % (t['tag'], t['line'], t['offset'], tag, self.lineno, self.offset)
            else:
                self.error = 'no match for </%s>(line:%d offset:%d) ' % (tag, self.lineno, self.offset)

    def getError(self):
        if not self.error and self.stack:
            self.error = ', '.join(['<%s>(line:%d offset:%d)' % (t['tag'], t['line'], t['offset']) for t in self.stack])
        return self.error


def getErrorTag(html):
    '''
    判断该html格式是否正确，正确返回None，否则返回错误描述
    '''
    syt = HTMLSyntax()
    syt.feed(html)
    return syt.getError()


def getAllLinks(path, html):
    '''
    获取HTML文档中的所有A标签链接
    '''
    links = []
    for h in re.findall(r'<a [^/]*href=["\']([^\s^\'^"]+)["\']', html):
        if h.startswith('tel:'):
            continue
        elif '://' not in h:
            url = urljoin(path, h).replace('/../', '/')
        else:
            url = h
        if url not in links:
            links.append(url)
    return links


def getHtmlOfUrl(url, **kwargs):
    '''
    获取url对应的html文档，根据需要替换该方法
    '''
    import requests
    res = requests.get(url, **kwargs)
    if res.status_code > 400:
        raise Exception(res.status_code)
    if res.cookies and 'cookies' in kwargs and type(kwargs['cookies']) == dict:
        kwargs['cookies'].update(res.cookies.get_dict())
    return res.text


def main():
    import pickle  # 用于状态持久化
    from optparse import OptionParser
    parser = OptionParser(usage='usage: %prog [options] url1 [url2 ...]', version="%prog " + __version__, description="")

    parser.add_option("-s", "--statefile",
                      action="store",
                      dest='state',
                      default='',
                      help="state file to save fetch state"
                      )
    parser.add_option("-H", "--header",
                      action="append",
                      dest='headers',
                      default=[],
                      help="set http request headers, like 'curl -H'",
                      )
    parser.add_option("-r", "--ignore",
                      action="append",
                      dest='ignores',
                      default=[],
                      help="add ignore url param, exp: -i 'random'",
                      )
    parser.add_option("-e", "--exclude",
                      action="append",
                      dest='excludes',
                      default=[],
                      help="exclude url pattern",
                      )
    parser.add_option("-i", "--include",
                      action="append",
                      dest='includes',
                      default=[],
                      help="include url pattern",
                      )
    parser.add_option("-n", "--new",
                      action="store_true",
                      dest='isnew',
                      default=False,
                      help="fetch with new state"
                      )
    parser.add_option("-g", "--goon",
                      action="store_true",
                      dest='isgoon',
                      default=False,
                      help="go on when occur error"
                      )

    (options, args) = parser.parse_args()

    savestatus = {}
    if options.state and not options.isnew:
        with open(options.state, 'rb') as f:
            savestatus = pickle.load(f)

    savestatus.setdefault('urls', [])
    savestatus.setdefault('doneurls', [])
    savestatus.setdefault('ignoreurls', [])
    savestatus.setdefault('exc', [])
    savestatus.setdefault('counter', 0)
    urls = savestatus['urls']
    doneurls = savestatus['doneurls']
    ignoreurls = savestatus['ignoreurls']
    counter = savestatus['counter']
    ignores = options.ignores

    isnew = options.isnew
    goon = options.isgoon
    withlast = 'last' in sys.argv
    savestatus.setdefault('cookies', {})
    cookies = savestatus['cookies']
    if withlast and doneurls:
        urls.append(doneurls.pop())
    if isnew:
        del urls[:]
        del doneurls[:]

    for arg in args:
        if arg.startswith('http://') or arg.startswith('https://'):
            urls.append(arg)

    if not urls:
        print(parser.format_help())
        exit()

    url = urls[0]
    if type(url) == tuple:
        url, preurl = url
    rooturl = re.findall("(https{0,1}://[^/]+)", url)[0]

    def printerr(e, url, preurl):
        if not preurl:
            sys.stderr.write(' %s in %s\n' % (e, url))
        else:
            sys.stderr.write(' %s in %s (from %s )\n' % (e, url, preurl))
        if not goon:
            raise Exception('Exit with exception')

    reqkwargs = {
        'headers': []
    }
    if options.headers:
        headers = {}
        for h in options.headers:
            ix = h.index(':')
            if ix > 0:
                key = h[0:ix].strip()
                val = h[ix + 1:].strip()
                if key.lower() == 'cookie':
                    # Cookie
                    rs = re.findall('([^;]+)=([^;]*)', val, re.MULTILINE | re.IGNORECASE) or []
                    for k, v in rs:
                        cookies[k] = v
                else:
                    headers[key] = val
        if headers:
            reqkwargs['headers'] = headers
    try:
        reqkwargs['cookies'] = cookies
        while urls:
            counter += 1
            url = urls.pop()
            preurl = None
            if type(url) == tuple:
                url, preurl = url
            if url and url not in doneurls and url.startswith('http'):
                print('fetching %5d %s ...' % (counter, url))
                html = None
                # 				html = getHtmlOfUrl(url, **reqkwargs)
                try:
                    html = getHtmlOfUrl(url, **reqkwargs)
                except Exception as e:
                    printerr(e, url, preurl)
                if not html:
                    continue
                doneurls.append(url)
                for u in getAllLinks(url, html):
                    if ignores and '?' in u:
                        ix = u.index('?')
                        u1 = u[0:ix]
                        u2 = re.sub('#.*', '', u[ix:])
                        for ic in ignores:
                            u2 = re.sub(r'[\?&]%s=[^&]*' % ic, '', u2)
                        u2 = u2.strip('&?')
                        iu = (u1 + '?' + u2) if u2 else u1
                        if iu in ignoreurls:
                            continue
                        ignoreurls.append(iu)
                    if options.excludes:
                        found = False
                        for p in options.excludes:
                            if re.match(p, u):
                                found = True
                                break
                        if found:
                            # print('exclude', u)
                            continue
                            # print(u, '->', iu)
                    if options.includes:
                        found = False
                        for p in options.includes:
                            if re.match(p, u):
                                found = True
                                break
                        if not found:
                            # print('not include', u)
                            continue
                    if rooturl in u and u not in urls and u not in doneurls:
                        nurl = u
                        if '#' in u:
                            nurl = u[0:u.index('#')]
                        urls.append((nurl, url))
                err = getErrorTag(html)
                if err:
                    printerr(err, url, preurl)
        print('finish!')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(e)
    except KeyboardInterrupt as e:
        print('user exit!')
        pass
    savestatus['counter'] = counter
    if options.state:
        with open(options.state, 'wb+') as f:
            pickle.dump(savestatus, f)


if __name__ == '__main__':
    main()
