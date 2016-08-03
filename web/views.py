from django.shortcuts import render
from django.http import HttpResponse
import requests

# Create your views here.
def catchall(request):
	return HttpResponse('tr')

def check_updates(request):
	return HttpResponse(requests.get("https://osu.ppy.sh/%s" % request.get_full_path()).text)

def get_scores(request):
	if request.GET.get('vv') != "3":
		return HttpResponse("Error: Old client.", status=403)
	user = authenticate(username=request.GET.get('us'), password=request.GET.get('ha'))
	try:
		player = Player.objects.get(user=user)
	except Player.DoesNotExist:
		return HttpResponse("Error: Wrong user info.", status=401)
	toreturn = '''2|false|1|1|1
0
[bold:0,size:20]merzbow|woodpecker no. 1
10.0
1|lol|13371337|1337|0|0|1210|0|0|1000|1|24|1|2|1454951961|1
2|ahmet|13371338|1338|0|0|1210|0|0|1000|1|24|2|1|1454951986|1
1|lol|13371337|1337|0|0|1210|0|0|1000|1|24|1|2|1454951961|1
'''
	return HttpResponse(toreturn)

'''	try:
		mapset = Mapset.objects.get(id=request.GET.get('i'))
	except Mapset.DoesNotExist:
	    return HttpResponse("Error: No such mapset.", status=404)

	try:
		beatmap = mapset.beatmap_set.objects.get(filename=request.GET.get('f'))
	except Beatmap.DoesNotExist:
		return HttpResponse("Error: No such beatmap.", status=404)

	if beatmap.filehash != request.GET.get('c'):
		return HttpResponse("Error: Wrong beatmap hash.", status=403)

	mode = request.GET.get('m')
	scoretype = request.GET.get('v')
	if scoretype == 0:
		return HttpResponse("Error: Don't ask the server for local data.", status=400)

	if scoretype == 1:
		plays = Play.objects.filter(beatmap=beatmap, mode=mode)
		leaderboard = plays.order_by('-score', 'timestamp')
		playcount = len(plays)
		toreturn = "2|false|%s|%s|%s\n" % (beatmap.id, mapset.id, playcount)+ \
				   "%s\n" % (beatmap.offset) + \
				   "[bold:0,size:20]%s|%s\n" % (mapset.artist, mapset.song) + \
				   "%s\n" % (beatmap.rating)
		myplay = Play.objects.get(beatmap=beatmap, mode=mode, player=player)
		toreturn += (playstring(myplay, leaderboard.index(myplay)+1)+"\n" if myplay else "\n")
		x = (50 if playcount>=50 else playcount)
		for i in range(0, x):
			toreturn += playstring(leaderboard[i], i+1)+"\n"
	if scoretype in [2,3,4,5]:'''

def avatar(request, id):
	try:
		image = open("web/avatars/" + id, "rb")
	except:
		image = open("web/avatars/-1", "rb")

	return HttpResponse(image.read())
