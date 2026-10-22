"""Fetch only explicitly requested supported fonts and their licenses locally."""
import hashlib
import io
import json
from pathlib import Path
import urllib.request

from PIL import ImageFont


def fetch_font(name, output_dir):
    if name.strip().casefold() not in ('noto sans kr', 'noto-sans-kr', '구글 고딕', '구글고딕', '본고딕'):
        raise ValueError('Supported download: Noto Sans KR. Other fonts need a verified local file/source.')
    directory = Path(output_dir).expanduser().resolve()
    # The user-selected font is stored in the work folder, never installed system-wide.
    font = directory / 'NotoSansKR.ttf'
    license_file = directory / 'NotoSansKR-OFL.txt'
    receipt = directory / 'NotoSansKR-source.json'
    if any(p.exists() for p in (font, license_file, receipt)):
        if not all(p.is_file() for p in (font, license_file, receipt)):
            raise ValueError('Incomplete font cache; use a new output directory or repair the selected cache')
        metadata = json.loads(receipt.read_text(encoding='utf-8'))
        if hashlib.sha256(font.read_bytes()).hexdigest() != metadata['sha256'] or hashlib.sha256(license_file.read_bytes()).hexdigest() != metadata['license_sha256']:
            raise ValueError('Font cache changed; inspect it before reuse')
        return metadata
    base = 'https://raw.githubusercontent.com/google/fonts/main/ofl/notosanskr/'
    font_url, license_url = base + 'NotoSansKR%5Bwght%5D.ttf', base + 'OFL.txt'
    # Finish both downloads and validate before publishing any cache entry.
    def download(url):
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read(32 * 1024 * 1024 + 1)
        if len(data) > 32 * 1024 * 1024:
            raise ValueError('Font resource exceeds expected maximum size')
        return data
    data, license_data = download(font_url), download(license_url)
    face = ImageFont.truetype(io.BytesIO(data), 52)
    if face.getname()[0] != 'Noto Sans KR' or b'SIL OPEN FONT LICENSE' not in license_data:
        raise ValueError('Downloaded font family or license does not match the requested source')
    metadata = {'family': 'Noto Sans KR', 'font': str(font), 'font_weight': 600,
                'source': font_url, 'license_source': license_url, 'license': str(license_file),
                'sha256': hashlib.sha256(data).hexdigest(),
                'license_sha256': hashlib.sha256(license_data).hexdigest()}
    directory.mkdir(parents=True, exist_ok=True)
    for path, content in ((font, data), (license_file, license_data),
                          (receipt, (json.dumps(metadata, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))):
        with path.open('xb') as stream:
            stream.write(content)
    return metadata
