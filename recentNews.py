import requests
from bs4 import BeautifulSoup
import re
# 请替换为你的秘钥
appid = 'yourappid'
secretKey = 'yoursecretkey'


from fake_useragent import UserAgent
ua = UserAgent()
headers = {'user-agent': ua.chrome}

pythonweekly_recent_issues_archive_url = (
    'http://us2.campaign-archive2.com/home/'
    '?u=e2e180baf855ac797ef407fc7&id=9e26887fc5')

def get_pythonweekly_recent_issues_urls():
    
    res = requests.get(pythonweekly_recent_issues_archive_url, headers=headers)
    soup = BeautifulSoup(res.content, 'lxml')
    return [[
                a.text.split(' ')[-1].strip(),
                a['href'],
            ]
            for a in soup.select('li a')]

pythonweekly_recent_issues_urls = get_pythonweekly_recent_issues_urls()

def get_single_issue_info(url):
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.content, 'lxml')
    content = soup.select_one('td .defaultText')

    submenus = [i.text for i in content.find_all('span', attrs={'style':"color:#B22222"})]
    for index, i in enumerate(submenus):
        if re.search('[Aa]rticles', i):
            break
    start_text = i
    end_text = submenus[index+1]

    flag = 0
    list_ = []
    for s in content.find_all('span'):
        if not flag:
            if s.text != start_text:
                continue
            else:
                flag = 1
                continue
        if s.text == end_text:
            break
        try:
            one = [s.text.strip(), s.find('a')['href']]
            # print(one)
            list_.append(one)
        except TypeError:
            pass
    return list_

for i in pythonweekly_recent_issues_urls:
    # [text, url, list] 
    print(i[0])
    i.append(get_single_issue_info(i[1]))

pythonweekly_recent_issues = pythonweekly_recent_issues_urls


def baidu_translate(query):
    '''
    http://api.fanyi.baidu.com/api/trans/product/apidoc
    '''
    from hashlib import md5
    import random

    url = 'http://api.fanyi.baidu.com/api/trans/vip/translate'
    fromLang = 'en'
    toLang = 'zh'
    salt = random.randint(32768, 65536)

    sign = appid + query + str(salt) + secretKey
    m1 = md5()
    m1.update(sign.encode('utf-8'))
    sign = m1.hexdigest()
    
    params = {'appid':appid,
              'q':query,
              'from':fromLang,
              'to':toLang,
              'salt':str(salt),
              'sign':sign,}
    res = requests.get(url, params=params)
    return res.json()['trans_result'][0]['dst']

for *_, articles in pythonweekly_recent_issues:
    for i in articles:
        i.append(baidu_translate(i[0]))
    print('done')


from jinja2 import Template
table = """
<table>
    {% for issue_num, issue_href, article_lists in issues %}
        {% for article_name, article_href, article_chinese in article_lists %}
        <tr>
            <td><a href='{{issue_href}}'>{{ issue_num }}</a></td>
            <td><a href='{{article_href}}'>{{ article_name }}</a></td>
            <td><a href='{{article_href}}'>{{ article_chinese }}</a></td>
        </tr>
        {% endfor %}
    {% endfor %}
</table>
"""

template = Template(table)
t = template.render(issues=pythonweekly_recent_issues)

import time
with open('pythonweekly_recent ' + time.ctime().replace(':', '_') + '.html', 'w', encoding='utf-8') as f:
    f.write(t)

import tldextract
host_list = [
    tldextract.extract(i[1]).domain
    for *_, articles in pythonweekly_recent_issues for i in articles ]

from collections import Counter
counter = Counter(host_list)
counter.most_common(20)


with open('pythonweekly_recent.md', 'w', encoding='utf-8') as f:
    f.write(u'### PythonWeekly文章教程近期汇总\n')
    f.write(u'|      期号     |     英文名    | 中文名|\n')
    f.write(u'| ------------- |:-------------:| -----:|\n')
    for issue_num, issue_href, article_lists in pythonweekly_recent_issues:
        for article_name, article_href, article_chinese in article_lists:
            f.write(('| [{issue_num}]({issue_href}) '
                     '| [{article_name}]({article_href}) '
                     '| [{article_chinese}]({article_href}) '
                     '| \n').format(**locals()))
