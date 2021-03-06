#coding=utf-8
import datetime,time    
import getpass
import os
import sys
import md5
import json
import random
from weibo import APIClient
from django.template import Context, loader,RequestContext
from django.db.models import Q
from django.http import *
from BetBall.bet.timer import *
from BetBall.bet.models import *  
import random, Image, ImageDraw, ImageFont, md5, datetime, ImageColor, StringIO

#APP_KEY = '3118024522' # app key of betball
#APP_SECRET = '95895b5b4556994a798224902af57d30' # app secret of betball
#CALLBACK_URL = 'http://www.noya35.com/weiboLoginBack' # callback url

APP_KEY = '2945318614' # app key of betball
APP_SECRET = '26540ac5e2728be53005df042bc9bc00' # app secret of betball
CALLBACK_URL = 'http://127.0.0.1:8888/weiboLoginBack' # callback url
client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
SITE_URL = 'http://www.noya35.com'

def listTodayMatches(request):    
    gambler =  request.session.get('gambler')
    if gambler is None:
        c = Context({'session':request.session}) 
        t = loader.get_template('login.htm')
        return HttpResponse(t.render(c))
    else:
        now = datetime.datetime.now()  
        list = Match.objects.filter(state='1', matchtime__gte=now)     
        c = Context({'list':list,'session':request.session}) 
        t = loader.get_template('index.htm')
        return HttpResponse(t.render(c))
    
def viewMatches(request,year,month,date):
    year=int(year)    
    month=int(month)    
    date=int(date)    
    matchdate = datetime.date(year,month,date)  
    list = Match.objects.filter(state='1', matchdate=matchdate)      
    c = Context({'list':list,'matchdate':matchdate,'session':request.session}) 
    t = loader.get_template('matches.htm')
    return HttpResponse(t.render(c))

def listTodayAllMatches(request):    
    now = datetime.datetime.now()    
    list = Match.objects.filter(matchtime__gte=now)      
    c = Context({'list':list,'session':request.session}) 
    t = loader.get_template('index.htm')
    return HttpResponse(t.render(c))

def viewMatch(request):   
    matchdate = datetime.date.today()    
    list = Match.objects.filter(matchdate=matchdate)      
    c = Context({'list':list,'session':request.session}) 
    t = loader.get_template('index.htm')
    return HttpResponse(t.render(c))

def gologin(request):
    c = Context({}) 
    t = loader.get_template('login.htm')
    return HttpResponse(t.render(c))

def login(request):  
    r = request.POST['result']
    sr = request.session['result']
    if r!=str(sr):
        return result("Wrong answer!")
    username = request.POST['username']
    m = Gambler.objects.filter(username=username)      
    pwd = md5.new(request.POST['password'])
    pwd.digest()
    if len(m)!=0:
        if  m[0].password == pwd.hexdigest():
            if m[0].state=='0':
                return result("Account not active, please contact admin.")
            else:
                request.session['gambler'] = m[0]
                return myaccount(request)
        else:
            return result("Your username and password didn't match.")
    else:
        return result("Your username and password didn't match.")


def register(request):  
    c = Context({}) 
    t = loader.get_template('register.htm')
    return HttpResponse(t.render(c))
    
def saveRegister(request):  
    username = request.POST['username'].strip()
    email = request.POST['email'].strip()
    if validateEmail(request.POST['email']):
        weibo = 'weibo' in request.session and request.session['weibo'] or ''
        if username is None:
            c = Context({}) 
            t = loader.get_template('register.htm')
            return HttpResponse(t.render(c))      
        pwd = md5.new(request.POST['password'])
        if request.POST['password']!=request.POST['password1']:
            return result("Password didn't match.")
        u = Gambler.objects.filter(username=username)
        if len(u)>0:
            return result("Username exsited.")
        u = Gambler.objects.filter(email=email)
        if len(u)>0:
            return result("Email exsited.")
        else:
            name = request.POST['name']
            gambler = Gambler(name=name,username=username,weibo=weibo,password=pwd.hexdigest(),state='1',regtime=datetime.datetime.now(),balance=0)
            gambler.save()
            return result("Please wait for admin to approve your register.")
    else:
        return result("Email not valid.")

def recharge(request):  
    c = Context({}) 
    t = loader.get_template('recharge.htm')
    return HttpResponse(t.render(c))


def logout(request):
    try:
        del request.session['gambler']
    except KeyError:
        pass
    return result("You're logged out.")
    
def betMatch(request,id,r):   
    id=int(id)
    r = str(r)
    match = Match.objects.get(id=id)
    now = datetime.datetime.now()
    if now>match.matchtime:
        return result("Kidding! Match is over!")
    gambler =  request.session.get('gambler')
    bets = Transaction.objects.filter(match=match,gambler=gambler)
    #下注自动发微博
    status = u'亲们，俺刚才手快，砸了一罐可乐在上面'+match.hometeam+'vs'+match.awayteam+u'，您别b4啊！'+SITE_URL
    if client!=None:
        expires_in = request.session.get('expires_in')
        access_token = request.session.get('access_token')
        client.set_access_token(access_token, expires_in)
        client.post.statuses__update(status=status)
    if len(bets)==0:
        transaction = Transaction(match=match,gambler=gambler,bet=1,bettime=now,result=r,state='0')
        transaction.save()
        return result("Thanks for your bet.")
    
    else:
        transaction=bets[0]
        transaction.bettime=now
        transaction.result=r
        transaction.save()
        return result("Thanks for update your bet.")

def viewMatchBet(request):  
    if request.session.get('admin', False):
        return result("You've not admin!")
    matchdate = datetime.date.today()    
    list = Match.objects.filter(matchdate=matchdate)      
    c = Context({'list':list,'session':request.session}) 
    t = loader.get_template('index.htm')
    return HttpResponse(t.render(c))

def viewGambler(request):   
    admin=request.session.get('admin')
    if admin is None:
        t = loader.get_template('admin_login.htm')
        c = Context({}) 
        return HttpResponse(t.render(c))
    list = Gambler.objects.all().order_by("-state") 
    c = Context({'list':list,'session':request.session}) 
    t = loader.get_template('gambler.htm')
    return HttpResponse(t.render(c))
 
def lega(request,lega): 
    admin=request.session.get('admin')  
    if admin is None:
        t = loader.get_template('admin_login.htm')
        c = Context({}) 
        return HttpResponse(t.render(c))
    now = datetime.datetime.now()    
    list = Match.objects.filter(matchtime__gte=now,lega=lega).order_by('-state','matchtime')        
    c = Context({'list':list,'session':request.session}) 
    t = loader.get_template('admin.htm')
    return HttpResponse(t.render(c))


def myaccount(request):
    gambler =  request.session.get('gambler')
    if gambler is None:
        c = Context({}) 
        t = loader.get_template('login.htm')
        return HttpResponse(t.render(c))
    else:
        c = Context({'gambler':gambler,'session':request.session}) 
        t = loader.get_template('my.htm')
        return HttpResponse(t.render(c))
    
def updateAccount(request):
    gambler =  request.session.get('gambler')
    name = request.POST['name']
    pwd = request.POST['password']
    pwd1 = request.POST['password1']
    pwd2 = request.POST['password2']
    if name!="":
        gambler.name=name
    if pwd!="":
        pwd = md5.new(pwd)
        pwd.digest()
        if gambler.password == pwd.hexdigest():
            if pwd1!="" and pwd2!="" and pwd1==pwd2:
                pwd1= md5.new(pwd1)
                gambler.password = pwd1.hexdigest()
            else:
                result("Please input the same password twice!")
        else:
            return result("Wrong old password!")
    gambler.save()
    request.session['gambler']=gambler
    return result("Account update!")
    
def mybet(request):
    gambler =  request.session.get('gambler')
    if gambler is None:
        c = Context({}) 
        t = loader.get_template('login.htm')
        return HttpResponse(t.render(c))
    else:
        bets = Transaction.objects.filter(gambler=gambler).order_by('-bettime')
        c = Context({'gambler':gambler,'bets':bets,'session':request.session}) 
        t = loader.get_template('mybet.htm')
        return HttpResponse(t.render(c))

def result(r):
    c = Context({'result':r}) 
    t = loader.get_template('result.htm')
    return HttpResponse(t.render(c))

def search(request):
    key=request.GET['q']
    list = Match.objects.filter(Q(lega__icontains=key)|Q(hometeam__icontains=key)|Q(awayteam__icontains=key))  
    now = datetime.datetime.now()
    c = Context({'list':list,'key':key,'now':now,'session':request.session}) 
    t = loader.get_template('search.htm')
    return HttpResponse(t.render(c))  



def cancelBet(request,id):
    id=int(id)
    transaction = Transaction.objects.get(id=id) 
    matchtime = transaction.match.matchtime
    now = datetime.datetime.now()
    if now>matchtime:
        return result("Match is over, you cannot cancel this bet!")   
    else:  
        transaction.delete() 
        return result("Transaction clean!")     
    
def viewMatchBets(request,id):
    id=int(id)
    match = Match.objects.get(id=id) 
    bets = Transaction.objects.filter(match=match).order_by('-bettime') 
    c = Context({'list':bets,'match':match,'session':request.session}) 
    t = loader.get_template('match_bet.htm')
    return HttpResponse(t.render(c))

def setSession(c,request):
    c['session']=request.session
    
def validateEmail(email):
    if len(email) > 6:
        if re.match('^[\w\.-]+@[\w\.-]+\.\w{2,4}$', email) != None:
            return 1
    return 0
 
def getUsername(request):  
    c = Context({}) 
    t = loader.get_template('get_username.htm')
    return HttpResponse(t.render(c))
    
def getPassword(request):  
    c = Context({}) 
    t = loader.get_template('get_password.htm')
    return HttpResponse(t.render(c))

def verifyImg(request):
    n1 = random.randint(0,9)
    n2 = random.randint(0,9)  
    op = ''
    if n1%3==0:
        result = n1+n2
        op = str(n1)+'+'+str(n2)+'='
    if n1%3==1:
        result = n1-n2
        op = str(n1)+'-'+str(n2)+'='
    if n1%3==2:
        result = n1*n2
        op = str(n1)+'*'+str(n2)+'='
    request.session['result']=result
    #创建一个IO流对象  
    mstream=StringIO.StringIO()  
    #这是我想要从querystring中获取的显示图片的字符（如果想要图片验证，则加密它，注意我没有使用session存储这个需要显示的字符串，因为session消耗资源太大）  
    q = list(op)
    #我这里演示的是直接产生的字符串，实际中需要加入噪音线  
    im = Image.new("RGBA", (80, 20),color=127*122)  
    draw = ImageDraw.Draw(im, "RGBA")  
    draw.ink = 255  
    draw.text((5,0), q[0],font=ImageFont.truetype("ARIAL.TTF", 18))  
    draw.text((20,0), q[1],font=ImageFont.truetype("ARIAL.TTF", 18))  
    draw.text((35,0), q[2],font=ImageFont.truetype("ARIAL.TTF", 18))  
    draw.text((50,0), q[3],font=ImageFont.truetype("ARIAL.TTF", 18))  
    im.save(mstream,"JPEG")  
    return HttpResponse(mstream.getvalue(),"image/jpg")  