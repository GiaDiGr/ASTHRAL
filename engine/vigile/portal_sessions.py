"""Bounded local portal sessions and request admission; no clinical authority."""
import time,secrets,hashlib,threading
class Sessions:
 def __init__(self,idle=900,absolute=28800,clock=time.monotonic):
  if not 1<=idle<=3600 or not idle<=absolute<=86400:raise ValueError('INVALID_SESSION_POLICY')
  self.idle=idle;self.absolute=absolute;self.clock=clock;self.rows={};self.lock=threading.RLock()
 def _key(self,token):return hashlib.sha256(token.encode()).hexdigest()
 def get(self,token,touch=True):
  with self.lock:
   key=self._key(token);row=self.rows.get(key);now=self.clock()
   if not row or now>=min(row['idle_until'],row['absolute_until']):self.rows.pop(key,None);return None
   if touch:row['idle_until']=min(now+self.idle,row['absolute_until'])
   return dict(row)
 def create(self,absolute_until=None):
  with self.lock:
   now=self.clock()
   for key,row in list(self.rows.items()):
    if now>=min(row['idle_until'],row['absolute_until']):self.rows.pop(key)
   if len(self.rows)>=128:raise RuntimeError('SESSION_LIMIT')
   token=secrets.token_urlsafe(32);self.rows[self._key(token)]={'idle_until':now+self.idle,'absolute_until':absolute_until or now+self.absolute,'reads':[],'assistant':[]};return token
 def revoke(self,token):
  with self.lock:self.rows.pop(self._key(token),None)
 def renew(self,token):
  with self.lock:
   row=self.get(token,False)
   if not row:return None
   self.revoke(token);new=self.create(row['absolute_until']);self.rows[self._key(new)]['reads']=row['reads'];self.rows[self._key(new)]['assistant']=row['assistant'];return new
 def admit(self,token,assistant=False):
  with self.lock:
   row=self.rows.get(self._key(token));now=self.clock()
   if row and now>=min(row['idle_until'],row['absolute_until']):self.rows.pop(self._key(token),None);return False
   if not row:return False
   name='assistant' if assistant else 'reads';window=[t for t in row[name] if now-t<60];row[name]=window
   if len(window)>=(12 if assistant else 120):return False
   window.append(now);return True
