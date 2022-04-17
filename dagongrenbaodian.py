import requests
import json
import sys
from GenEpub import gen_epub

'''
        "id": 6656,
        "createdAt": "2022-03-01T00:00:00Z",
        "updatedAt": "2022-04-17T08:34:56Z",
        "enterprise": "美团",
        "name": "后端",
        "city": 19,
        "otherWelfare": "",
        "monthlySalary": 21,
        "months": 15.5,
        "jobType": 0,
        "eduBackground": 2,
        "industry": 17,
        "onDuty": "10:00",
        "offDuty": "21:30",
        "dutyType": 1,
        "startNoonBreak": "12:00",
        "endNoonBreak": "14:00",
        "officePlace": 2,
        "leaveType": 1,
        "commuting": 2,
        "houseRent": 0,
        "remark": "",
        "pv": 131,
        "likeNum": 5,
        "dislikeNum": 0,
        "cityName": "北京"
'''

indMap = {1:"农林牧渔",2:"采矿",3:"制造业（食品饮料）",4:"制造业（纺织）",5:"制造业（汽车）",6:"制造业（机械设备）",7:"制造业（半导体）",8:"制造业（化工）",9:"制造业（医药）",10:"制造业（冶金）",11:"制造业（其他）",12:"电热燃气自来水",13:"建筑",14:"批发和零售",15:"交通运输仓储邮政",16:"住宿和餐饮",17:"信息传输软件互联网",18:"金融",19:"房地产",20:"商务（律师咨询广告等）",21:"租赁",22:"科学研究和技术服务",23:"水利环境和公共设施管理",24:"居民服务",25:"教育",26:"卫生和社会工作",27:"文化体育和娱乐业",28:"公共管理社会保障和社会组织",29:"其他"}
eduMap = {1:"专科",2:"本科",3:"硕士",4:"博士"}
commMap = {1:"0.5小时以内",2:"0.5~1小时",3:"1~1.5小时",4:"1.5~2小时",5:"2小时以上",6:"不限制"}
plcMap = {1:"工厂",2:"办公楼",3:"商铺",4:"公共设施",5:"户外",6:"其他"}
lveMap = {1:"双休",2:"双到单",3:"双到无",4:"大小周",5:"单休",6:"单到无",7:"三休",8:"无休"}
dtMap = {1: "固定", 2: "灵活"}

def download_page(i):
    url = 'https://api.puwangwang8.com/api/v1/job/detail'
    r = requests.post(url, json={'id': i})
    r.raise_for_status()
    j = r.json()
    d = j['data']
    d['createdAt'] = d['createdAt'].replace('T', ' ').replace('Z', '')
    d['updatedAt'] = d['updatedAt'].replace('T', ' ').replace('Z', '')
    d['name'] = d['name'] or '暂无'
    d['enterprise'] = d['enterprise'] or '暂无'
    d['cityName'] = d['cityName'] or '暂无'
    d['industry'] = d['industry'] or '暂无'
    d['remark'] = d['remark'] or '暂无'
    d['onDuty'] = d['onDuty'] or '暂无'
    d['offDuty'] = d['offDuty'] or '暂无'
    d['startNoonBreak'] = d['startNoonBreak'] or '暂无'
    d['endNoonBreak'] = d['endNoonBreak'] or '暂无'
    if d['monthlySalary'] and d['months']:
        d['salary'] = f"{d['monthlySalary']}K x {d['months']}薪"
    else:
        d['salary'] = '暂无'
    d['otherWelfare'] = d['otherWelfare'] or '暂无'
    d['houseRent'] = d['houseRent'] or '暂无'
    d['industry'] = indMap.get(d['industry'], '暂无')
    d['dutyType'] = dtMap.get(d['dutyType'], '暂无')
    d['eduBackground'] = eduMap.get(d['eduBackground'], '暂无')
    d['leaveType'] = lveMap.get(d['leaveType'], '暂无')
    d['officePlace'] = plcMap.get(d['officePlace'], '暂无')
    d['commuting'] = commMap.get(d['commuting'], '暂无')
    title = f"{d['name']}/{d['enterprise']}/{d['cityName']}/{d['salary']}/{d['eduBackground']}/{d['onDuty']}-{d['offDuty']}"
    co = f"""
        <ul>
        <li>ID：<a href='https://puwangwang8.com/#/jobInfo?id={i}'>{i}</a></li>
        <li>职位：{d['name']}</li>
        <li>企业：{d['enterprise']}</li>
        <li>城市：{d['cityName']}</li>
        <li>行业：{d['industry']}</li>
        <li>薪资：{d['salary']}</li>
        <li>福利描述：{d['otherWelfare']}</li>
        <li>工作时间：{d['onDuty']} - {d['offDuty']} {d['dutyType']}</li>
        <li>午休时间：{d['startNoonBreak']} - {d['endNoonBreak']}</li>
        <li>教育学历：{d['eduBackground']}</li>
        <li>休假类型：{d['leaveType']}</li>
        <li>办公地：{d['officePlace']}</li>
        <li>通勤时长（分钟）：{d['commuting']}</li>
        <li>房租（K/月）：{d['houseRent']}</li>
        <li>备注：{d['remark']}</li>
        <li>创建于：{d['createdAt']}</li>
        <li>更新于：{d['updatedAt']}</li>
        </ul>
    """
    return {'title': title, 'content': co}



def main():
    st = int(sys.argv[1])
    ed = int(sys.argv[2])
    
    src = 'https://puwangwang8.com/#/home'
    articles = [{
        'title': f'职位数据库（打工人宝典）{st}-{ed}',
        'content': f'<p>来源：<a href="{src}">{src}</a></p>'
    }]
    
    for i in range(st, ed + 1):
        try:
            print(f'page: {i}')
            art = download_page(i)
            articles.append(art)
        except Exception as ex: print(ex)
    gen_epub(articles, {})
    
if __name__ == '__main__': main()