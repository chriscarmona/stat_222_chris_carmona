
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import urllib
import zipfile

from lxml import etree
from scipy.interpolate import interp1d
from datetime import datetime, timedelta
from matplotlib.backends.backend_pdf import PdfPages

# Data directory #
data_dir = '/Users/Chris/Documents/26 UC Berkeley/03 Courses/STAT 222/stat_222_chris_carmona/data/'
out_dir = '/Users/Chris/Documents/26 UC Berkeley/03 Courses/STAT 222/stat_222_chris_carmona/output/'

# Portfolio file #
port_file = 'port_2013-12.csv'

# Portfolio #
port = pd.read_csv( data_dir + port_file , na_values=['','NA','na','NaN','NULL'] )

port = pd.Series(port.position.values,index=port.id_instr)

# fixed-income instruments cashflows #
cshf_info_file = 'instr_cashflows.csv'
cshf_info = pd.read_csv( data_dir + cshf_info_file , na_values=['','NA','na','NaN','NULL'] )
cshf_info['Date'] = pd.to_datetime(cshf_info['Date'])
cshf_info = cshf_info.groupby(['id_instr','Date'])['value'].sum()

# instruments description #
instr_info_file = 'instr_description.csv'
instr_info = pd.read_csv( data_dir + instr_info_file , na_values=['','NA','na','NaN','NULL'] )

currencies = ['AUD', 'CAD', 'CHF', 'CLP', 'EUR', 'GBP', 'JPY', 'NOK', 'NZD', 'SEK', 'SGD']
# Flip all currencies to dollars per curency
cur_usd = ['AUD', 'EUR', 'GBP', 'NZD']
cur_flip = list(set(currencies).difference(set(cur_usd)))


nodes = np.array([1,3,6],dtype=np.float64)
nodes = nodes/12
nodes = np.append(nodes, np.array([1,2,3,5,7,10,20,30],dtype=np.float64) )
nodes_names = ['GOVT_USD_USA_1m','GOVT_USD_USA_3m','GOVT_USD_USA_6m',
               'GOVT_USD_USA_1y','GOVT_USD_USA_2y','GOVT_USD_USA_3y',
               'GOVT_USD_USA_5y','GOVT_USD_USA_7y','GOVT_USD_USA_10y',
               'GOVT_USD_USA_20y','GOVT_USD_USA_30y']

def port_valuation( port, calc_date, risk_factors, instr_info, cshf_info):
    # Cash flows for bonds
    bonds_cshf = cshf_info.ix[ port.index.values ].unstack('id_instr')
    bonds_cshf = bonds_cshf[bonds_cshf.index>=calc_date]
    bonds_cshf = bonds_cshf/1000000
    bonds_cshf = bonds_cshf * port[bonds_cshf.columns]
    
    # Cash flows for currencies
    ccy_cshf = port[currencies].dropna()
    ccy_cshf = pd.DataFrame( ccy_cshf.values, index=ccy_cshf.index, columns=[calc_date] ).T
    if 'USD' in port.index:
        ccy_cshf['USD'] = port['USD']
    
    # cashflows for all the portfolio
    port_cshf = pd.merge( ccy_cshf, bonds_cshf, left_index=True, right_index=True, how='outer' )
    port_cshf.dropna( how='all' )
    
    # Discount factors calculation
    discount = pd.Series( np.array(risk_factors[nodes_names].values) ,
                         index=[ calc_date + pd.DateOffset(days=x*365) for x in nodes ] )
    discount = np.exp(-discount * nodes)
    discount = discount.set_value(calc_date, 1)
    discount = discount.reindex( index= discount.index.append(port_cshf.index).unique() )
    discount = discount.sort_index()
    discount = discount.interpolate(method="time")
    discount = discount.reindex( index=port_cshf.index)
    
    # present value
    port_cshf_pv = discount * port_cshf
    
    # present value in USD
    ccy_instr = instr_info.ix[ instr_info.id_instr.isin(port.index), ['id_instr','currency']]
    ccy_instr = ccy_instr.set_index('id_instr').currency
    
    #print port_cshf_pv.ix[:1,"JPY"]
    
    for ccy in ccy_instr[ ccy_instr != 'USD' ].unique():
        instr_ccy = ccy_instr[ccy_instr == ccy].index.values
        if ccy in cur_flip:
            port_cshf_pv[instr_ccy] = port_cshf_pv[instr_ccy] / risk_factors[ccy]
        else:
            port_cshf_pv[instr_ccy] = port_cshf_pv[instr_ccy] * risk_factors[ccy]
    
    #print port_cshf_pv.ix[:1,"JPY"]
    port_mtm_value = port_cshf_pv.sum(axis=0)[port.index]
    return port_mtm_value

def test_3():
    risk_factors_test = pd.Series( [1.5]*len(currencies) ,
                                  index=currencies)
    port_test = pd.Series( [1000]*len(currencies) ,
                                  index=currencies)
    
    port_mtm_base = port_valuation(port=port_test,
                                   calc_date=datetime.strptime('2013-12-30','%Y-%m-%d'),
                                   risk_factors=risk_factors_test,
                                   instr_info=instr_info,
                                   cshf_info=cshf_info )
    result = all(port_mtm_base[cur_flip] == 1000/1.5) and all(port_mtm_base[cur_usd] == 1000*1.5)
    
    print 'Checking currency valuation:', result
    assert result == True


def test_4():
    risk_factors_test = pd.Series( nodes * 0.05 ,
                                  index=nodes_names)
    port_test = pd.Series( [1000] ,
                                  index=['US912796BU23','US912796BV06'])
    
    port_mtm_base = port_valuation(port=port_test,
                                   calc_date=datetime.strptime('2013-12-30','%Y-%m-%d'),
                                   risk_factors=risk_factors_test,
                                   instr_info=instr_info,
                                   cshf_info=cshf_info )
    
    result = all( np.array( [round(i,4) for i in port_mtm_base] ) ==  np.array( [999.8060, 999.7261] ) )
    print 'Checking Bonds valuation:', result
    assert result == True