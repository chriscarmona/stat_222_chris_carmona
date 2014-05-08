
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

def test_1():

    instr_name_len = np.array( [ len(i) for i in  port.index.values ] )
    instr_port = port.index.values[ instr_name_len == 12 ]
    
    instr_port_defined = [ (i in cshf_info.unstack().index.values) for i in instr_port ]
    
    result = all(instr_port_defined) 
    print 'Checking all instruments cashflows defined:', result
    assert result == True

test_1()