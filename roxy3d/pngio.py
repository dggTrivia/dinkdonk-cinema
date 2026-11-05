"""Small offline 8-bit RGB/RGBA PNG reader/writer. Only Python stdlib + NumPy.

This avoids installing packages or depending on a separate system Python.
Image arrays are top-down sRGB uint8, with straight alpha as specified by PNG.
"""
import struct
import zlib
import hashlib
import subprocess
import os
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent

def cache_path(path):
    path=Path(path).resolve();stat=path.stat()
    key=hashlib.sha256((str(path)+str(stat.st_mtime_ns)+str(stat.st_size)).encode()).hexdigest()[:24]
    return ROOT/'cache'/'png'/(key+'.rgba')

def predecode(paths):
    """Batch native Windows decoding; Python fallback below stays available."""
    folder=ROOT/'cache'/'png';folder.mkdir(parents=True,exist_ok=True)
    pairs=[(Path(p).resolve(),cache_path(p)) for p in paths if not cache_path(p).exists()]
    if not pairs:return
    listing=folder/('decode_list_'+str(os.getpid())+'.tsv')
    listing.write_text('\n'.join(str(p)+'\t'+str(c) for p,c in pairs),encoding='utf-8')
    subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'decode_png.ps1'),'-List',str(listing)],check=True)

def read(path,use_cache=True):
    buf=Path(path).read_bytes()
    assert buf[:8]==b'\x89PNG\r\n\x1a\n'
    cached=cache_path(path)
    if use_cache and cached.exists():
        w,h=struct.unpack_from('>II',buf,16)
        return np.fromfile(cached,dtype=np.uint8).reshape(h,w,4)
    offset=8;packed=[]
    while offset<len(buf):
        n=struct.unpack_from('>I',buf,offset)[0]
        typ=buf[offset+4:offset+8];data=buf[offset+8:offset+8+n]
        if typ==b'IHDR':
            w,h,bits,mode,comp,filt,interlace=struct.unpack('>IIBBBBB',data)
            assert bits==8 and mode in [2,6] and interlace==0,(bits,mode,interlace)
        if typ==b'IDAT':packed.append(data)
        offset+=n+12
    channels=4 if mode==6 else 3
    raw=np.frombuffer(zlib.decompress(b''.join(packed)),dtype=np.uint8).reshape(h,w*channels+1)
    out=np.zeros((h,w*channels),np.uint8)
    for y,row in enumerate(raw):
        f=int(row[0]);vals=row[1:].copy()
        prev=out[y-1] if y else np.zeros(w*channels,np.uint8)
        if f==0:pass
        elif f==1:
            vals=np.cumsum(vals.reshape(w,channels),axis=0,dtype=np.uint64).astype(np.uint8).reshape(-1)
        elif f==2:vals=(vals.astype(np.uint16)+prev).astype(np.uint8)
        elif f in [3,4]:
            # RGB(A) pixels are independent lanes, while x has a recurrence.
            vals=vals.reshape(w,channels);pv=prev.reshape(w,channels).astype(np.int16)
            left=np.zeros(channels,np.int16);upperleft=np.zeros(channels,np.int16)
            for x in range(w):
                up=pv[x]
                if f==3:pred=(left+up)//2
                else:
                    p=left+up-upperleft
                    a=np.abs(p-left);b=np.abs(p-up);c=np.abs(p-upperleft)
                    pred=np.where((a<=b)&(a<=c),left,np.where(b<=c,up,upperleft))
                vals[x]=((vals[x].astype(np.int16)+pred)&255).astype(np.uint8)
                left=vals[x].astype(np.int16);upperleft=up
            vals=vals.reshape(-1)
        else:raise ValueError(f)
        out[y]=vals
    out=out.reshape(h,w,channels)
    if channels==3:out=np.concatenate([out,np.full((h,w,1),255,np.uint8)],axis=2)
    return out

def write(path,arr):
    arr=np.asarray(arr,np.uint8)
    h,w,c=arr.shape
    assert c in [3,4]
    def chunk(typ,data):return struct.pack('>I',len(data))+typ+data+struct.pack('>I',zlib.crc32(typ+data)&0xffffffff)
    # Sub filtering is fast and compresses gradients and transparent margins well.
    diff=arr.copy()
    diff[:,1:]=(arr[:,1:].astype(np.int16)-arr[:,:-1]).astype(np.uint8)
    scan=np.concatenate([np.ones((h,1),np.uint8),diff.reshape(h,w*c)],axis=1)
    data=b'\x89PNG\r\n\x1a\n'
    data+=chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6 if c==4 else 2,0,0,0))
    data+=chunk(b'sRGB',b'\x00')
    data+=chunk(b'IDAT',zlib.compress(scan.tobytes(),6))+chunk(b'IEND',b'')
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_bytes(data)
