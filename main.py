import csv
import json
import re
import dateparser as dp
import threading
import random
import time
import datetime
from collections import Counter
import math
from textblob import TextBlob
import db

TOTAL_DATES = -365

COLUMNS = ['open', 'high', 'low', 'close']
IS_TICKER = re.compile("[A-Z]{1,4}|\d{1,3}(?=\.)|\d{4,}")
# This is a regex that determines if a string is a stock ticker
COMPANY_LIST = "companylist.csv"

WSB_DATASET = "/media/christopher/ssd/wsbData.json"
HISTORICAL_DATA = "data/{0}.csv"
ALL_COUNTS = "dataset/AllCounts.json"
DATES = json.load(open("dataset/ListOfDatesOrder.json"))

def get_all_possible_tickers(fileName="companylist.csv"):
	with open(fileName, 'rb') as f:
		reader = csv.reader(f)
		your_list = list(reader)
	return [x[0] for x in your_list[1:]]

def get_company_by_ticker(tickerVal):
	with open(COMPANY_LIST, 'rb') as f:
		reader = csv.reader(f)
		your_list = list(reader)
	for x in your_list[1:]:
		if x[0] == tickerVal:
			return x[1]

def get_all_info_by_ticker(tickerVal):
	with open(COMPANY_LIST, 'rb') as f:
		reader = csv.reader(f)
		your_list = list(reader)
	for x in your_list[1:]:
		if x[0] == tickerVal:
			return x

def get_average_volume_by_ticker(tickerVal):
	try:
		with open(HISTORICAL_DATA.format(tickerVal), 'rb') as f:
			reader = csv.reader(f)
			your_list = list(reader)
		total = 0
		count = 0
		your_list.pop(0)
		for x in your_list[TOTAL_DATES:]:
			try:
				total += int(x[-1])
				count += 1
			except:
				pass
		return (float(total) / float(count))
	except Exception as exp:
		print exp
		return 0

def get_open_price_by_ticker(tickerVal, date):
	try:
		with open(HISTORICAL_DATA.format(tickerVal), 'rb') as f:
			reader = csv.reader(f)
			your_list = list(reader)
		for x in your_list[1:]:
			if x[0] == date:
				return x[1]
	except Exception as exp:
		print exp
		return 0

def get_close_price_by_ticker(tickerVal, date):
	try:
		with open(HISTORICAL_DATA.format(tickerVal), 'rb') as f:
			reader = csv.reader(f)
			your_list = list(reader)
		for x in your_list[1:]:
			if x[0] == date:
				return x[4]
	except Exception as exp:
		print exp
		return 0

def get_diff_from_ticker(tickerVal):
	info = {}
	try:
		with open(HISTORICAL_DATA.format(tickerVal), 'rb') as f:
			reader = csv.reader(f)
			your_list = list(reader)
		your_list.pop(0)
		for x in your_list[TOTAL_DATES:]:
			#print x
			try:
				info[x[0]] = float(x[4]) - float(x[1])
			except:
				pass
	except:
		pass
	return info

def get_percent_diff_from_ticker(tickerVal):
	info = {}
	try:
		with open(HISTORICAL_DATA.format(tickerVal), 'rb') as f:
			reader = csv.reader(f)
			your_list = list(reader)
		your_list.pop(0)
		for x in your_list[TOTAL_DATES:]:
			#print x
			try:
				info[x[0]] = ((float(x[4]) - float(x[1])) / float(x[1])) * 100
			except:
				pass
	except:
		pass
	return info

def get_total_count_by_ticker(tickerVal):
	a = json.load(open("dataset/AllCounts.json"))
	return a[tickerVal]

def get_day_difference_between_utc(utcTime):
	a = datetime.datetime.now().date()
	b = convert_date(utcTime)
	delta = a - b
	return delta.days

def get_dates():
	sql_command = """SELECT dateVal FROM comments;"""
	totalCount = 0
	dates = []
	for val in set(db.run_command(sql_command)):
		dateVal = val[0]
		if dateVal not in dates:
			dates.append(dateVal)
	return dates

def get_total_count_dates(dateVal):
	sql_command = """SELECT count(body) FROM comments WHERE dateVal = '{}';""".format(dateVal)
	return db.run_command(sql_command)

def get_total_ticker_count_dates(tickerVal):
	a = json.load(open("dataset/totalByDate.json"))
	info = {}
	for key, val in a.iteritems():
		info[key] = 0
	sql_command = """SELECT dateVal, tickers FROM comments WHERE tickers LIKE '%{}%';""".format(tickerVal)
	for val in db.run_command(sql_command):
		dateVal = val[0]
		tickers = [x.upper() for x in val[1].split(",") if len(x) > 0]
		if tickerVal.upper() in tickers:
			info[dateVal] += 1
	return info

def calc_ratio_info(tickerVal):
	a = json.load(open("dataset/totalByDate.json"))
	info = {}
	for key, val in a.iteritems():
		info[key] = 0
	sql_command = """SELECT dateVal, tickers FROM comments WHERE tickers LIKE '%{}%';""".format(tickerVal)
	for val in db.run_command(sql_command):
		dateVal = val[0]
		tickers = [x.upper() for x in val[1].split(",") if len(x) > 0]
		if tickerVal.upper() in tickers:
			info[dateVal] += 1
	totalRatio = 0.0
	totalCount = 0
	for key, val in info.iteritems():
		ratio = float(info[key]) / float(a[key])
		totalRatio += ratio
		info[key] = ratio
		totalCount += 1
	return {"average": totalRatio / float(totalCount), "dates": info}

def calc_predicted_direction(tickerVal):
	a = json.load(open("dataset/totalByDate.json"))
	info = {}
	for key, val in a.iteritems():
		info[key] = 0
	sql_command = """SELECT dateVal, tickers FROM comments WHERE tickers LIKE '%{}%';""".format(tickerVal)
	for val in db.run_command(sql_command):
		dateVal = val[0]
		tickers = [x.upper() for x in val[1].split(",") if len(x) > 0]
		if tickerVal.upper() in tickers:
			info[dateVal] += 1
	totalRatio = 0.0
	totalCount = 0
	for key, val in info.iteritems():
		totalRatio += float(info[key]) / float(a[key])
		totalCount += 1
	averageVal = totalRatio / float(totalCount)
	trades = {}
	for key, value in a.iteritems():
		trades[key] = 0
	for key, value in info.iteritems():
		thisAvg = float(info[key]) / float(a[key])
		diffVal = thisAvg - averageVal
		if ((abs(float(diffVal)) / averageVal) * 100) < 25:
			trades[key] = 0
		else:
			if diffVal > 0:
				trades[key] = 1
			else:
				trades[key] = -1
	return trades

def get_count_by_ticker(tickerVal):
	# This is super hacky because the tickers are stored as a string like F,TSLA,ETC.
	sql_command = """SELECT tickers FROM comments WHERE tickers LIKE '%{}%';""".format(tickerVal)
	totalCount = 0
	for val in db.run_command(sql_command):
		tickers = [x.upper() for x in val[0].split(",") if len(x) > 0]
		if tickerVal.upper() in tickers:
			totalCount += 1
	return totalCount

def get_weekday_by_ticker(tickerVal):
	# This is super hacky because the tickers are stored as a string like F,TSLA,ETC.
	info = {}
	sql_command = """SELECT weekday, tickers FROM comments WHERE tickers LIKE '%{}%';""".format(tickerVal)
	totalVal = 0
	totalCount = 0
	for val in db.run_command(sql_command):
		weekday = str(val[0])
		tickers = [x.upper() for x in val[1].split(",") if len(x) > 0]
		if tickerVal.upper() in tickers:
			if weekday not in info:
				info[weekday] = 0
			info[weekday] += 1
	return info

def get_first_comment_with_ticker(tickerVal):
	sql_command = """SELECT created_utc, tickers FROM comments WHERE tickers LIKE '%{}%';""".format(tickerVal)
	largest_num = 0
	for val in db.run_command(sql_command):
		utcTime = str(val[0])
		tickers = [x.upper() for x in val[1].split(",") if len(x) > 0]
		if tickerVal.upper() in tickers:
			z = get_day_difference_between_utc(utcTime)
			if z > largest_num:
				largest_num = z
	return largest_num

def get_average_by_ticker(tickerVal):
	# This is super hacky because the tickers are stored as a string like F,TSLA,ETC.
	info = {}
	sql_command = """SELECT weekday, tickers FROM comments WHERE tickers LIKE '%{}%';""".format(tickerVal)
	totalVal = 0
	totalCount = 0
	for val in db.run_command(sql_command):
		weekday = str(val[0])
		tickers = [x.upper() for x in val[1].split(",") if len(x) > 0]
		if tickerVal.upper() in tickers:
			if weekday not in info:
				info[weekday] = 0
			info[weekday] += 1
	return info

'''
def get_sentiment_by_ticker(tickerVal):
	# This is super hacky because the tickers are stored as a string like F,TSLA,ETC.
	sql_command = """SELECT polarity, tickers FROM comments WHERE tickers LIKE '%{}%';""".format(tickerVal)
	totalVal = 0
	totalCount = 0
	for val in db.run_command(sql_command):
		sentiment = val[0]
		tickers = [x.upper() for x in val[1].split(",") if len(x) > 0]
		if tickerVal.upper() in tickers:
			totalVal += sentiment
			totalCount += 1
	if totalCount == 0:
		return 0
	return float(totalVal) / float(totalCount)
'''

def get_sentiment_by_ticker(tickerVal):
	a = json.load(open('dataset/sentimentByTicker.json'))
	for val in a:
		if val['ticker'] == tickerVal:
			return val['sentiment']

def get_average_upvotes_by_ticker(tickerVal):
	# This is super hacky because the tickers are stored as a string like F,TSLA,ETC.
	sql_command = """SELECT ups, tickers FROM comments WHERE tickers LIKE '%{}%';""".format(tickerVal)
	totalVal = 0
	totalCount = 0
	for val in db.run_command(sql_command):
		sentiment = val[0]
		tickers = [x.upper() for x in val[1].split(",") if len(x) > 0]
		if tickerVal.upper() in tickers:
			if sentiment != None:
				totalVal += sentiment
				totalCount += 1
	if totalCount == 0:
		return 0
	return float(totalVal) / float(totalCount)

def get_all_counts(sort=True, reverse=False):
	h = []
	g = json.load(open(ALL_COUNTS))
	for key, val in g.iteritems():
		h.append({'count': val, 'ticker': key})
	if sort == True:
		h = sorted(h, key=lambda k: k['count'])
	if reverse == True:
		h = h[::-1]
	return h

def get_yolo_comments():
	# This returns tickers that are used in "YOLO" comments
	sql_command = """SELECT tickers FROM comments WHERE body LIKE '%yolo%' AND tickers not NULL;"""

	tickers = []
	for val in db.run_command(sql_command):
		tickers += [x.upper() for x in val[0].split(",") if len(x) > 0]
	return tickers



STOCK_TICKERS = get_all_possible_tickers()
STOCK_TICKERS.remove("EDIT")

def read_csv(filename):
	# Reads the dataset with historical prices
	with open(filename, 'rb') as f:
		reader = csv.reader(f)
		return list(reader)

def get_sentiment(stringVal):
	# Replaces each ticker with TSLA as it's sentiment neutral
	z = re.findall('[A-Z]{1,4}|\d{1,3}(?=\.)|\d{4,}', stringVal)
	for val in set(z):
		stringVal = stringVal.replace(val, "TSLA")
	return TextBlob(stringVal)

def convert_date(dateVal):
	# Converts to format 2004-01-05
	dt = dp.parse(dateVal)
	return dt.date()

def get_weekday(dateVal):
	# Converts to format 2004-01-05
	dt = dp.parse(dateVal)
	return dt.weekday()

def extract_tickers(string):
	e = re.findall('[A-Z]{1,4}|\d{1,3}(?=\.)|\d{4,}', string)
	return list(set(e).intersection(set(STOCK_TICKERS)))

def isTicker(stringVal):
	if IS_TICKER.match(stringVal):
		return stringVal in set(STOCK_TICKERS)
	return False

def extract_buy_or_sell(string):
	info = {'puts': [], 'calls': [], 'buy': [], 'sell': []}
	# Extracts the words buy or sell from the comment
	for val in re.split("(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", string):
		# This splits the string into sentences
		allWords = re.findall("\w+", str(val))
		while len(allWords) > 0:
			word = allWords.pop(0)
			if re.match("[\W]?([Bb]uy)[\W]?", word):
				# This means it's the word buy
				tempList = []
				while len(allWords) > 0:
					newWord = allWords.pop(0)
					if isTicker(newWord):
						tempList.append(newWord)
					elif re.match("[\W]?([Pp]ut[s]?)[\W]?", newWord):
						if len(tempList) > 0:
							# This means a sentence like
							# put $5 in TSLA
							while len(tempList) > 0:
								info['puts'].append(tempList.pop())
							break

					elif re.match("[\W]?([Cc]all[s]?)[\W]?", newWord):
						if len(tempList) > 0:
							# This means a sentence like
							# call my friend to put $5 in TSLA
							while len(tempList) > 0:
								info['calls'].append(tempList.pop())
							break
				info['buy'] += tempList

			elif re.match("[\W]?[Ss]horting?[\W]?", word):
				while len(allWords) > 0:
					newWord = allWords.pop(0)
					if isTicker(newWord):
						info['sell'].append(newWord)
					else:
						break

			elif re.match("[\W]?([Ss]ell|[Ss]old|[Cc]los[(e|ing)]|[Ss]hort[s]?)[\W]?", word):
				# This means it's indicating they want to sell
				# Sell TSLA puts would be equivilant to a call
				tempList = []
				while len(allWords) > 0:
					newWord = allWords.pop(0)
					if isTicker(newWord):
						tempList.append(newWord)
					elif re.match("[\W]?([Pp]ut[s]?)[\W]?", newWord):
						if len(tempList) > 0:
							# This means a sentence like
							# put $5 in TSLA
							while len(tempList) > 0:
								info['calls'].append(tempList.pop())
							break

					elif re.match("[\W]?([Cc]all[s]?)[\W]?", newWord):
						if len(tempList) > 0:
							# This means a sentence like
							# call my friend to put $5 in TSLA
							while len(tempList) > 0:
								info['puts'].append(tempList.pop())
							break

					elif re.match("[Ss]hort[s]?", newWord):
						# IE closing out a short == buy
						if len(tempList) > 0:
							# This means a sentence like
							# call my friend to put $5 in TSLA
							while len(tempList) > 0:
								info['buy'].append(tempList.pop())
							break

				info['sell'] += tempList

			elif isTicker(word):
				tempList = [word]
				while len(allWords) > 0:
					newWord = allWords.pop(0)
					if isTicker(newWord):
						tempList.append(newWord)
					elif re.match("[\W]?([Pp]ut[s]?)[\W]?", newWord):
						if len(tempList) > 0:
							# This means a sentence like
							# put $5 in TSLA
							while len(tempList) > 0:
								info['puts'].append(tempList.pop())
							break

					elif re.match("[\W]?([Cc]all[s]?)[\W]?", newWord):
						if len(tempList) > 0:
							# This means a sentence like
							# call my friend to put $5 in TSLA
							while len(tempList) > 0:
								info['calls'].append(tempList.pop())
							break
				info['buy'] += tempList
	return info



def random_string(stringVal):
	# Should return float or int
	return float(stringVal)

def text_entropy(s):
	p, lns = Counter(s), float(len(s))
	return -sum( count/lns * math.log(count/lns, 2) for count in p.values())

def calc_words(stringVal):
	return stringVal.count(" ")

class DatasetProcess(object):
	def __init__(self, function, createNew=False, verbose=True, threads=1, saveAs=False):
		self.lock = threading.Lock()
		self.threads = threads
		# This is the lock for multithreading
		self.functionVal = function
		self.totalRuns = 0
		self.totalCount = 0
		self.results = {}
		self.totalTime = 0
		self.forumnData = {}
		self.saveAs = saveAs
		self.verbose = verbose

	def save(self, fileName):
		with open(fileName, 'w') as fp:
			json.dump(self.forumnData, fp)

	def run(self):
		with open(WSB_DATASET) as f:
			for i, line in enumerate(f):
				val = json.loads(line)
				dayVal = convert_date(val['created_utc'])
				if dayVal not in self.forumnData:
					self.forumnData[dayVal] = []
				self.forumnData[dayVal].append(self.functionVal(val['body']))
				if self.verbose == True:
					if i % 2000 == 0:
						print i
		if self.saveAs != False:
			self.save(self.saveAs)
		return self.forumnData

	def get_average(self):
		self.average = (float(self.totalCount) / float(self.totalRuns))
		return self.average

	def get_diff_from_average(self):
		self.average = (float(self.totalCount) / float(self.totalRuns))
		return [x - self.average for x in self.toReturn]

class MultiThread(object):
	def __init__(self, listOfObjects, function, threads=1):
		self.lock = threading.Lock()
		self.threads = threads
		self.totalLength = len(listOfObjects)
		# This is the lock for multithreading
		self.objects = [{'id': x, 'val': e} for x, e in enumerate(listOfObjects)]
		self.functionVal = function
		self.totalRuns = 0
		self.totalCount = 0
		self.results = {}
		self.totalTime = 0

	def run_single(self):
		while len(self.objects) > 0:
			self.lock.acquire()
			if len(self.objects) == 0:
				self.lock.release()
				break
			this_val = self.objects.pop()
			self.lock.release()
			returnVal = self.functionVal(this_val['val'])
			self.lock.acquire()
			self.totalRuns += 1
			self.totalCount += float(returnVal)
			self.lock.release()
			self.results[str(this_val['id'])] = returnVal
			self.toReturn = []

	def run_all(self):
		start = time.time()
		threads = [threading.Thread(target=self.run_single) for i in range(self.threads)]
		for thread in threads:
			thread.start()
		for thread in threads:
			thread.join()
		end = time.time()
		self.totalTime = end-start
		self.average = (float(self.totalCount) / float(self.totalRuns))
		self.toReturn = [self.results[str(i)] for i in range(self.totalLength)]
		return self.toReturn

	def get_average(self):
		self.average = (float(self.totalCount) / float(self.totalRuns))
		return self.average

	def get_diff_from_average(self):
		self.average = (float(self.totalCount) / float(self.totalRuns))
		return [x - self.average for x in self.toReturn]

def run_on_all(listOfStrings, function):
	a = MultiThread(listOfStrings, function, 20)
	function()

class Algo(object):
	"""docstring for Algo"""
	def __init__(self):
		self.days = []
		# These are the days in the dataset
		self.dataset = {}
		# These are the values of the dataset
		self.read_dataset()
		# Fills the dataset with info from the CSV
		#print self.dataset
		self.forumnData = {}
		# This contains the forumn dataset
		#self.read_forumn_data()
		# Reads the dataset

	def read_dataset(self, filename="vixcurrent.csv"):
		csvFile = read_csv(filename)
		# This is the csv file containing historical prices
		csvFile = csvFile[2:]
		# Removes the header columns
		for row in csvFile:
			# This gets the current dataset
			day = row[0]
			# This is the day value
			self.days.append(day)
			# Adds the day to the list of days
			self.dataset[day] = {}
			# This contains the information from each column
			for i, columnVal in enumerate(COLUMNS):
				# Iterates over each column
				self.dataset[day][columnVal] = float(row[i+1])
				# Assigns each value to the info dict

	def read_forumn_data(self, filename="/media/christopher/ssd/wsbData.json"):
		# This is the data from wallstreet bets
		# It populates the forumnData
		with open(filename) as f:
			for i, line in enumerate(f):
				val = json.loads(line)
				dayVal = convert_date(val['created_utc'])
				if dayVal not in self.forumnData:
					self.forumnData[dayVal] = []
				self.forumnData[dayVal].append(val)
				if i % 2000 == 0:
					print i

	def calc_diff_from_date(self, date, days):
		# Calculates the difference in values from a specified day onward
		# Ie: date=1/29/2004, days=7
		dayIndex = self.days.index(date)
		# This is the index of the inputted day
		info = {}
		for column in COLUMNS:
			# Goes over each column in the dataset
			currentVal = self.dataset[date][column]
			futureVal = self.dataset[self.days[dayIndex+days]][column]
			info[column] = currentVal - futureVal
		return info

	def calc_avg_from_date(self, date, days):
		# Calculates the average values from a specified day onward
		# Ie: date=1/29/2004, days=7
		dayIndex = self.days.index(date)
		# This is the index of the inputted day
		info = {}
		for column in COLUMNS:
			# Goes over each column in the dataset
			info[column] = []
		#print dayIndex
		for i in range(dayIndex, dayIndex+days):
			# Goes through each column in the dataset
			dayInfo = self.dataset[self.days[i]]
			# This is all the info for the current day
			for column in COLUMNS:
				# Goes over each column in the dataset
				info[column].append(dayInfo[column])
		for column in COLUMNS:
			# Goes through each column in the dataset
			info[column] = (sum(info[column]) / len(info[column]))
		return info

	def calculate_day_diff(self, date):
		# This calculates the daily change
		return (self.dataset[date]['close'] - self.dataset[date]['open'])

	def calc_for_all(self, functionVal):
		# This will run each day through a specific function
		returnVal = {}
		for val in self.days:
			# Iterates over each day
			 returnVal[val] = functionVal(val)
		return returnVal

	#def calc_forumn_frequency(self):

def calc_stock_ranking(tickerVal):
	for i, val in enumerate(get_all_counts(reverse=True)):
		if val['ticker'] == tickerVal:
			break
	return i

class Trade():
	"""docstring for Trade"""
	def __init__(self, ticker):
		self.ticker = ticker
		self.all_counts = get_all_counts(reverse=True)
		# Contains total counts by stock ticker
		# dict(count, ticker)
		self.overall_sentiment = get_sentiment_by_ticker(ticker)
		# This contains the overall sentiment towards the ticker
		self.total_count = get_total_count_by_ticker(ticker)
		# Contains the total amount of mentions for this ticker
		self.ticker_ranking = calc_stock_ranking(ticker)
		self.historical_data = get_diff_from_ticker(ticker)
		# Contains difference in open-close price for a given day
		# type (dict[date])
		self.percent_diff = get_percent_diff_from_ticker(ticker)
		# Percentage difference per day
		self.all_dates = DATES
		self.modified_dates = [x for x in self.all_dates if x in self.historical_data]
		if len(self.modified_dates) == 0:
			raise Exception("No Data for this stock")
		x = calc_ratio_info(ticker)
		# This calculates comment ratio for the ticker
		self.ratio_by_date = x['dates']
		# Comment ratio by date
		self.average_ratio = x['average']
		# This is the average comment ratio
		self.info_vals = []
		self.totalTrades = 0

	def short(self, date, amount, duration=0):
		#print("Shorting for {} days".format(duration))
		if duration > 0:
			open_amt = get_open_price_by_ticker(self.ticker, date)
			indexVal = self.modified_dates.index(date)
			if (indexVal + duration) >= len(self.modified_dates):
				close_date = self.modified_dates[-1]
			else:
				close_date = self.modified_dates[indexVal + duration]
			close_amt = get_close_price_by_ticker(self.ticker, close_date)
		else:
			open_amt = get_open_price_by_ticker(self.ticker, date)
			close_amt = get_close_price_by_ticker(self.ticker, date)
		#print("Start: {}".format(amount))
		#print("End: {}".format(amount + (amount * (-1*((float(close_amt) - float(open_amt)) / float(open_amt))))))
		increase = ((float(close_amt) - float(open_amt)) / float(open_amt))
		#print("Stock increase: {}%".format(increase))
		return amount + (amount * (-1*((float(close_amt) - float(open_amt)) / float(open_amt))))

	def long(self, date, amount, duration=0):
		#print("Long for {} days".format(duration))
		if duration > 0:
			#print("Duration")
			open_amt = get_open_price_by_ticker(self.ticker, date)
			indexVal = self.modified_dates.index(date)
			if (indexVal + duration) >= len(self.modified_dates):
				close_date = self.modified_dates[-1]
			else:
				close_date = self.modified_dates[indexVal + duration]
			close_amt = get_close_price_by_ticker(self.ticker, close_date)
		else:
			open_amt = get_open_price_by_ticker(self.ticker, date)
			close_amt = get_close_price_by_ticker(self.ticker, date)
		return amount + (amount * ((float(close_amt) - float(open_amt)) / float(open_amt)))
		#return amount + (amount * ((self.percent_diff[date])*.01))

	def calc_buy_and_hold(self, balance):
		a = get_open_price_by_ticker(self.ticker, self.modified_dates[0])
		b = get_close_price_by_ticker(self.ticker, self.modified_dates[-1])
		return balance + (balance * ((float(b) / float(a)) / float(a)))

	def test_strategy(self, function, balance):
		goingLongBalance = balance
		info = function(self)
		dayDelay = info.get('delay', 0)
		# Defaults to 0 delay
		totalTrades = 0
		self.info_vals = []
		totalShares = goingLongBalance / float(get_open_price_by_ticker(self.ticker, self.modified_dates[dayDelay]))
		for i in range(dayDelay, len(self.modified_dates)):
			indicatorDay = self.modified_dates[i-dayDelay]
			tradeDay = self.modified_dates[i]
			tradeType = info['trades'][indicatorDay].get('trade')
			if tradeType != None:
				if info['trades'][indicatorDay].get("completed", False) == False:
					totalTrades += 1
					if tradeType == 'short':
						e = i
						duration = 0
						while e < len(self.modified_dates):
							tempIndicatorDay = self.modified_dates[e-dayDelay]
							tempTradeType = info['trades'][tempIndicatorDay].get('trade')
							if tempTradeType == "long":
								info['trades'][tempIndicatorDay]["completed"] = True
								duration += 1
							else:
								break
							e += 1
						balance = self.short(tradeDay, balance, duration)
					elif tradeType == 'long':
						e = i
						duration = 0
						while e < len(self.modified_dates):
							tempIndicatorDay = self.modified_dates[e-dayDelay]
							tempTradeType = info['trades'][tempIndicatorDay].get('trade')
							if tempTradeType == "long":
								info['trades'][tempIndicatorDay]["completed"] = True
								duration += 1
							else:
								break
							e += 1
						balance = self.long(tradeDay, balance, duration)
			goingLongBalance = totalShares * float(get_close_price_by_ticker(self.ticker, self.modified_dates[i]))
			self.info_vals.append({"date": self.modified_dates[i], "long_balance": goingLongBalance, "strategy_balance": balance})
		print("Total Trades: {}".format(totalTrades))
		self.totalTrades = totalTrades
		return balance

	def get_more_info(self):
		return self.info_vals






if __name__ == '__main__':
	#a = Algo()
	#print a.calc_diff_from_date('1/5/2004', 7)
	#a.calc_for_all(a.calculate_day_diff)
	#print len(a.forumnData)
	#message = """you should buy TSLA.  Maybe even AMD if you feel like it."""
	#message = """buying TSLA calls and maybe AMD if I feel like it"""
	#message = """closing out my TSLA shorts"""
	#message = """short TSLA probably or put put AMD call"""
	#message = """dude i don't even know"""
	#e = re.compile("[\W]?([Bb]uy|[Ss]ell)[\W]?")
	#if e.match('bestbuy'):
	#	print("Found")
	'''for message in open("dataset/onlyComments.txt").read().split("\n"):

					if len(message) > 0:
						f =  extract_buy_or_sell(message)
						if len(message) < 100:
							totalCount = 0
							for key, val in f.iteritems():
								totalCount += len(val)
							if val > 0:
								print("{} | {}".format(message, f))'''
	#print isTicker("BARH")
	#newWord = "puts"
	#print re.match("[\W]?([Pp]ut[s]?)[\W]?", newWord)
	#listOfObjects = range(1,100)
	#objectVal = [{'id': x, 'val': e} for x, e in enumerate(listOfObjects)]
	#print objectVal
	'''c = open("comments.txt").read().split("\n")
				a = MultiThread(c, calc_words)
				g = a.run_all()
				print g
				print a.get_diff_from_average()
				print a.totalTime'''
	#a = MultiThread([str(i) for i in range(0,101)], random_string)
	#b = a.run_all()
	#print a.get_diff_from_average()
	#print b
	#print get_diff_from_ticker("MU")
	a = Trade("TSLA")
	for key, value in a.ratio_by_date.iteritems():
		print("{} - {}".format(value, a.average_ratio))
