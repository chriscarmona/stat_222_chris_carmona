
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

def zero_from_yield_bootstrap( ytm_curve , nodes ):

    nodes_old = nodes.copy()
    nodes = np.append(0,nodes)
    ytm_curve = np.append(0,ytm_curve)
    
    nodes_new = np.arange(0,max(nodes)+0.5,0.5)
    nodes_new = np.append(nodes,nodes_new)
    nodes_new = np.sort(nodes_new)
    nodes_new = np.unique(nodes_new)
        
    f = interp1d(nodes, ytm_curve, kind='linear')
    ytm_new = f(nodes_new)
    ytm_new[0]=0
    
    ytm_new = pd.Series(ytm_new,index=nodes_new)
    zero_new = np.zeros_like(ytm_new)
    
    nodes_coupon = np.in1d(nodes_new,np.arange(0,max(nodes),0.5)+0.5)
    
    for node_i in nodes_new[nodes_coupon==False]:
        zero_new[node_i] = (1+ytm_new[node_i]*node_i) ** (1/node_i)-1
    zero_new[0] = 0
    
    
    for node_i in nodes_new[nodes_coupon]:
        cpn_i = ytm_new[node_i]/2
        zero_new[node_i] = - np.log( (1 - cpn_i * np.exp(-nodes_new[ nodes_new<node_i * nodes_coupon ] * zero_new[ nodes_new<node_i * nodes_coupon ]).sum())/(1+cpn_i) ) * (1/node_i)

        
    return zero_new[np.in1d(nodes_new,nodes_old)].values

def test_2():
    nodes = np.array(range(1,31),dtype=np.float64)
    ytm_curve_test = pd.Series( np.zeros_like(nodes)+0.05 , index=nodes)
    zero_curve_test = zero_from_yield_bootstrap( ytm_curve=ytm_curve_test.values , nodes=nodes )
    zero_curve_test = np.array( [ round(rate, 2) for rate in zero_curve_test ],dtype=np.float64)
    result = all( ytm_curve_test == zero_curve_test )
    
    print 'Checking zero rates:', result
    assert result == True

test_2()