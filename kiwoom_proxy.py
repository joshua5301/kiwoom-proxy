import sys
import kiwoomproxy

if len(sys.argv) > 1:
    log_level = sys.argv[1]
else:
    log_level = 'ERROR'

proxy = kiwoomproxy.Proxy()
proxy.set_address('127.0.0.1')
proxy.set_port(53939)
proxy.start(log_level=log_level)
