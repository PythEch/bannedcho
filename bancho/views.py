from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import *
from django.views.decorators.csrf import csrf_exempt

from .models import *

from struct import pack, unpack
from construct import *

import pickle
import hashlib
import time

PROTOCOL_VERSION = 19

#################### Packets ####################

def OsuString(name):
    return StringAdapter(
        LengthValueAdapter(
            Sequence(name,
                Magic("\x0b"),
                ULInt8("length"),
                Field("data", lambda ctx: ctx.length),
            )
        )
    )

array   = PrefixedArray(ULInt32("int"), length_field=ULInt16("length"))
string  = OsuString("string")
default = ULInt32("default")
unknown = Rename("unknown", PrefixedArray(ULInt8("byte"), length_field=ULInt8("length")))

class DataType(object):
    PROTOCOL_VERSION        = 0x4b
    USER_DATA               = 0x53
    PLAY_DATA               = 0x0b
    OPEN_CHANNEL            = 0x40
    CHANNEL_INFO            = 0x41
    CHANNEL_MESSAGE_SERVER  = 0x07
    CHANNEL_MESSAGE_CLIENT  = 0x01
    PING                    = 0x04

packets = {
    DataType.PING: Struct("ping"),
    DataType.CHANNEL_MESSAGE_CLIENT: Struct("channelMessageClient",
        OsuString("string0"),
        OsuString("message"),
        OsuString("channel")
    ),
    DataType.CHANNEL_MESSAGE_SERVER: Struct("channelMessageServer",
        OsuString("playerName"),
        OsuString("message"),
        OsuString("channel"),
        ULInt32("playerId")
    ),
    DataType.USER_DATA: Struct("userData",
        ULInt32("id"),
        OsuString("playerName"),
        ULInt8("utcOffset"),
        ULInt8("country"),
        ULInt8("playerRank"),
        LFloat32("longitude"),
        LFloat32("latitude"),
        ULInt32("globalRank")
    ),
    DataType.PLAY_DATA: Struct("playData",
        ULInt32("id"),
        ULInt8("bStatus"),
        OsuString("string0"),
        OsuString("string1"),
        ULInt32("mods"),
        ULInt8("playMode"),
        ULInt32("int0"),
        ULInt64("score"),
        LFloat32("accuracy"),
        ULInt32("playCount"),
        ULInt64("experience"),
        ULInt32("int1"),
        ULInt16("pp")
    ),
    DataType.CHANNEL_INFO: Struct("channelInfo",
        OsuString("tag"),
        OsuString("description"),
        ULInt16("userCount")
    ),
    24: string,
    64: string,
    66: string,
    105: string,
    23: Pass,
    50: Pass,
    59: Pass,
    80: Pass,
    72: array,
    96: array
}

packet = Struct("osuPacket",
    ULInt16("type"),
    Padding(1),
    PascalString("data", length_field=ULInt32("length")),
)

packet_stream = Struct("packet_stream",
    GreedyRange(
        Struct("osuPacket",
            ULInt16("type"),
            Padding(1),
            ULInt32("length"),
            Switch("payload", lambda context: context.type, packets, default=unknown),
            #Padding(4),
        )
    )
)

def handle_request(request):
    osu_token = request.META.get("HTTP_OSU_TOKEN")
    player = Player.objects.get(token=osu_token)
    stream = packet_stream.parse(request.body).osuPacket
    response = ''

    for p in stream:
        if p.type == DataType.CHANNEL_MESSAGE_CLIENT:
            chan = Channel.objects.get(tag=p.payload.channel)
            msg  = p.payload.message

            data = pickle.loads(chan.data)
            if len(data) >= 100:
				data = data[-100:]
            data.append(
                (player.id, time.time(), msg)
            )

            chan.data = pickle.dumps(data)
            chan.save()

    # check if new message occurs
    for chan in Channel.objects.all():
        data = pickle.loads(chan.data)
        for (player_id, timestamp, msg) in data:
            if timestamp > player.last_ping and player_id != player.id:
                response += create_packet(DataType.CHANNEL_MESSAGE_SERVER, Container(
                    playerId = player_id,
                    playerName = Player.objects.get(id=player_id).user.username,
                    message = msg,
                    channel = chan.tag,
                ))

    player.last_ping = time.time()
    player.save()
    return HttpResponse(response)

# builder
def create_packet(type, value):
    if not value:
        value = 0

    data = packets.get(type, default).build(value)

    return packet.build(Container(
        type = type,
        data = data
    ))

#################### API ####################

def login(request):
    lines = request.body.splitlines()
    if len(lines) != 3:
        return HttpResponse("Error: POST request has to include 3 elements not %d elements." % len(lines), status=400)

    username, passhash, _ = lines
    user = authenticate(username=username, password=passhash)

    player = Player.objects.get(user=user)

    if not player:
        return HttpResponse("Error: Something went wrong while logging in.", status=401)

    token = hashlib.md5(username + passhash + str(time.time())).hexdigest()
    token = "%s-%s-%s-%s-%s" % (token[:8], token[8:12], token[12:16], token[16:20], token[20:])
    player.token = token
    player.last_ping = time.time()
    player.save()

    response = (
        (92, 0), # ban status/time
        (5, 0), # user id
        (DataType.PROTOCOL_VERSION, PROTOCOL_VERSION), # bancho proto version
        (71, 0), # user rank (suppoter etc)
        (72, [1, 2]), # friend list
        (DataType.USER_DATA, Container( # local player
            id = 41,
            playerName = username,
            utcOffset = 24,
            country = 42,
            playerRank = 43,
            longitude = 44,
            latitude = 45,
            globalRank = 46,
        )),
        (DataType.PLAY_DATA, Container( # more local player data
            id = 47,
            bStatus = 48,
            string0 = '',
            string1 = '',
            mods = 49,
            playMode = 50,
            int0 = 51,
            score = 99,
            accuracy = 52,
            playCount = 53,
            experience = 54,
            int1 = 55, #int? global rank
            pp = 56,
        )),
        (DataType.USER_DATA, Container(
            id = 3,
            playerName = 'BanchoBob',
            utcOffset = 24,
            country = 1,
            playerRank = 57,
            longitude = 58,
            latitude = 59,
            globalRank = 60,
        )),
        (96, [0, 41]), # TODO list of player
        (89, None),
        # foreach player online, packet 12 or 95
        (DataType.OPEN_CHANNEL, '#osu'),
        (DataType.OPEN_CHANNEL, '#news'),
        (DataType.CHANNEL_INFO, Container(
            tag = '#osu',
            description = 'Main channel',
            userCount = 15
        )),
        (DataType.CHANNEL_INFO, Container(
            tag = '#news',
            description = 'This will contain announcements and info, while beta lasts.',
            userCount = 3
        )),
        (DataType.CHANNEL_MESSAGE_SERVER, Container(
            playerName = 'BanchoBob',
            playerId = 3,
            message = 'This is a test message! First step to getting chat working!',
            channel = '#osu'
        ))
    )

    response = "".join(create_packet(type, data) for (type, data) in response)
    response = HttpResponse(response)

    response['cho-token'] = token
    response['cho-protocol'] = str(PROTOCOL_VERSION)

    return response

@csrf_exempt
def bancho(request, param):
    osu_token = request.META.get("HTTP_OSU_TOKEN")

    if osu_token:
        return handle_request(request)
    else:
        return login(request)
