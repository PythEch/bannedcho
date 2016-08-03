from django.conf.urls import url

from . import views

urlpatterns = [
	url(r'check-updates.php', views.check_updates),
	url(r'osu-osz2-getscores.php', views.get_scores),
	url(r'', views.catchall),
]
