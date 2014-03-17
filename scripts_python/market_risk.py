import numpy as np
import pandas as pd
from lxml import etree
import urllib
import zipfile

# Data directory #
data_dir = '/Users/Chris/Documents/26 UC Berkeley/03 Courses/STAT 222/stat_222_chris_carmona/data/'
port_date = '.csv'

# Portfolio #
port_file = 'port_2013-12.csv'
port = pd.read_csv( data_dir + port_file , na_values=['','NA','na','NaN','NULL'] )

port

url = 'http://www.treasury.gov/resource-center/data-chart-center/interest-rates/pages/XmlView.aspx?data=yieldyear&year=2013'

urllib.urlretrieve(url, data_dir+"yields.xml")

##### Loading xml file #####

doc = etree.parse(data_dir+"yields.xml")
# root element: 254 elements
root = doc.getroot()

rates_data = {}
for entries in root.findall('{http://www.w3.org/2005/Atom}entry'):
    for content_i in entries.find('{http://www.w3.org/2005/Atom}content'):
        row_i = {}
        for property_i in content_i.getchildren():
            if property_i.tag.replace('{http://schemas.microsoft.com/ado/2007/08/dataservices}','')=="NEW_DATE":
                date_i = property_i.text.replace("T00:00:00","")
            else:
                row_i[ property_i.tag.replace('{http://schemas.microsoft.com/ado/2007/08/dataservices}','') ] = property_i.text
        rates_data[date_i]=row_i

#DATE=pd.DataFrame(rates_data).NEW_DATE.astype(np.string_)
#DATE=pd.to_datetime( DATE )
#rates_data = pd.DataFrame(rates_data,index=DATE)
#rates_data[:3]

rates_data = pd.DataFrame(rates_data)
rates_data = rates_data.T
rates_data = rates_data.drop(['BC_30YEARDISPLAY','Id'],axis=1)
rates_data.rename( columns={#'NEW_DATE':'DATE',
                  'BC_1MONTH':'GOVT_USD_USA_1m',
                  'BC_3MONTH':'GOVT_USD_USA_3m',
                  'BC_6MONTH':'GOVT_USD_USA_6m',
                  'BC_1YEAR':'GOVT_USD_USA_1y',
                  'BC_2YEAR':'GOVT_USD_USA_2y',
                  'BC_3YEAR':'GOVT_USD_USA_3y',
                  'BC_5YEAR':'GOVT_USD_USA_5y',
                  'BC_7YEAR':'GOVT_USD_USA_7y',
                  'BC_10YEAR':'GOVT_USD_USA_10y',
                  'BC_20YEAR':'GOVT_USD_USA_20y',
                  'BC_30YEAR':'GOVT_USD_USA_30y',
                  },
                  inplace=True)

rates_data = rates_data.convert_objects(convert_numeric=True)
rates_data = rates_data.divide(100)
rates_data

url_zip = 'http://www.federalreserve.gov/datadownload/Output.aspx?rel=H10&filetype=zip'

##### Download zip file with data #####

#import urllib
urllib.urlretrieve(url_zip, data_dir+"ccy.zip")

#import zipfile
zip_file = open(data_dir+'ccy.zip', 'rb')
z = zipfile.ZipFile(zip_file)
#print z.namelist()
z.extract('H10_data.xml', data_dir)


##### Loading xml file #####

doc = etree.parse(data_dir+'H10_data.xml')
# root element: 254 elements
root = doc.getroot()

data_set = root.find('{http://www.federalreserve.gov/structure/compact/common}DataSet')
series = data_set.findall('{http://www.federalreserve.gov/structure/compact/H10_H10}Series')

currencies = ['AUD', 'CAD', 'CHF', 'CLP', 'CNY', 'EUR', 'GBP', 'JPY', 'NOK', 'NZD', 'SEK', 'SGD']

ccy_data = {}
for serie in series:
    #    print serie.attrib['FX'] + ' ' + serie.attrib['CURRENCY'] + ' ' + serie.attrib['UNIT'] + ' ' + serie.attrib['FREQ']
    if serie.attrib['FX'] in currencies and serie.attrib['FREQ']=='9':
        #        print serie.attrib['FX'] + ' ' + serie.attrib['CURRENCY'] + ' ' + serie.attrib['UNIT'] + ' ' + serie.attrib['FREQ']
        row_i = {}
        for obs in serie.findall('{http://www.federalreserve.gov/structure/compact/common}Obs'):
            row_i[ obs.attrib['TIME_PERIOD'] ] = obs.attrib['OBS_VALUE']
        ccy_data[serie.attrib['FX']]=row_i

ccy_data = pd.DataFrame(ccy_data)
ccy_data = ccy_data.convert_objects(convert_numeric=True)
ccy_data

all_data = pd.merge( ccy_data, rates_data, right_index=True, left_index=True,how='outer')

all_data_complete = all_data.dropna()

all_data_complete

# Global databases #

# instruments description #
instr_info_file = 'instr_description.csv'
instr_info = pd.read_csv( data_dir + instr_info_file , na_values=['','NA','na','NaN','NULL'] )

# Risk factors description #
curves_info_file = 'curve_nodes_description.csv'
curves_info = pd.read_csv( data_dir + curves_info_file , na_values=['','NA','na','NaN','NULL'] )

# fixed-income instruments cashflows #
cshf_info_file = 'instr_cashflows.csv'
cshf_info = pd.read_csv( data_dir + cshf_info_file , na_values=['','NA','na','NaN','NULL'] )


rtn_data = all_data_complete.copy(deep=True)

# Flip all currencies to dollars per curency
cur_usd = ['AUD', 'EUR', 'GBP', 'NZD']
cur_flip = list(set(currencies).difference(set(cur_usd)))
for cur in cur_flip:
    if cur in rtn_data.columns:
        #        print cur
        rtn_data[cur] = 1/rtn_data[cur]

# Get rid of negative and zero values
rtn_data[rtn_data<=0] = float('NaN')
rtn_data = rtn_data.dropna()

# Calculate log-returns
rtn_data = rtn_data.apply(np.log)
rtn_data = rtn_data - rtn_data.shift(1)
rtn_data = rtn_data.dropna()

##################################################

# EWMA function
def ewma(X,lambda):
    sigma=X.values
    X.values

rtn_data.values

