"""KALE emergency LAN chat. In-memory only; anonymous displayed names, bearer session tokens.
Never write user messages, tokens or client addresses to disk.
"""
from collections import deque
from datetime import datetime, timezone
import re
import secrets
import threading
import time

class ChatError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status=status

class LANChat:
    def __init__(self, ttl=65, max_users=64, max_messages=180):
        self.ttl=ttl
        self.max_users=max_users
        self.sessions={}
        self.messages=deque(maxlen=max_messages)
        self.sequence=0
        self.lock=threading.RLock()

    @staticmethod
    def name(value):
        if not isinstance(value,str):raise ChatError('Geçerli bir isim yaz.')
        name=value.strip()
        if not (2<=len(name)<=28) or any(ord(c)<32 or ord(c)==127 for c in name):
            raise ChatError('İsim 2–28 karakter olmalı.')
        if len(name.encode('utf-8'))>80:raise ChatError('İsim çok uzun.')
        return name

    def _purge(self,now):
        for token,s in list(self.sessions.items()):
            if now-s['last_seen']>self.ttl:self.sessions.pop(token,None)

    def _auth(self,token,now):
        if not isinstance(token,str) or len(token)!=64:raise ChatError('Oturum bulunamadı. Yeniden giriş yap.',401)
        session=self.sessions.get(token)
        if session is None:raise ChatError('Oturum süresi dolmuş. Yeniden giriş yap.',401)
        session['last_seen']=now
        return session

    def join(self,name,now=None):
        now=time.monotonic() if now is None else now
        name=self.name(name)
        with self.lock:
            self._purge(now)
            if len(self.sessions)>=self.max_users:raise ChatError('Sohbet dolu. Biraz sonra dene.',503)
            if any(s['name'].casefold()==name.casefold() for s in self.sessions.values()):
                raise ChatError('Bu isim kullanılıyor. Başka isim seç.',409)
            token=secrets.token_hex(32)
            self.sessions[token]={'name':name,'last_seen':now,'last_post':-100,'posts':0}
            return {'token':token,'name':name}

    def snapshot(self,token,after=0,now=None):
        now=time.monotonic() if now is None else now
        with self.lock:
            self._purge(now)
            mine=self._auth(token,now)
            users=sorted((s['name'] for s in self.sessions.values()),key=str.casefold)
            msgs=[m.copy() for m in self.messages if m['id']>after]
            return {'me':mine['name'],'online':users,'count':len(users),'messages':msgs,
                    'last_id':self.sequence,'retained':len(self.messages),'server_time':datetime.now(timezone.utc).isoformat()}

    def send(self,token,text,now=None):
        now=time.monotonic() if now is None else now
        if not isinstance(text,str):raise ChatError('Mesaj metni gerekli.')
        text=text.strip()
        if not text or len(text)>600 or len(text.encode('utf-8'))>2400 or any(c in ('\x00','\r') for c in text):
            raise ChatError('Mesaj boş veya 600 karakteri aşıyor.')
        with self.lock:
            self._purge(now)
            sender=self._auth(token,now)
            if now-sender['last_post']<0.8:raise ChatError('Çok hızlı gönderiyorsun.',429)
            sender['last_post']=now
            self.sequence+=1
            item={'id':self.sequence,'name':sender['name'],'text':text,
                  'time':datetime.now(timezone.utc).isoformat()}
            self.messages.append(item)
            return {'message':item}

    def leave(self,token):
        with self.lock:
            if isinstance(token,str):self.sessions.pop(token,None)
            return {'ok':True}

CHAT=LANChat()
