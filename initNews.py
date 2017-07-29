import requests
from bs4 import BeautifulSoup
import re
# 请替换为你的秘钥
appid = 'yourappid'
secretKey = 'yoursecretkey'

from fake_useragent import UserAgent
ua = UserAgent()
headers = {'user-agent': ua.chrome}

pythonweekly_init_issues_archive_url = (
    'http://www.pythonweekly.com/archive/')

def get_pythonweekly_init_issues_urls():
    url = pythonweekly_init_issues_archive_url
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.content, 'lxml')
    return [[
                a.text.split(' ')[-1].strip(),
                ''.join([url, a['href']]),
            ] for a in soup.select('li a')]

pythonweekly_init_issues_urls = get_pythonweekly_init_issues_urls()

def get_single_issue_info(issue):
    try:
        # issue = [text, url, list] 
        url = issue[1]
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.content, 'lxml')
        content = soup.select_one('td .defaultText')

        try:
            submenus = [i.text for i in content.find_all('strong')]
            for index, menu in enumerate(submenus):
                if re.search('[Aa]rticles', menu):
                    break
            start_text = [menu,]
            end_text = submenus[index+1]
        except:
            # 脏改 
            start_text = ['Articles,\xa0Tutorials and Talks',
                          '\xa0Tutorials and Talks', # 应对11,12.html
                          'Articles Tutorials and Talks']
            end_text = 'Interesting Projects, Tools and Libraries'

        flag = 0
        list_ = []
        for s in content.find_all('span'):
            if not flag:
                if s.text not in start_text:
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
        # return list_
        issue.append(list_)
        print('下载完成', issue[0])
    except Exception as e:
        print('wrong: ', issue[0], '\n', e)

from multiprocessing.dummy import Pool
pool = Pool(30)
pool.map(get_single_issue_info, pythonweekly_init_issues_urls)
pythonweekly_init_issues = pythonweekly_init_issues_urls


def baidu_translates(query):
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
    return res.json()['trans_result']

def get_translate(issue):
    articles = issue[-1]
    try:
        result = baidu_translates('\n'.join([i[0] for i in articles]))
        for index, i in enumerate(articles):
            i.append(result[index]['dst'])
        print('翻译完成', issue[0])
    except:
        print('**翻译失败**', issue[0])

pool.map(get_translate, pythonweekly_init_issues)


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
t = template.render(issues=pythonweekly_init_issues)

import time
with open('pythonweekly_init ' + time.ctime().replace(':', '_') + '.html', 'w', encoding='utf-8') as f:
    f.write(t)
    

pool.close()
pool.join()

# https://stackoverflow.com/questions/9626535/get-domain-name-from-url
# get_host = requests.urllib3.util.url.get_host # get_host(i[1])[1]
import tldextract
host_list = [
    tldextract.extract(i[1]).domain
    for *_, articles in pythonweekly_init_issues for i in articles ]

from collections import Counter
counter = Counter(host_list)
print(counter.most_common(20))

with open('pythonweekly_init.md', 'w', encoding='utf-8') as f:
    f.write(u'### PythonWeekly初期文章教程汇总\n')
    f.write(u'|      期号     |     英文名    | 中文名|\n')
    f.write(u'| ------------- |:-------------:| -----:|\n')
    for issue_num, issue_href, article_lists in pythonweekly_init_issues:
        for article_name, article_href, article_chinese in article_lists:
            f.write(('| [{issue_num}]({issue_href}) '
                     '| [{article_name}]({article_href}) '
                     '| [{article_chinese}]({article_href}) '
                     '| \n').format(**locals()))
