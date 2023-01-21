import network
from esp32 import NVS

def connWiFi() :
	try :
		_nvs = NVS('esp32Ctrl')
		_buf = bytearray(1024)
		sz   = _nvs.get_blob('ssid', _buf)
		ssid = _buf[:sz].decode()
		sz   = _nvs.get_blob('key', _buf)
		key  = _buf[:sz].decode()
		w    = network.WLAN(network.STA_IF)
		w.active(False)
		w.active(True)
		w.connect(ssid, key if key else None)
		print('Connecting Wi-Fi to %s...' % ssid)
	except :
		pass

connWiFi()
