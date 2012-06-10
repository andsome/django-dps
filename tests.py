import unittest
import dps
from os import environ
from datetime import timedelta, date
import re
from urlparse import urlparse, parse_qs

class TestKeyValidation(unittest.TestCase):
	def setUp(self):
		self.gateway = dps.PXPayGateway(environ['PXPAY_USERID'], environ['PXPAY_KEY'], 'http://example.com/success', 'http://example.com/failure')

	def test_long_key_validation(self):
		long_key = '5bd74c629d33a271d2cee8d188d78ffb5ba91ef43a1de7d492cee8d188d8d78ffb5bd74c629d33a2'
		
		self.assertRaises(dps.InvalidPXPayKeyError, dps.PXPayGateway, 'user_id', long_key, 'http://example.com/success', 'http://example.com/failure')
	
	def test_short_key_validation(self):
		short_key = '456af23'
		
		self.assertRaises(dps.InvalidPXPayKeyError, dps.PXPayGateway, 'user_id', short_key, 'http://example.com/success', 'http://example.com/failure')
	
	def test_invalid_key_validation(self):
		invalid_chars_key = 'g8r7d492cek8d188d58cfb5bd74c629e33a271d fd6a82ee0+d4a91ef43a0de7'

		self.assertRaises(dps.InvalidPXPayKeyError, dps.PXPayGateway, 'user_id', invalid_chars_key, 'http://example.com/success', 'http://example.com/failure')
	
	def test_invalid_amount(self):
		self.assertRaises(ValueError, self.gateway.process_payment, -1.0, 'Payment')
		
	def test_invalid_merchant_reference(self):
		self.assertRaises(ValueError, self.gateway.process_payment, 1.0, 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
	
	def test_invalid_currency(self):
		self.assertRaises(ValueError, self.gateway.process_payment, 1.0, 'Payment', currency='BAD')
	
	def test_invalid_billing_id(self):
		self.assertRaises(ValueError, self.gateway.process_payment, 1.0, 'Payment', billing_id='Anything')
		
	def test_invalid_email_address(self):
		self.assertRaises(ValueError, self.gateway.process_payment, 1.0, 'Payment', email_address='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
		
	def test_invalid_txn_data_str(self):
		self.assertRaises(ValueError, self.gateway.process_payment, 1.0, 'Payment', txn_data_1='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
		
		self.assertRaises(ValueError, self.gateway.process_payment, 1.0, 'Payment', txn_data_2='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
		
		self.assertRaises(ValueError, self.gateway.process_payment, 1.0, 'Payment', txn_data_3='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
		
	def test_invalid_txn_data(self):
		self.assertRaises(ValueError, self.gateway.process_payment, 1.0, 'Payment', txn_data_1={'foo': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'})

		self.assertRaises(ValueError, self.gateway.process_payment, 1.0, 'Payment', txn_data_2={'foo': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'})
		
		self.assertRaises(ValueError, self.gateway.process_payment, 1.0, 'Payment', txn_data_3={'foo': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'})
		
	def test_invalid_opt(self):
		self.assertRaises(ValueError, self.gateway.process_payment, 1.0, 'Payment', opt='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
	
	def test_transaction(self):
	
		txn_data_1 = {'txn_data_1_1': 'one', 'txn_data_1_2': 'two'}
		txn_data_2 = ['one', 'two', 'three']
		txn_data_3 = 'Transaction Data Three'
	
		pay_url = self.gateway.process_payment( 1.0, 'Payment', txn_data_1=txn_data_1, txn_data_2=txn_data_2, txn_data_3=txn_data_3)
	
		self.assertIsInstance(pay_url, str)
		
		try:
			import mechanize
		except ImportError:
			print "\nCan't test payment processing as mechanize is not installed.\n"
			return
				
		br = mechanize.Browser()
		
		def dotrue(*args, **kwargs):
			return True
		
		br.open(pay_url)
		
		br.viewing_html = dotrue
		
		br.select_form(name='PmtEnt')
		
		t = date.today() + timedelta(days=365)
		
		br['CardNum'] = '4111111111111111'
		br['ExMnth'] = t.strftime('%m')
		br['ExYr'] = t.strftime('%y')
		br['NmeCard'] = 'TEST CARD'
		br['Cvc2'] = '123'
		
		br.form.action = re.sub(r'\s+', '', br.form.action)
				
		#response2 = 
		br.submit()
		
		result_url_str = None
		
		for link in br.links():
			for attr in link.attrs:
				if attr[0] == 'class':
					if attr[1] == '2':
						result_url_str = link.url
						break
						
		self.assertIsNotNone(result_url_str)
		
		result_url = urlparse(result_url_str)
		
		query_dict = parse_qs(result_url.query)
		
		result_code = query_dict['result'][0]
		
		self.gateway.process_response(result_code)
			
		self.assertEqual(txn_data_1, self.gateway.txn_data_1)
		self.assertEqual(txn_data_2, self.gateway.txn_data_2)
		self.assertEqual(txn_data_3, self.gateway.txn_data_3)
if __name__ == '__main__':
	unittest.main()