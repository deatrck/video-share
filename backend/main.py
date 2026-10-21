import asyncio
import ipaddress
import os
import re
import socket
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask
import yt_dlp

app = FastAPI(title='Video Share API')
app.add_middleware(CORSMiddleware, allow_origins=os.getenv('ALLOWED_ORIGINS','http://localhost:3000').split(','), allow_methods=['GET','POST'], allow_headers=['*'])
HOSTS = {'tiktok.com':'TikTok','douyin.com':'Douyin','iesdouyin.com':'Douyin','facebook.com':'Facebook','fb.watch':'Facebook','instagram.com':'Instagram','youtube.com':'YouTube','youtu.be':'YouTube','xiaohongshu.com':'Xiaohongshu','xhslink.com':'Xiaohongshu'}
class Link(BaseModel):
    url: str

def check_url(raw):
    parsed=urlparse(raw.strip())
    if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port not in (None,443):
        raise HTTPException(400,'Chỉ chấp nhận HTTPS công khai')
    host=(parsed.hostname or '').lower().rstrip('.')
    provider=next((v for k,v in HOSTS.items() if host==k or host.endswith('.'+k)),None)
    if not provider: raise HTTPException(400,'Nền tảng chưa được hỗ trợ')
    try:
        addresses=socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
        if any(not ipaddress.ip_address(addr[4][0]).is_global for addr in addresses):
            raise ValueError('Private address')
    except Exception: raise HTTPException(400,'Không xác minh được máy chủ công khai')
    return raw.strip(),provider

def extract(url, download=False, directory=None):
    options={'quiet':True,'no_warnings':True,'noplaylist':True,'skip_download':not download,'socket_timeout':15,'retries':1,'max_filesize':250*1024*1024,'ignoreerrors':False,'extract_flat':False}
    if download:
        options.update({'outtmpl':str(Path(directory)/'%(id).80s.%(ext)s'),'format':'best[ext=mp4][height<=1080]/best[height<=1080]/best','merge_output_format':'mp4'})
    with yt_dlp.YoutubeDL(options) as ydl:
        data=ydl.extract_info(url,download=download)
        if not data: raise ValueError('Không có dữ liệu video')
        return data

@app.get('/api/health')
def health(): return {'ok':True}

@app.post('/api/info')
async def info(link:Link):
    url,provider=check_url(link.url)
    try:
        data=await asyncio.wait_for(asyncio.to_thread(extract,url),timeout=35)
        if data.get('_type')=='playlist': raise HTTPException(400,'Bản đầu hỗ trợ video lẻ, chưa hỗ trợ cả kênh')
        return {'id':str(data.get('id','')),'title':data.get('title') or 'Video','thumbnail':data.get('thumbnail'),'duration':data.get('duration'),'uploader':data.get('uploader'),'provider':provider,'url':url}
    except HTTPException: raise
    except Exception as exc: raise HTTPException(422,f'Không thể đọc video này: {str(exc)[:180]}')

@app.post('/api/download')
async def download(link:Link):
    url,_=check_url(link.url)
    folder=tempfile.TemporaryDirectory(prefix='video-share-')
    try:
        await asyncio.wait_for(asyncio.to_thread(extract,url,True,folder.name),timeout=150)
        files=[p for p in Path(folder.name).iterdir() if p.is_file() and p.suffix.lower() in ('.mp4','.webm','.mkv')]
        if not files: raise ValueError('Không có file tải được')
        file=max(files,key=lambda p:p.stat().st_size)
        if file.stat().st_size>250*1024*1024: raise ValueError('File vượt giới hạn 250 MB')
        return FileResponse(file,filename=file.name,media_type='application/octet-stream',background=BackgroundTask(folder.cleanup))
    except Exception as exc:
        folder.cleanup()
        raise HTTPException(422,f'Tải thất bại: {str(exc)[:180]}')
