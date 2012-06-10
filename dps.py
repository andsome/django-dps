import urllib2
import re
import simplejson
from xml.etree.ElementTree import Element, SubElement, tostring, parse

__version__ = '1.1'

PXPOSTURL = 'https://sec.paymentexpress.com/pxpay/pxaccess.aspx'
DEFAULT_CURRENCY = 'NZD'
CURRENCIES = ('CAD', 'CHF', 'DKK', 'EUR', 'FRF', 'GBP', 'HKD', 'JPY', 'NZD', 'SGD', 'THB', 'USD', 'ZAR', 'AUD', 'WST', 'VUV', 'TOP', 'SBD', 'PNG', 'MYR', 'KWD', 'FJD')

def clean_transaction_data(transaction_data):
	"""Cleans data for TXNData1, TXNData2 and TXNData3. Non-strings are attempted to be converted to JSON. This function is not intended to be called directly by the user."""
	if type(transaction_data) != str:
		transaction_data = simplejson.dumps(transaction_data)
				
	if len(transaction_data) > 255:
		raise ValueError('Transaction Data 1 must be <= 255 characters long.')
		
	return transaction_data

class InvalidPXPayUserError(ValueError):
	"""Raised if a user ID that looks invalid is entered. Not validated against DPS."""
	pass

class InvalidPXPayKeyError(ValueError):
	"""Raised if a key that looks invalid is entered. Not validated against DPS.""" 
	pass

class InvalidCurrencyError(ValueError):
	"""Raised in an unknown currency code is used. See DPS website for valid currencies."""
	pass

class PXPayPaymentError(ValueError):
	"""Raised if DPS denies the transaction."""
	pass

class PXPayGateway(object):
	"""Class for processing credit card payments through the DPS PXPay Gateway."""
	def __init__(self, user_id, key, success_url=None, failure_url=None, post_url=PXPOSTURL):
		if len(user_id) > 32:
			raise InvalidPXPayUserError('PXPay User ID must be 32 chars or less.')
		
		self.user_id = user_id
		
		if not re.match('^([a-f0-9]{64})$', key):
			raise InvalidPXPayKeyError('PXPay Key is not 64 char hex.')
		
		self.key = key
		self.success_url = success_url
		self.failure_url = failure_url
		self.post_url = post_url
		
	def process_payment(self, amount, merchant_reference, txn_type='Purchase', currency=DEFAULT_CURRENCY, txn_id=None, billing_id=None, email_address=None, enable_add_bill_card=False, txn_data_1=None, txn_data_2=None, txn_data_3=None, opt=None):
		"""Initiate a PXPay transaction, and return the URI of the payment page for the client to be redirected to."""
		
		if enable_add_bill_card == False and billing_id != None:
			raise ValueError('billing_id must be None if enable_add_bill_card is False')
		
		generate_request = Element('GenerateRequest')
		
		SubElement(generate_request, 'PxPayUserId').text = self.user_id
		SubElement(generate_request, 'PxPayKey').text = self.key
		
		if amount < 0:
			raise ValueError('The amount to charge must not be negative.')
		
		SubElement(generate_request, 'AmountInput').text = '%.2f' % amount
		
		if currency == None:
			currency = DEFAULT_CURRENCY
		
		if not currency in CURRENCIES:
			raise InvalidCurrencyError('Currency %s is not valid.' % currency) 
		
		SubElement(generate_request, 'CurrencyInput').text = currency
		
		if len(merchant_reference) > 64:
			raise ValueError('Merchant Reference must be <= 64 chars.')
		
		SubElement(generate_request, 'MerchantReference').text = merchant_reference
		SubElement(generate_request, 'TxnType').text = txn_type
		SubElement(generate_request, 'UrlSuccess').text = self.success_url
		SubElement(generate_request, 'UrlFail').text = self.failure_url
		
		if enable_add_bill_card:
			SubElement(generate_request, 'EnableAddBillCard').text = '1'
			
			if billing_id:
				if len(billing_id) > 32:
					raise ValueError('billing_id must be <= 32 chars.')
			
				SubElement(generate_request, 'BillingId').text = billing_id
				
		if email_address:
			if len(email_address) > 255:
				raise ValueError('Email address must be <= 255 chars.')
		
			SubElement(generate_request, 'EmailAddress').text = email_address
			
		if txn_data_1:
			txn_data_1 = clean_transaction_data(txn_data_1)
			SubElement(generate_request, 'TxnData1').text = txn_data_1
			
		if txn_data_2:
			txn_data_2 = clean_transaction_data(txn_data_2)
			SubElement(generate_request, 'TxnData2').text = txn_data_2
			
		if txn_data_3:
			txn_data_3 = clean_transaction_data(txn_data_3)
			SubElement(generate_request, 'TxnData3').text = txn_data_3
			
		if txn_id:
			if len(txn_id) > 16:
				raise ValueError('Transaction ID must be <= 16 chars.')
			
			SubElement(generate_request, 'TxnId').text = txn_id
			
		if opt:
			if len(opt) > 64:
				raise ValueError('Opt must be <= 64 chars.')
		
			SubElement(generate_request, 'Opt').text = opt
		
		response_conn = urllib2.urlopen(self.post_url, tostring(generate_request))
		
		response = parse(response_conn)
		
		root = response.getroot()
		
		valid = root.attrib['valid']
		
		if valid != '1':
			raise PXPayPaymentError('Response indicated valid != 1')
				
		return response.findtext("URI")
		
	def process_response(self, response):
		"""Process a response from DPS to determine if the transaction is valid."""
		response_request = Element('ProcessResponse')
		SubElement(response_request, 'PxPayUserId').text = self.user_id
		SubElement(response_request, 'PxPayKey').text = self.key
		SubElement(response_request, 'Response').text = response
		
		self.response_raw = urllib2.urlopen(self.post_url, tostring(response_request))
		response = parse(self.response_raw)
		
		root = response.getroot()

		valid = root.attrib['valid']
		
		self.amount_settlement = response.findtext('AmountSettlement')
		self.auth_code = response.findtext('AuthCode')
		self.card_name = response.findtext('CardName')
		self.card_number = response.findtext('CardNumber')
		self.date_expiry = response.findtext('DateExpiry')
		self.dps_txn_ref = response.findtext('DpsTxnRef')
		self.success = response.findtext('Success')
		self.response_text = response.findtext('ResponseText')
		self.dps_billing_id = response.findtext('DpsBillingId')
		self.cardholder_name = response.findtext('CardHolderName')
		self.currency_settlement = response.findtext('CurrencySettlement')
		self.txn_data_1 = response.findtext('TxnData1')
		self.txn_data_2 = response.findtext('TxnData2')
		self.txn_data_3 = response.findtext('TxnData3')
		
		try:
			self.txn_data_1 = simplejson.loads(self.txn_data_1)
		except:
			pass

		try:
			self.txn_data_2 = simplejson.loads(self.txn_data_2)
		except:
			pass
			
		try:
			self.txn_data_3 = simplejson.loads(self.txn_data_3)
		except:
			pass
		
		self.txn_type = response.findtext('TxnType')
		self.currency_input = response.findtext('CurrencyInput')
		self.merchant_reference = response.findtext('MerchantReference')
		self.client_info = response.findtext('ClientInfo')
		self.txn_id = response.findtext('TxnId')
		self.email_address = response.findtext('EmailAddress')
		self.billing_id = response.findtext('BillingId')
		self.txn_mac = response.findtext('TxnMac')
		
		if self.success != '1':
			raise PXPayPaymentError('Payment failed: %s' % self.response_text)