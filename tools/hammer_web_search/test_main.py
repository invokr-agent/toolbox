import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch, MagicMock

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("tool_under_test", HERE/"main.py")
tool=importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)
ARGS={'query': 'hello', 'limit': 5}
RESPONSE=(200, 'application/json', b'{"results":[{"title":"Hello","url":"https://example.org/","content":"World"}]}')
EXPECTED={'results': [{'title': 'Hello', 'url': 'https://example.org/', 'snippet': 'World'}], 'truncated': False}
HOST='search.example.org'

class Tests(unittest.TestCase):
    def test_operation_offline(self):
        with patch.object(tool,"request",return_value=RESPONSE), patch.object(tool.Path,"read_text",return_value=json.dumps({"endpoint":"https://"+HOST+"/search"})):
            self.assertEqual(tool.run(ARGS),EXPECTED)

    def test_url_policy(self):
        for url in ['http://'+HOST, 'https://127.0.0.1/', 'https://'+HOST+':444/',
                    'https://evil.invalid/', 'https://user:pass@'+HOST, 'https://'+HOST+'/#fragment',
                    'https://'+HOST+'/\r\nx']:
            with self.subTest(url=url), patch.object(tool.socket,"getaddrinfo") as dns:
                with self.assertRaises(ValueError): tool.request(url)
                dns.assert_not_called()

    def test_private_and_mixed_dns_denied(self):
        for addresses in [['127.0.0.1'],['169.254.169.254'],['10.0.0.1'],['::1'],['93.184.216.34','127.0.0.1']]:
            answers=[(2,1,6,'',(ip,443)) for ip in addresses]
            with patch.object(tool.socket,'getaddrinfo',return_value=answers), patch.object(tool.socket,'socket') as sock:
                with self.assertRaises(ValueError): tool.request('https://'+HOST+'/')
                sock.assert_not_called()

    def test_pins_ip_verifies_tls_and_closes(self):
        answers=[(2,1,6,'',('93.184.216.34',443))]
        with patch.object(tool.socket,'getaddrinfo',return_value=answers) as dns, patch.object(tool.socket,'socket') as sock, patch.object(tool.ssl,'create_default_context') as tls, patch.object(tool.http.client,'HTTPSConnection') as client:
            response=client.return_value.getresponse.return_value
            response.status=200
            response.getheader.side_effect=lambda key,default='': {'Content-Encoding':'identity','Content-Type':'text/plain'}.get(key,default)
            response.read.return_value=b'hello'
            self.assertEqual(tool.request('https://'+HOST+'/path?q=x'),(200,'text/plain',b'hello'))
            dns.assert_called_once()
            sock.return_value.connect.assert_called_once_with(('93.184.216.34',443))
            tls.return_value.wrap_socket.assert_called_once_with(sock.return_value,server_hostname=HOST)
            response.read.assert_called_once_with(65537)
            client.return_value.close.assert_called_once()
            sock.return_value.close.assert_called_once()

    def test_redirect_status_compression_and_oversize_denied(self):
        for status,encoding,body in [(302,'identity',b''),(500,'identity',b''),(200,'gzip',b''),(200,'identity',b'x'*65537)]:
            with patch.object(tool.socket,'getaddrinfo',return_value=[(2,1,6,'',('93.184.216.34',443))]), patch.object(tool.socket,'socket'), patch.object(tool.ssl,'create_default_context'), patch.object(tool.http.client,'HTTPSConnection') as client:
                response=client.return_value.getresponse.return_value
                response.status=status
                response.getheader.side_effect=lambda key,default='': encoding if key=='Content-Encoding' else 'text/plain'
                response.read.return_value=body
                with self.assertRaises(ValueError): tool.request('https://'+HOST+'/')
                client.return_value.close.assert_called_once()

    def test_protocol_errors_offline(self):
        name=json.loads((HERE/'plugin.json').read_text())['name']
        for raw in ['{',json.dumps({'name':name,'arguments':{}}),json.dumps({'name':name,'arguments':{'unexpected':1}})]:
            result=subprocess.run([sys.executable,'-I','-B',str(HERE/'main.py')],input=raw,text=True,capture_output=True,timeout=3,env={'PATH':os.defpath})
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('error',json.loads(result.stdout))

if __name__=='__main__': unittest.main()
