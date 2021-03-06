import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import sys
from sqlalchemy import create_engine
import psycopg2
sys.path.append('../..')
from spiders import *

class visual:

	def __init__(self):
		self.engine = create_engine('postgresql://pi:password@192.168.1.185:5432/amazon')
		
		query = '''SELECT * FROM Shaver; '''
		self.df = pd.read_sql(query,self.engine)
		#self.hostname = '192.168.1.185'
		#self.username = 'pi'
		#self.password = 'password'
		#self.database='amazon'
		self.labels = ''
		self.pp = PdfPages('{}.pdf'.format(searchquery.searchitem.replace(' ','_')))
		#self.conn = psycopg2.connect(host = self.hostname,database=self.database,user=self.username, password=self.password, port = 5432)
		#self.conn.autocommit = True
		#self.cursor = self.conn.cursor()
	

	def close_database(self):
		self.engine.dispose()
		self.pp.close()
		#self.cursor.close()
		#self.conn.close()
	
	def price_range(self):
		df = self.df.replace(0, np.NaN)
		mean = df['price'].mean()
		small_bins = [0.001,10,25,50,75,100,200,300]
		medium_bins = [0.001,50,100,150,200,250,300,400]
		big_bins = [0.001,100,250,500,750,1000,2000,3000]
		final_bins = []
		if mean <= 200:
			final_bins = small_bins
			above_price = [len(df.loc[df['price'] > 300])]
		elif mean > 300 and df['price'].mean() <= 500 :
			final_bins = medium_bins
			above_price = [len(df.loc[df['price'] > 400])]
		else:
			final_bins = big_bins
			above_price = [len(df.loc[df['price'] > 3000])]
			
		sizes = list(df['price'].value_counts(bins=final_bins).sort_index(ascending=True)) + above_price
		labels = ['Under $'+str(final_bins[1]),'\$'+str(final_bins[1])+' - \$' + str(final_bins[2]),'\$'+str(final_bins[2])+' - \$' + str(final_bins[3]),'$'+str(final_bins[3])+' - \$' + str(final_bins[4]),'$'+str(final_bins[4])+' - \$' + str(final_bins[5]),'\$'+str(final_bins[5])+' - \$' + str(final_bins[6]),'\$'+str(final_bins[6])+' - \$' + str(final_bins[7]),'\$'+str(final_bins[7])+' & Above']
		for index,val in enumerate(sizes):
			if val <=0:
				del sizes[index]
				del labels[index]
		
		for index,val in enumerate(sizes):
			labels[index] = labels[index] + ' (' + "{:.2%}".format(val/sum(sizes)) + ')'

		patches, texts = plt.pie(sizes, startangle=90)

		plt.legend(patches, labels, loc="best",fontsize=20)
		plt.title('Price Range\n\n Average Price: $' + str(np.around(mean, decimals=2)))

		plt.axis('equal')
		plt.tight_layout()
		
		plt.gcf().set_size_inches(20,16)
		plt.savefig(self.pp, format='pdf')

	def clean_brand(self):
		df = self.df.replace('n/a',np.NaN)
		for holder in df['brand']:
			for index,values in enumerate(df['brand']):
				if str(holder).lower() in str(values).lower():
					df.at[index,'brand']= str(holder).upper()
		self.df = df.replace('NAN',np.NaN)
		
	def brand(self):
		self.clean_brand()
		df = self.df
		brand = dict(df['brand'].value_counts(ascending=False))			
		total_brand = sum(brand.values())
		top = 20
		try:
			sizes = list(brand.values())[:top]
			labels = list(brand.keys())[:top]
		except:
			sizes = brand.values()
			labels = brand.keys()
			top = len(brand.values())

		for index,val in enumerate(sizes):
			if val <=0:
				del sizes[index]
				del labels[index]
				
		self.labels = labels.copy()
		for index,val in enumerate(sizes):
			labels[index] = labels[index] + ' (' + "{:.2%}".format(val/total_brand) + ')'
		
		patches, texts = plt.pie(sizes, startangle=90)
		plt.legend(patches, labels, loc="best",fontsize=20)
		plt.title('Top '+ str(top) +' brands\n\n Total # of brands: ' + str(len(brand)))
		plt.axis('equal')
		plt.tight_layout()

		plt.gcf().set_size_inches(20,16)
		plt.savefig(self.pp, format='pdf')


	def insert_data_labels(self,bars,ax):
		for bar in bars:
			bar_height = bar.get_height()
			ax.annotate('{0:.0f}'.format(bar.get_height()),
				xy=(bar.get_x() + bar.get_width() / 2, bar_height),
				xytext=(0, 3),
				textcoords='offset points',
				ha='center',
				va='bottom'
)

	def reviews(self):
		df =self.df
		labels = self.labels.copy()
		df = df.groupby(['brand'])['reviews'].agg([np.sum,np.mean])
		dataset = df.loc[labels] 

		index = np.arange(len(labels))
		maxx = int(dataset['sum'].values.astype(int).max())
		total = dataset['sum'].values.astype(int).tolist()
		mean = dataset['mean'].values.round(0).astype(int).tolist()

		y_axis = np.arange(0, maxx, 10000)
		bar_width = 0.5

		fig,ax = plt.subplots(figsize=(20, 16))

		barTotal = ax.bar(index - bar_width/2, total,bar_width,label='sum of reviews')
		barmean = ax.bar(index + bar_width/2, mean,bar_width,label='average of reviews')
		plt.tick_params(axis='x', which='major', labelsize=8)
		plt.tight_layout()
		ax.set_xticks(index)	
		ax.set_xticklabels(labels)
		plt.title('Top {} brands total & average reviews'.format(len(labels)))
		ax.set_yticks(y_axis)
		ax.set_yticklabels(y_axis)
		ax.legend()
		self.insert_data_labels(barTotal,ax)
		self.insert_data_labels(barmean,ax)
		plt.tight_layout()
		plt.savefig(self.pp, format='pdf')
		

if __name__ == "__main__":
	obj = visual()
	obj.price_range()
	obj.brand()
	obj.reviews()
	obj.close_database()

