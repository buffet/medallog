#!/usr/bin/env python3

# except for the noted exception the following license (the unlicense) applies:
#
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <http://unlicense.org/>

# USAGE:
# 1. install python3 (version three!!1!)
# 2. run the script (double click, most likely)
# 2b. if that didn't work, maybe you got multiple steam accounts with the game or whatever, pass the path to medallog.txt explicitly
# 3. select cell E5 and press ctrl+v
# 4. enjoy new peebs

import contextlib
import ctypes
import datetime
import glob
import os
import re
import sys
import time

### all code until the next ### is stolen from pyperclip
### all copyright belongs to the original authors
### the code is licensed under BSD-3-Clause
from ctypes.wintypes import (
    HGLOBAL,
    LPVOID,
    DWORD,
    LPCSTR,
    INT,
    HWND,
    HINSTANCE,
    HMENU,
    BOOL,
    UINT,
    HANDLE,
)

from ctypes import c_size_t, sizeof, c_wchar_p, get_errno, c_wchar

class CheckedCall(object):
    def __init__(self, f):
        super(CheckedCall, self).__setattr__("f", f)

    def __call__(self, *args):
        ret = self.f(*args)
        if not ret and get_errno():
            raise Exception("Error calling " + self.f.__name__)
        return ret

    def __setattr__(self, key, value):
        setattr(self.f, key, value)


windll = ctypes.windll
msvcrt = ctypes.CDLL("msvcrt")

safeCreateWindowExA = CheckedCall(windll.user32.CreateWindowExA)
safeCreateWindowExA.argtypes = [
    DWORD,
    LPCSTR,
    LPCSTR,
    DWORD,
    INT,
    INT,
    INT,
    INT,
    HWND,
    HMENU,
    HINSTANCE,
    LPVOID,
]
safeCreateWindowExA.restype = HWND

safeDestroyWindow = CheckedCall(windll.user32.DestroyWindow)
safeDestroyWindow.argtypes = [HWND]
safeDestroyWindow.restype = BOOL

OpenClipboard = windll.user32.OpenClipboard
OpenClipboard.argtypes = [HWND]
OpenClipboard.restype = BOOL

safeCloseClipboard = CheckedCall(windll.user32.CloseClipboard)
safeCloseClipboard.argtypes = []
safeCloseClipboard.restype = BOOL

safeEmptyClipboard = CheckedCall(windll.user32.EmptyClipboard)
safeEmptyClipboard.argtypes = []
safeEmptyClipboard.restype = BOOL

safeGetClipboardData = CheckedCall(windll.user32.GetClipboardData)
safeGetClipboardData.argtypes = [UINT]
safeGetClipboardData.restype = HANDLE

safeSetClipboardData = CheckedCall(windll.user32.SetClipboardData)
safeSetClipboardData.argtypes = [UINT, HANDLE]
safeSetClipboardData.restype = HANDLE

safeGlobalAlloc = CheckedCall(windll.kernel32.GlobalAlloc)
safeGlobalAlloc.argtypes = [UINT, c_size_t]
safeGlobalAlloc.restype = HGLOBAL

safeGlobalLock = CheckedCall(windll.kernel32.GlobalLock)
safeGlobalLock.argtypes = [HGLOBAL]
safeGlobalLock.restype = LPVOID

safeGlobalUnlock = CheckedCall(windll.kernel32.GlobalUnlock)
safeGlobalUnlock.argtypes = [HGLOBAL]
safeGlobalUnlock.restype = BOOL

wcslen = CheckedCall(msvcrt.wcslen)
wcslen.argtypes = [c_wchar_p]
wcslen.restype = UINT

GMEM_MOVEABLE = 0x0002
CF_UNICODETEXT = 13


@contextlib.contextmanager
def window():
    """
    Context that provides a valid Windows hwnd.
    """
    # we really just need the hwnd, so setting "STATIC"
    # as predefined lpClass is just fine.
    hwnd = safeCreateWindowExA(
        0, b"STATIC", None, 0, 0, 0, 0, 0, None, None, None, None
    )
    try:
        yield hwnd
    finally:
        safeDestroyWindow(hwnd)


@contextlib.contextmanager
def clipboard(hwnd):
    """
    Context manager that opens the clipboard and prevents
    other applications from modifying the clipboard content.
    """
    # We may not get the clipboard handle immediately because
    # some other application is accessing it (?)
    # We try for at least 500ms to get the clipboard.
    t = time.time() + 0.5
    success = False
    while time.time() < t:
        success = OpenClipboard(hwnd)
        if success:
            break
        time.sleep(0.01)
    if not success:
        raise Exception("Error calling OpenClipboard")

    try:
        yield
    finally:
        safeCloseClipboard()


def copy_windows(text):
    with window() as hwnd:
        with clipboard(hwnd):
            safeEmptyClipboard()

            if text:
                count = wcslen(text) + 1
                handle = safeGlobalAlloc(GMEM_MOVEABLE, count * sizeof(c_wchar))
                locked_handle = safeGlobalLock(handle)

                ctypes.memmove(
                    c_wchar_p(locked_handle), c_wchar_p(text), count * sizeof(c_wchar)
                )

                safeGlobalUnlock(handle)
                safeSetClipboardData(CF_UNICODETEXT, handle)


### end of pyperclip burglery

# order matters
levels = [
    "TUT_MOVEMENT",  # Movement
    "TUT_SHOOTINGRANGE",  # Pummel
    "SLUGGER",  # Gunner
    "TUT_FROG",  # Cascade
    "TUT_JUMP",  # Elevate
    "GRID_TUT_BALLOON",  # Bounce
    "TUT_BOMB2",  # Purify
    "TUT_BOMBJUMP",  # Climb
    "TUT_FASTTRACK",  # Fasttrack
    "GRID_PORT",  # Glass Port
    "GRID_PAGODA",  # Take Flight
    "TUT_RIFLE",  # Godspeed
    "TUT_RIFLEJOCK",  # Dasher
    "TUT_DASHENEMY",  # Thrasher
    "GRID_JUMPDASH",  # Outstretched
    "GRID_SMACKDOWN",  # Smackdown
    "GRID_MEATY_BALLOONS",  # Catwalk
    "GRID_FAST_BALLOON",  # Fastlane
    "GRID_DRAGON2",  # Distinguish
    "GRID_DASHDANCE",  # Dancer
    "TUT_GUARDIAN",  # Guardian
    "TUT_UZI",  # Stomp
    "TUT_JUMPER",  # Jumper
    "TUT_BOMB",  # Dash Tower
    "GRID_DESCEND",  # Descent
    "GRID_STAMPEROUT",  # Driller
    "GRID_CRUISE",  # Canals
    "GRID_SPRINT",  # Sprint
    "GRID_MOUNTAIN",  # Mountain
    "GRID_SUPERKINETIC",  # Superkinetic
    "GRID_ARRIVAL",  # Arrival
    "FLOATING",  # Forgotten City
    "GRID_BOSS_YELLOW",  # The Clocktower
    "GRID_HOPHOP",  # Fireball
    "GRID_RINGER_TUTORIAL",  # Ringer
    "GRID_RINGER_EXPLORATION",  # Cleaner
    "GRID_HOPSCOTCH",  # Warehouse
    "GRID_BOOM",  # Boom
    "GRID_SNAKE_IN_MY_BOOT",  # Streets
    "GRID_FLOCK",  # Steps
    "GRID_BOMBS_AHOY",  # Demolition
    "GRID_ARCS",  # Arcs
    "GRID_APARTMENT",  # Apartment
    "TUT_TRIPWIRE",  # Hanging Gardens
    "GRID_TANGLED",  # Tangled
    "GRID_HUNT",  # Waterworks
    "GRID_CANNONS",  # Killswitch
    "GRID_FALLING",  # Falling
    "TUT_SHOCKER2",  # Shocker
    "TUT_SHOCKER",  # Bouquet
    "GRID_PREPARE",  # Prepare
    "GRID_TRIPMAZE",  # Triptrack
    "GRID_RACE",  # Race
    "TUT_FORCEFIELD2",  # Bubble
    "GRID_SHIELD",  # Shield
    "SA L VAGE2",  # Overlook
    "GRID_VERTICAL",  # Pop
    "GRID_MINEFIELD",  # Minefield
    "TUT_MIMIC",  # Mimic
    "GRID_MIMICPOP",  # Trigger
    "GRID_SWARM",  # Greenhouse
    "GRID_SWITCH",  # Sweep
    "GRID_TRAPS2",  # Fuse
    "TUT_ROCKETJUMP",  # Heaven's Edge
    "TUT_ZIPLINE",  # Zipline
    "GRID_CLIMBANG",  # Swing
    "GRID_ROCKETUZI",  # Chute
    "GRID_CRASHLAND",  # Crash
    "GRID_ESCALATE",  # Ascent
    "GRID_SPIDERCLAUS",  # Straightaway
    "GRID_FIRECRACKER_2",  # Firecracker
    "GRID_SPIDERMAN",  # Streak
    "GRID_DESTRUCTION",  # Mirror
    "GRID_HEAT",  # Escalation
    "GRID_BOLT",  # Bolt
    "GRID_PON",  # Godstreak
    "GRID_CHARGE",  # Plunge
    "GRID_MIMICFINALE",  # Mayhem
    "GRID_BARRAGE",  # Barrage
    "GRID_1GUN",  # Estate
    "GRID_HECK",  # Trapwire
    "GRID_ANTFARM",  # Ricochet
    "GRID_FORTRESS",  # Fortress
    "GRID_GODTEMPLE_ENTRY",  # Holy Ground
    "GRID_BOSS_GODSDEATHTEMPLE",  # The Third Temple
    "GRID_EXTERMINATOR",  # Spree
    "GRID_FEVER",  # Breakthrough
    "GRID_SKIPSLIDE",  # Glide
    "GRID_CLOSER",  # Closer
    "GRID_HIKE",  # Hike
    "GRID_SKIP",  # Switch
    "GRID_CEILING",  # Access
    "GRID_BOOP",  # Congregation
    "GRID_TRIPRAP",  # Sequence
    "GRID_ZIPRAP",  # Marathon
    "TUT_ORIGIN",  # Sacrifice
    "GRID_BOSS_RAPTURE",  # Absolution
    "SIDEQUEST_OBSTACLE_PISTOL",  # Elevate Traversal I
    "SIDEQUEST_OBSTACLE_PISTOL_SHOOT",  # Elevate Traversal II
    "SIDEQUEST_OBSTACLE_MACHINEGUN",  # Purify Traversal
    "SIDEQUEST_OBSTACLE_RIFLE_2",  # Godspeed Traversal
    "SIDEQUEST_OBSTACLE_UZI2",  # Stomp Traversal
    "SIDEQUEST_OBSTACLE_SHOTGUN",  # Fireball Traversal
    "SIDEQUEST_OBSTACLE_ROCKETLAUNCHER",  # Dominion Traversal
    "SIDEQUEST_RAPTURE_QUEST",  # Book of Life Traversal
    "SIDEQUEST_DODGER",  # Doghouse
    "GRID_GLASSPATH",  # Choker
    "GRID_GLASSPATH2",  # Chain
    "GRID_HELLVATOR",  # Hellevator
    "GRID_GLASSPATH3",  # Razor
    "SIDEQUEST_ALL_SEEING_EYE",  # All Seeing Eye
    "SIDEQUEST_RESIDENTSAWB",  # Resident Saw I
    "SIDEQUEST_RESIDENTSAW",  # Resident Saw II
    "SIDEQUEST_SUNSET_FLIP_POWERBOMB",  # Sunset Flip Powerbomb
    "GRID_BALLOONLAIR",  # Balloon Mountain
    "SIDEQUEST_BARREL_CLIMB",  # Climbing Gym
    "SIDEQUEST_FISHERMAN_SUPLEX",  # Fisherman Suplex
    "SIDEQUEST_STF",  # STF
    "SIDEQUEST_ARENASIXNINE",  # Arena
    "SIDEQUEST_ATTITUDE_ADJUSTMENT",  # Attitude Adjustment
    "SIDEQUEST_ROCKETGODZ",  # Rocket
]

if len(sys.argv) > 1:
    filepath = sys.argv[1]
else:
    userprofile = os.getenv("USERPROFILE")
    filepath = glob.glob(f"{userprofile}/AppData/LocalLow/Little Flag Software, LLC/Neon White/*/medallog.txt")[0]

inf = float("inf")
records = {}
with open(filepath) as f:
    for line in f:
        m = re.match(r"^([\w ]+) (\d+.\d+)", line)
        if not m:
            raise Exception("idk invalid syntax, what are you doing?")
        records[m[1]] = min(records.get(m[1], inf), float(m[2]))

res = ""
for lvl in levels:
    sec = records[lvl]
    min = int(sec // 60)
    sec = sec % 60
    sec = int(sec * 1000) / 1000.0
    res += f"{min}:{sec:06.3f}\n"

copy_windows(res)
