"""Execute the production HTTPS fallback literal with controlled responses."""
import io
from pathlib import Path
import re
import ssl
import sys
import tempfile
import unittest
from unittest.mock import patch

LAUNCHER = Path(__file__).resolve().parents[1] / 'daily-vlog/scripts/run.ps1'
CODE = re.search(r"\$DownloadCode = @'\n(.*?)\n'@", LAUNCHER.read_text(encoding='utf-8-sig'), re.S).group(1)


class Response(io.BytesIO):
    def __init__(self, url, content=b'verified content'):
        super().__init__(content)
        self.url = url

    def geturl(self):
        return self.url


class DownloadTests(unittest.TestCase):
    def run_code(self, output, response=None, error=None):
        with patch.object(sys, 'argv', ['-c', 'https://example.com/uv.zip', str(output)]), patch('urllib.request.urlopen', return_value=response, side_effect=error) as request:
            exec(compile(CODE, str(LAUNCHER), 'exec'), {})
            return request.call_args

    def test_verifies_certificates_and_hostname_then_writes_body(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / '한글 공백.zip'
            call = self.run_code(output, Response('https://downloads.example.com/uv.zip'))
            context = call.kwargs['context']
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
            self.assertTrue(context.check_hostname)
            self.assertEqual(output.read_bytes(), b'verified content')

    def test_insecure_final_redirect_is_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / 'download.zip'; output.write_bytes(b'previous')
            with self.assertRaisesRegex(ValueError, 'HTTPS'):
                self.run_code(output, Response('http://downloads.example.com/uv.zip'))
            self.assertEqual(output.read_bytes(), b'previous')

    def test_certificate_failure_propagates_without_writing(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / 'download.zip'
            with self.assertRaises(ssl.SSLCertVerificationError):
                self.run_code(output, error=ssl.SSLCertVerificationError('fixture untrusted certificate'))
            self.assertFalse(output.exists())


if __name__ == '__main__': unittest.main()
