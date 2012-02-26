#coding=utf-8

from BetBall.bet.models import Vote, Gambler, VoteColumn, VoteDetail
from django.http import HttpResponse
from django.template import Context, loader, RequestContext

'''
for all actions of vote
'''


def goVotePage(request):
    context = Context({'session':request.session});
    template = loader.get_template("votes.htm")
    return HttpResponse(template.render(context));

def goNewVotePage(request):
    context = Context({'session':request.session})
    template = loader.get_template("new_votes.htm")
    return HttpResponse(template.render(context))
    

def newVote(request):
    pass


    