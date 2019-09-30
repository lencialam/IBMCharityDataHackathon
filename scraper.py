# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import urllib
from bs4 import BeautifulSoup
import urlparse
import requests
df = pd.read_csv('Data/basic_info.csv')
# df=df.dropna(axis=0, how='any')
fina_df = pd.read_csv('Data/fina_info.csv')
invest_df = pd.read_csv('Data/invest_info.csv')
project_df = pd.read_csv('Data/project.csv')
project_df = project_df.loc[project_df['项目编码'].str.isnumeric(),:]
project_df['项目编码'] = project_df['项目编码'].astype(np.int32)
# collect all organizations
all_organizations = list(set(list(set(invest_df.loc[:,'受助单位名称'].unique())) + list(set(project_df.loc[:,'基金会名称'])) +list(set(df.loc[:,'基金会名称']))))
# Set the startingpoint for the spider and initialize 

url = "http://www.baidu.com/s?wd=公益基金會&rsv_spt=1&rsv_iqid=0xadfaa58e00000586&issp=1&f=8&rsv_bp=1&rsv_idx=2&ie=utf-8&rqlang=cn&tn=baiduhome_pg&rsv_enter=0&oq=%25E5%2585%25AC%25E7%259B%258A%25E5%259F%25BA%25E9%2587%2591%25E6%259C%2583&rsv_t=d4ba%2FY7RvuB5V74XU7eCxUg%2B%2BcpQule%2Bvn%2BuOMu6ba2WA5UoEnXS7Yot0klYxZq0ZhUO&rsv_pq=ff9a12f90000ebf3"
LIMIT = 100000
# create lists for the urls in que and visited urls
urls = [url]
visited = [url]
organization_dict = dict(zip(all_organizations,[0]*len(all_organizations)))
# Since the amount of urls in the list is dynamic
#   we just let the spider go until some last url didn't
#   have new ones on the webpage
while len(urls)>0 and len(visited) < LIMIT:
    r= requests.get(url)
#     print urls
    urls.pop(0)
#     print urls
    soup = BeautifulSoup(r.content,"lxml")
    links = soup.find_all('a')
    for organization in all_organizations:    
        if organization in str(soup.body):
            organization_dict[organization] +=1
    for link in links:
#             newurl =  urlparse.urljoin(link.base_url,link.url)
        newurl = link.get('href')
#         re.compile('Cette entreprise est membre de la FVE\w+..\w+'))
        
        if newurl not in visited:
            visited.append(newurl)
            urls.append(newurl)
#     print urls
#     url.
pd.DataFrame(organization_dict.items()).to_csv('organization_dict.csv',index=False)
