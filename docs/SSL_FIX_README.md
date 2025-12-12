# SSL Fix for Bybit Testnet API

## Problem
The Bybit testnet API uses self-signed certificates, which causes SSL verification to fail with the error:
```
requests.exceptions.SSLError: HTTPSConnectionPool(host='api-testnet.bybit.com', port=443): Max retries exceeded with url: /v5/market/kline?category=linear&interval=15&limit=500&symbol=BTCUSDT (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1000)')))
```

## Solution
Modified `bybit_api.py` to disable SSL verification for testnet mode:

1. **Added urllib3 import** at the top of the file
2. **Disabled SSL warnings** for testnet mode
3. **Disabled SSL verification** for the HTTP client in testnet mode

### Changes Made

```python
# Added to imports
import urllib3

# In __init__ method for testnet mode
else:
    # Для testnet отключаем SSL verification из-за self-signed certificates
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Создаем HTTP сессию для testnet
    self.session = HTTP(
        api_key=api_key,
        api_secret=api_secret,
        testnet=True
    )
    
    # Отключаем SSL verification для testnet
    if hasattr(self.session, '_http_manager') and hasattr(self.session._http_manager, 'client'):
        self.session._http_manager.client.verify = False
```

## Testing
Use the test script to verify the fix:
```bash
python test_ssl_fix.py
```

## Security Note
⚠️ **Important**: This fix only applies to testnet mode. SSL verification remains enabled for real trading mode to ensure security.

## Files Modified
- `bybit_api.py` - Added SSL fix for testnet mode
- `test_ssl_fix.py` - Test script to verify the fix

## Usage
The fix is automatically applied when using testnet mode:
```python
api = BybitAPI(api_key=api_key, api_secret=api_secret, trade_mode='test')
```

For real trading, SSL verification remains enabled:
```python
api = BybitAPI(api_key=api_key, api_secret=api_secret, trade_mode='real')
```

