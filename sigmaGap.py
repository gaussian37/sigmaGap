import time
import datetime
import warnings
import os
import sys
import subprocess

# pip가 없으면 pip를 설치한다.
try:
    import pip
except ImportError:
    print("Install pip for python3")
    subprocess.call(['sudo', 'apt-get', 'install', 'python3-pip'])

try:
    import numpy
except ModuleNotFoundError:
    print("Install numpy")
    subprocess.call([sys.executable, "-m", "pip", "install", 'numpy'])
finally:
    import numpy as np
    
try:
    import pandas as pd
except ModuleNotFoundError:
    print("Install pandas")
    subprocess.call([sys.executable, "-m", "pip", "install", 'pandas'])
finally:
    import pandas as pd

try:
    import argparse
except ModuleNotFoundError:
    print("Install argparse")
    subprocess.call([sys.executable, "-m", "pip", "install", 'argparse'])
finally:
    import argparse

try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    print("Install matplotlib")
    subprocess.call([sys.executable, "-m", "pip", "install", 'matplotlib'])
finally:
    import matplotlib.pyplot as plt

try:
    import progressbar
except ModuleNotFoundError:
    print("Install progressbar")
    subprocess.call([sys.executable, "-m", "pip", "install", 'progressbar'])
finally:
    import progressbar

warnings.filterwarnings("ignore")

# argument parser를 구성해 주고 입력 받은 argument는 parse 합니다.
ap = argparse.ArgumentParser()
# -m, --money : 살 주식의 총 금액
ap.add_argument("-m", "--money", default=0, help="total money")
# -d, --divide : 분할 투자 갯수
ap.add_argument("-d", "--divide", required=True, help="the number of divide")
# -t, --txt : 출력할 text 이름을 받습니다. 기본값은 result
ap.add_argument("-t", "--txt", default="result.txt", help="Path of result text")
# -r, --rank : 상위 몇 rank 까지 조회할 지를 받습니다. 기본값은 30
ap.add_argument("-r", "--rank", default=30, help="how many company do you want?")
args = vars(ap.parse_args())

# 살 주식의 총 금액
totalMoney = int(args["money"])
# 분할 투자 갯수
divide = int(args["divide"])
# 상위 몇 rank 까지 조회할 것인가
ranks = int(args["rank"])
# 출력할 text 이름
fname = args["txt"]
# 분할 투자 시 한 기관에 투자할 금액
money = totalMoney // divide
# movingAverage 구간 크기
movingSize = 5

# 텍스트로 출력하도록 stdout 변경
sys.stdout = open(fname, 'w')

# kospi 상위 100개의 리스트를 가져 옵니다.
top100 = pd.read_excel("kospitop100.xlsx")
# 각 기관의 코드 번호를 문자열로 바꾸고 0으로 채워서 6자리로 만듭니다.
top100["code"] = top100["code"].astype(str)
for i in range(100):
    top100["code"][i] = top100["code"][i].zfill(6)

# 그래프를 저장할 디렉토리 생성합니다.
if os.path.exists("graph") == False:
    os.mkdir('graph')

# 선정된 기관의 담을 리스트
incentiveList = []
# movingAverage를 담을 리스트
predictionByMovingAverageList = {}

progress = progressbar.ProgressBar()
# 상위 기관부터 차례대로 접근 합니다.
for rank in progress(range(ranks)):
    # code를 입력 받습니다.
    code = top100["code"][rank]
    # 데이터를 담을 DataFrame을 생성합니다.
    df = pd.DataFrame()
    # 네이버 주식의 url에 입력받은 code를 대입합니다.
    url = 'http://finance.naver.com/item/sise_day.nhn?code={code}'.format(code=code)
    # 최근 1달 간의 주식 정보를 받아 옵니다.
    for i in range(1, 5):
        pg_url = '{url}&page={page}'.format(url=url, page=i)
        df = df.append(pd.read_html(pg_url, header=0)[0], ignore_index=True)
        df = df.dropna()
    # 일 별 최고가 리스트를 받아옵니다.
    highPrice = np.array(df["고가"])
    highPrice = np.flip(highPrice, axis = 0)
    # 일 별 종가 리스트를 받아옵니다.
    closingPrice = np.array(df["종가"])
    closingPrice = np.flip(closingPrice, axis = 0)
    # n일의 최고가 - (n-1)일의 종가 차이를 구합니다.
    # (n-1)일에서 종가 가격으로 구하고 n일에는 (종가 - 그 다음날 최고가)의 평균으로 팔 예정입니다.
    gap = np.array(highPrice[1:]) - np.array(closingPrice[:-1])

    f, (ax1, ax2, ax3) = plt.subplots(1, 3, sharex=False, sharey=False, figsize=(15, 5))
    # 최근 2달간의 데이터로 히스토그램을 그립니다.
    freq = ax1.hist(gap, rwidth=0.9)
    # 현재 가격을 받습니다.
    price = int(closingPrice[-1])
    # gap의 평균을 구합니다.
    mean = int(gap.mean())
    # gap의 표준편차를 구합니다.
    std = int(gap.std())
    
    # moving Average를 구합니다.    
    movingAverage = []
    # movingSize 단위로 movingAverage을 구합니다.
    for i in range(gap.size - movingSize + 1):
        movingAverage.append(gap[i:i+movingSize].mean())
    # moveingAverage들의 전체 평균을 구합니다.
    meanMovingAverage = int(np.mean(movingAverage))
    predictionByMovingAverage = int(movingSize*meanMovingAverage - np.sum(movingAverage[-movingSize+1:]))
    sellingPrice = int(closingPrice[-1] + predictionByMovingAverage)

    # 안정적인 투자를 위하여 mean - std가 음수 이면 투자하지 않습니다.
    # movingAverage를 계산해서 movingAverage를 이용한 내일 예상 차익값 0 이하이면 투자하지 않습니다.
    if (mean - std < 0) or (predictionByMovingAverage < 0):
        f.clf()
        continue
      
    
    numBuy = money // price        
    print("- " + top100["eng_company"][rank])        
    print("the number of buying : ", numBuy)        
    print("cost : ", format(numBuy * price, ","))
    print("prediction by movingAverage : ", format(predictionByMovingAverage, ","))
    incentive = int(predictionByMovingAverage * numBuy - predictionByMovingAverage * numBuy * 0.0031)
    print("incentive : ", format(incentive, ","))        
    incentiveList.append([incentive, top100["eng_company"][rank]])
    predictionByMovingAverageList[top100["eng_company"][rank]] = predictionByMovingAverage
    print()
    
    # 투자 대상 기관의 종가 대비 최고가 현황을 그래프로 출력합니다.
    ax1.set_title("Price Gap Histogram", fontSize=15)
    ax1.set_ylabel('frequency')
    ax1.set_xlabel("price gap")
    ax1.axvspan(mean - std, mean + std, facecolor='gray', alpha=0.2)

    ax1.text(mean - std, 1,
             "-σ : {:,}".format(mean - std), color='red', fontSize=12,
             bbox=dict(facecolor='y', edgecolor='red'))
    ax1.text(mean + std, 1,
             "σ : {:,}".format(mean + std), color='red', fontSize=12,
             bbox=dict(facecolor='y', edgecolor='red'))
    ax1.text(gap.min(), freq[0].max() * 0.8,
             "price : {:,}\nmean : {:,}\nstd : {:,}\n".format(price, mean, std, ","), color='red', fontSize=12)

    # Gap의 상태를 과거 부터 오늘 까지 현황을 표시합니다.
    # 회사 이름을 한 가운데 표시해 줍니다.
    ax2.set_title(top100["eng_company"][rank] + "\nGap State", fontSize=15)
    ax2.set_ylabel('price')
    ax2.set_xlabel('past → present')    
    ax2.bar(np.arange(len(gap)), gap, align='center',  alpha=0.5)

    # MovingAverage를 표시합니다.
    ax3.set_title("Moving Average state", fontSize=15)
    ax3.set_ylabel('price')
    ax3.set_xlabel('past → present')    
    ax3.bar(np.arange(len(movingAverage)), movingAverage, align='center',  alpha=0.5)
    ax3.text(0, np.max(movingAverage)*0.9,
            "mean of Moving Average : {:,}\nExpected Profit : {:,}\nSelling Price : {:,}".format(
                meanMovingAverage, predictionByMovingAverage, sellingPrice),
                fontSize=12, color='red')

    f.savefig("graph/" + top100["eng_company"][rank])
    f.clf()

# 대상 기관들을 예상 이윤 순으로 내림차순 정렬합니다.
incentiveList.sort(reverse=True)
# 분할 투자한 갯수만큼 상위 이윤 기관의 예상 이윤 총합을 구합니다.
totalMaxIncentive = sum([incentive[0] for incentive in incentiveList][:divide])
print("Total Maximum Incentive : ", format(totalMaxIncentive, ","))
# 분할 투자할 기관의 리스트를 최종 출력합니다.
print("Maximum Incentive List : ")
for incentive in incentiveList[:divide]:
    print("Company : {}, Incentive : {:,}".format(incentive[1], incentive[0]))   
