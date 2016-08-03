from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

import pickle

class GameMode(models.Model):
    MODE_OSU   = 0
    MODE_CTB   = 1
    MODE_TAIKO = 2
    MODE_MANIA = 3
    GAME_MODES = (
        (MODE_OSU, "Osu"),
        (MODE_CTB, "CTB"),
        (MODE_TAIKO, "Taiko"),
        (MODE_MANIA, "Mania"),
    )

    mode = models.PositiveIntegerField(choices=GAME_MODES)

    def __str__(self):
        return GameMode.GAME_MODES[self.mode][1]

class GameModeData(models.Model):
    total_score  = models.PositiveIntegerField()
    ranked_score = models.PositiveIntegerField()
    pp           = models.FloatField()
    accuracy     = models.FloatField()

    def __str__(self):
        return "T. Score: %s, R. Score: %s, PP: %s, Acc: %s" % (self.total_score, self.ranked_score, self.pp, self.accuracy)

class Player(models.Model):
    user      = models.OneToOneField(User)
    osu       = models.ForeignKey(GameModeData, related_name='osu')
    ctb       = models.ForeignKey(GameModeData, related_name='ctb')
    taiko     = models.ForeignKey(GameModeData, related_name='taiko')
    mania     = models.ForeignKey(GameModeData, related_name='mania')
    token     = models.CharField(max_length=36)
    last_ping = models.FloatField()

    def __str__(self):
        return str(self.user)

class Mapset(models.Model):
    song   = models.TextField(max_length=100)
    artist = models.TextField(max_length=100)
    mapper = models.ForeignKey(Player, on_delete=models.CASCADE)

    def __str__(self):
        return "%s - %s // %s" % (self.artist, self.song, str(self.mapper))

class Beatmap(models.Model):
    mapset   = models.ForeignKey(Mapset, on_delete=models.CASCADE)
    cs       = models.FloatField()
    hp       = models.FloatField()
    od       = models.FloatField()
    ar       = models.FloatField()
    diff     = models.FloatField()
    bpm      = models.FloatField()
    length   = models.SmallIntegerField()
    filename = models.TextField(max_length=100)
    filehash = models.TextField(max_length=32)
    name     = models.TextField(max_length=30)

    def __str__(self):
        return "%s - %s [%s] // %s" % (self.mapset.artist, self.mapset.song, self.name, self.mapset.mapper)

class Play(models.Model):
    pp       = models.FloatField()
    accuracy = models.FloatField()
    score    = models.PositiveIntegerField()
    mode     = models.OneToOneField(GameMode)
    player   = models.ForeignKey(Player, on_delete=models.CASCADE)
    beatmap  = models.ForeignKey(Beatmap, on_delete=models.CASCADE)
    mods     = models.PositiveIntegerField()

    def __str__(self):
        return "%s played by %s" % (self.beatmap, self.player)

class Channel(models.Model):
    data        = models.TextField(default=pickle.dumps([])) # last 100 messages with player id, message and timestamps
    tag         = models.CharField(max_length=32)
    description = models.CharField(max_length=255)
