# coding: utf-8
import numpy as np
import pandas as pd
import urllib
from bs4 import BeautifulSoup
import urlparse
from sklearn.metrics.pairwise import cosine_similarity



df = pd.read_csv('Data/basic_info.csv')
# df=df.dropna(axis=0, how='any')
df['原始基金'] = df['原始基金'].replace('[\¥,]', '', regex=True).astype(float)
df



fina_df = pd.read_csv('Data/fina_info.csv')

invalid_organizations = fina_df.loc[fina_df['工资福利支出'] / fina_df['总支出'] > 0.1,'基金会名称']

invest_df = pd.read_csv('Data/invest_info.csv')



project_df = pd.read_csv('Data/project.csv')
project_df = project_df.loc[project_df['项目编码'].str.isnumeric(),:]
project_df['项目编码'] = project_df['项目编码'].astype(np.int32)
project_df


# transparency
transparency_df = pd.read_csv('Data/transparency_info.csv').rename(columns={'分数':'score','基金会名称':'基金会名称','排名':'排名'}).set_index('基金会名称')
transparency_df = transparency_df.loc[:,'score'].dropna()
transparency_df -= transparency_df.min()
transparency_df /= transparency_df.max()
print "transparency:"
print "max", transparency_df.max(), "min", transparency_df.min()



# collect all organizations
all_organizations = list(set(list(set(invest_df.loc[:,'受助单位名称'].unique())) + list(set(project_df.loc[:,'基金会名称'])) +list(set(df.loc[:,'基金会名称']))))



fieldSet = set()
def create_field_set(row):
    global fieldSet
    fieldList = row.split('，')
    for field in fieldList:
        if field not in fieldSet:
            fieldSet.add(field)



#create field set for encoding
fieldDf = df.loc[:,'基金会行业领域']
fieldDf.apply(create_field_set)
fieldSet



#transform field information into multiple one-hot encoding
fieldList = list(fieldSet)
def multihot_encoding(row):
    global fieldSet
    global fieldList
    field_encoding = np.zeros(len(fieldSet))
    fields = row.split('，')
    for field in fields:
        if field in fieldSet:
            index = fieldList.index(field)
            field_encoding[index] = 1
    return field_encoding


multihotField = fieldDf.apply(multihot_encoding)


# calculate the 
fieldSimilarityDf = pd.DataFrame(columns = df['基金会名称'], index=df['基金会名称'])
length,_ = fieldSimilarityDf.shape
# compute the cosine similarity
fieldSimilarityDf = pd.DataFrame(cosine_similarity(np.array(list(multihotField))), columns = df['基金会名称'], index=df['基金会名称'])
fieldSimilarityDf



bi_invest_df = invest_df.loc[:,['受助单位名称','项目编码']].join(project_df.loc[:,['基金会名称','项目编码','SDG']].set_index('项目编码'), on='项目编码').dropna(subset=['基金会名称'])
bi_invest_df



# record the investment history

investedDf = pd.DataFrame(columns = all_organizations, index=all_organizations).fillna(0)



def count_invest(df):
    for index, row in bi_invest_df.iterrows():
        helped = row['受助单位名称']
        helping = row['基金会名称']
        if helped not in df.index or  helping not in df.index:
            print help, helping
            
            continue
        
        df.loc[helping, helped] +=1  
    return df
investedDf = count_invest(investedDf)



SDGList = ['无贫穷',
'零饥饿',
'良好健康与福祉',
'优质教育',
'性别平等',
'清洁饮水和卫生设施',
'经济适用的清洁能源',
'体面工作和经济增长',
'产业、创新和基础设施',
'减少不平等',
'可持续城市和社区',
'负责任消费和生产',
'气候行动',
'水下生物',
'陆地生物',
'和平、正义与强大机构',
'促进目标实现的伙伴关系',
'其他']
SDGSet = set(SDGList)
execute_organizations = bi_invest_df['受助单位名称'].unique()
executeDict = dict()

for e_organization in execute_organizations:
    currentDf = bi_invest_df.loc[bi_invest_df['受助单位名称'] == e_organization,['受助单位名称','SDG']]
    SDGs = []
    for index, row in currentDf.iterrows():
        SDGs += row['SDG'].split('，')  
    executeDict[currentDf['受助单位名称'].iloc[0]] = SDGs
SDGDf = pd.DataFrame(executeDict.items()).rename(columns={0:'受助单位名称',1:'SDG'})



def SDGMultiHotEncoding(row):
    global SDGList
    currentEncoding = np.zeros(len(SDGList))
    for SDG in row:
        index = SDGList.index(SDG)
        currentEncoding[index] = 1
    return currentEncoding



SDGDf['SDG'] = SDGDf['SDG'].apply(SDGMultiHotEncoding)


SDGSimilarityDf = pd.DataFrame(cosine_similarity(np.array(list(SDGDf['SDG']))), columns=SDGDf['受助单位名称'], index= SDGDf['受助单位名称'])


# create a numpy array for quick operation
invested2D = np.zeros((len(all_organizations),len(all_organizations)))
for i in range(len(all_organizations)):
    helping = all_organizations[i]
    if helping in set(bi_invest_df['基金会名称']):
        # gather all the organizations that helping has invested
        hashelpeds = list(bi_invest_df.loc[bi_invest_df['基金会名称'] == helping,'受助单位名称'].unique())
    else:
        continue        
        
    # if there is no invested organizations for this helping organization
    if len(hashelpeds) ==0:
        continue
    for j in range(len(all_organizations)):
        
        helped = all_organizations[j]
        if helping in fieldSimilarityDf.index and helped in SDGSimilarityDf.index:         
            if len(hashelpeds) == 0:
                invested2D[i][j] = 0
            else:
                num_hashelped = 0
                accumulatedSimilarity = 0
                for hashelped in hashelpeds:
            
                    if hashelped in SDGSimilarityDf.index and hashelped in fieldSimilarityDf.index:
                        num_hashelped +=1
                        accumulatedSimilarity += SDGSimilarityDf[hashelped][helped] * fieldSimilarityDf[helping][hashelped]
                if num_hashelped == 0:
                    invested2D[i,j] = 0
                else:
                    invested2D[i,j] = accumulatedSimilarity/num_hashelped
        else:
            invested2D[i][j] = 0
investedSimilarity = pd.DataFrame(invested2D,columns=all_organizations, index = all_organizations)


# <hr>


# ability of execution 

manforceDf = df.loc[:,['基金会名称','全职员工','志愿者数量', '负责人数']]
manforceDf.fillna(0, inplace =True)
manforceDf['man_force'] = manforceDf.apply(lambda(row): row['全职员工'] + row['志愿者数量'] + row['负责人数'], axis = 1)
manforceDf  = manforceDf.loc[:,['基金会名称', 'man_force']].set_index('基金会名称')
manforceDf['man_force'] /= manforceDf['man_force'].max()
print "man force:"
print "max", manforceDf['man_force'].max(), "min",manforceDf['man_force'].min()



leaderDf = df.loc[:,['基金会名称','负责人中现任国家工作人员数','负责人中担任过省部级及以上领导职务的人数']]
leaderDf.fillna(0, inplace =True)
leaderDf['leader_num'] = leaderDf.apply(lambda(row): row['负责人中现任国家工作人员数'] + row['负责人中担任过省部级及以上领导职务的人数'],axis =1)
leaderDf=leaderDf.loc[:,['基金会名称','leader_num']].set_index('基金会名称')
leaderDf['leader_num'] /= leaderDf['leader_num'].max()
print "number of leaders:"
print "max",leaderDf['leader_num'].max(),"min", leaderDf['leader_num'].min()


# <hr>


# portion of expenditure on social service in 2015
servicePortionDf = fina_df.loc[fina_df['财务年度']==2015,['基金会名称','总支出','公益事业支出']]
servicePortionDf['service_portion'] = servicePortionDf.loc[servicePortionDf['总支出']>0,:].apply(lambda(row): row['公益事业支出'] / row['总支出'] , axis=1)
servicePortionDf['service_portion'].fillna(0, inplace=True)
servicePortionDf = servicePortionDf.loc[:, ['基金会名称', 'service_portion']].set_index('基金会名称')
servicePortiondf = servicePortionDf.loc[servicePortionDf['service_portion']>1,'service_portion'] =1
print "service portion"
print "max", servicePortionDf["service_portion"].max(), "min",servicePortionDf["service_portion"].min()



# improve rate of total assests & social service expenditure
fina_df201415 = fina_df.loc[(fina_df['财务年度'] == 2015) | (fina_df['财务年度'] == 2014),:]
organizations = list(fina_df201415['基金会名称'].unique())
operationDf = pd.DataFrame(columns = ['total','service'], index = organizations)
fina_df201415 = fina_df201415.loc[fina_df201415['财务年度'] == 2015,['基金会名称','净资产','公益事业支出']].join( fina_df201415.loc[fina_df201415['财务年度'] == 2014,['基金会名称','净资产','公益事业支出']].rename(columns={'基金会名称':'基金会名称','净资产':'净资产2014','公益事业支出':'公益事业支出2014'}).set_index('基金会名称'), on='基金会名称')
total_mean = fina_df201415.loc[(fina_df201415['净资产'] >0) & (fina_df201415['净资产2014']>0),:].apply(lambda(row): (row['净资产'] - row['净资产2014'])/row['净资产2014'],axis=1).mean()
service_mean = fina_df201415.loc[(fina_df201415['公益事业支出'] >0) & (fina_df201415['公益事业支出2014']>0),:].apply(lambda(row): (row['公益事业支出'] - row['公益事业支出2014'])/row['公益事业支出2014'],axis=1).mean()
fina_df201415 = fina_df.loc[(fina_df['财务年度'] == 2015) | (fina_df['财务年度'] == 2014),:]
for organization in organizations:
    
#     print organization
    df2014 = fina_df201415.loc[(fina_df201415['基金会名称'] == organization )&(fina_df201415['财务年度'] == 2014), ['净资产','公益事业支出']]
    df2015 = fina_df201415.loc[(fina_df201415['基金会名称'] == organization )&(fina_df201415['财务年度'] == 2015), ['净资产','公益事业支出']]
#     print (df2015.iloc[0]['净资产']-df2014.iloc[0]['净资产'])
    if df2014.shape[0] <1 or df2015.shape[0] <1:
        operationDf.loc[operationDf.index ==organization,'total']= total_mean
        operationDf.loc[operationDf.index ==organization,'service']=service_mean
    else:
        # fill the incomplete info with mean value
        if df2014.iloc[0]['净资产'] == 0 or df2015.iloc[0]['净资产'] == 0 : operationDf.loc[operationDf.index==organization,'total'] = total_mean
        else: operationDf.loc[operationDf.index==organization,'total'] = (df2015.iloc[0]['净资产']-df2014.iloc[0]['净资产'])/ df2014.iloc[0]['净资产']
        if df2014.iloc[0]['公益事业支出'] == 0 or df2015.iloc[0]['公益事业支出'] == 0 : operationDf.loc[operationDf.index==organization,'service'] = service_mean
        else: operationDf.loc[operationDf.index==organization,'service']=(df2015.iloc[0]['公益事业支出']-df2014.iloc[0]['公益事业支出'])/df2014.iloc[0]['公益事业支出']



# normalize
operationDf -= operationDf.min()
operationDf /= operationDf.max()
print "total trend:"
print "max", operationDf['total'].max(), "min", operationDf['total'].min()
print "service expenditure trend:"
print "max", operationDf['service'].max(), "min", operationDf['service'].min()



# total asset in 2015
totalAssetDf = fina_df.loc[fina_df['财务年度']==2015,['基金会名称','净资产']].set_index('基金会名称')
totalAssetDf -= totalAssetDf.min()
totalAssetDf /= totalAssetDf.max()
print "total asset:"
print "max", totalAssetDf['净资产'].max(), "min", totalAssetDf['净资产'].min()



# total service expenditure in 2015
serviceExpendDf = fina_df.loc[fina_df['财务年度']==2015,['基金会名称','公益事业支出']].set_index('基金会名称').dropna()
serviceExpendDf= serviceExpendDf/serviceExpendDf.max()
print "service expenditure:"
print "max",serviceExpendDf['公益事业支出'].max(),"min",serviceExpendDf['公益事业支出'].min()


# <h1>News Scraper</h1>


# results from scraper.py
scraperDf = pd.read_csv('organization_dict.csv')
scraperDf.rename(columns={'0':'基金会名称','1':'count'}, inplace=True)
scraperDf = scraperDf.set_index('基金会名称')
scraperDf['count'] = scraperDf['count']/scraperDf['count'].max()
print "scraper result:"
print "max" ,scraperDf['count'].max(),"min",scraperDf['count'].min()


# <h1>Final Score</h1>

def calculateFinalScore(investing= '神华公益基金会', strategy = 40, influence=30, execution=20):

    INVESTING = investing
    print INVESTING
    STRATEGY_WEIGHT = strategy
    INFLUENCE_WEIGHT = influence
    EXECUTION_WEIGHT = execution

    all_organizations_except_investing = list(all_organizations)
    all_organizations_except_investing.pop(all_organizations.index(INVESTING))

    #get rid of those organizations whose 工資比例 > 10%
    for invalid_org in invalid_organizations:
        if invalid_org in all_organizations_except_investing :
            all_organizations_except_investing.pop(all_organizations_except_investing.index(invalid_org)) 
            
    score_dict = dict(zip(all_organizations_except_investing, np.zeros(len(all_organizations_except_investing))))
    strategies = np.zeros(len(all_organizations_except_investing))
    influences = np.zeros(len(all_organizations_except_investing))
    executions = np.zeros(len(all_organizations_except_investing))
    for i, organization in enumerate(all_organizations_except_investing):
        # similarity
        
        #direct similarity based on field
        if organization in fieldSimilarityDf and INVESTING in fieldSimilarityDf:
            
            strategies[i] += fieldSimilarityDf[organization][INVESTING]
        # invest similarity based on SDGs and invest history
        strategies[i] += investedSimilarity[INVESTING][organization]

        # transparency score
        if organization in transparency_df.index:
            strategies[i] += transparency_df.loc[organization]    
        else:
            strategies[i] += transparency_df.mean()
           
        # influence 
        
        # total asset
        if organization in totalAssetDf.index:
            influences[i] += totalAssetDf.loc[organization]
        else:
            influences[i] += totalAssetDf.mean()
        #service expenditure
        if organization in serviceExpendDf.index:  
            influences[i] += serviceExpendDf.loc[organization]
        else:
            influences[i] += serviceExpendDf.mean()
        
        # scraper result
        if organization in scraperDf.index:
            influences[i] += scraperDf.loc[organization]
        else:
            influences[i] += scraperDf.mean()
        
        # execution efficiency
        if organization in operationDf.index:
            executions[i] += operationDf.loc[organization]['total'] + operationDf.loc[organization]['service']
        else:
            executions[i] += operationDf['total'].mean() + operationDf['service'].mean()
        if organization in manforceDf.index:
            executions[i] += manforceDf.loc[organization]['man_force']
        else:
            executions[i] += manforceDf.mean()
        if organization in leaderDf.index:
            executions[i] += leaderDf.loc[organization]['leader_num']
        else:
            executions[i] += leaderDf.mean()
        if organization in servicePortionDf:
            executions[i] += executions[j].loc[organization]['service_portion']
    strategies -= np.min(strategies)
    strategies /= np.max(strategies)
    influences -= np.min(influences)
    influences /= np.max(influences)

    executions -= np.min(executions)
    executions /= np.max(executions)

    strategyDict = dict(zip(all_organizations_except_investing, strategies))
    influenceDict = dict(zip(all_organizations_except_investing, influences))
    executionDict = dict(zip(all_organizations_except_investing, executions))
    finalScoreDf= pd.DataFrame(columns=all_organizations_except_investing, index=[INVESTING])
    for organization in all_organizations_except_investing:
        # similarity
        strategy = strategyDict[organization]
        influence = influenceDict[organization]
        execution = executionDict[organization]
        
        finalScoreDf.iloc[0][organization]=strategy* STRATEGY_WEIGHT + influence* INFLUENCE_WEIGHT + execution * EXECUTION_WEIGHT

    finalScoreDf = finalScoreDf.transpose().rename(columns={INVESTING:'score'})
        


    return finalScoreDf.sort_values(['score'] ,ascending=False)


print "Data Preprocessing Ready!"

