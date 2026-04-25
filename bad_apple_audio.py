# /// script
# dependencies = [
#  "django-bolt[nanodjango]",
#  "datastar_py"
# ]
# ///
# also requires data:
# - static/audio.mp3 (audio track)
#
# should be able to run with pipx bad_apple_audio_150_mmap.py runbolt
# OR uv run bad_apple_audio_150_mmap.py runbolt
# %%
import asyncio
import mmap
from html import escape
import pathlib
import tomllib

# %%
from nanodjango import Django
from django_bolt.nanodjango import BoltAPI
# %% standard django/django-bolt below this
from django_bolt.responses import StreamingResponse
from django_bolt.middleware import no_compress
from django_bolt import CompressionConfig
from django.http import HttpResponse

# %%
from datastar_py import ServerSentEventGenerator as SSE
# %%

app = Django(
    STATIC_URL="/static/",
)
bolt = BoltAPI()


# %%
WORKINGDIR = pathlib.Path(__file__).parent
# WORKINGDIR = '/Users/clee/code/bad_apple_sse' # used during debuging
DATA_DIR = pathlib.Path(WORKINGDIR) / "bad_apple"
FRAME_FILE = DATA_DIR / "bad_apple_all.txt"
HDR_FILE = DATA_DIR / "details.toml"

_hdr = tomllib.load(open(HDR_FILE, "rb"))
# print(_hdr) # print this to look at media configuration
# %%
# N_ROWS = _hdr["n_rows"]
N_COLUMNS = _hdr["columns"]  # visible columns, excluding newline
_N_COLS_WITH_NL = _hdr["columns"] +1
N_FRAMES = _hdr["frames"] # this needs to be added to details.toml
FRAME_SIZE = _hdr['frame_size']
N_ROWS = FRAME_SIZE // _N_COLS_WITH_NL
FPS = _hdr['fps']
# assert N_ROWS * _N_COLS_WITH_NL == FRAME_SIZE
# %%
# mmap keeps the 77MB of frame data off the heap — the OS pages it in as
# we slice through it, and memory is shared across processes/workers.
_frame_fp = open(FRAME_FILE, "rb")
_frame_mm = mmap.mmap(_frame_fp.fileno(), 0, access=mmap.ACCESS_READ)

DELAY = 1.0 / FPS  # 60 fps

@app.route("/")
def index(request):
    return HttpResponse("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bad Apple SSE</title>
    <link rel="icon" href="favicon.ico" type="image/x-icon">
    <style>
        body {
            background-color: black;
            color: white;
            font-family: monospace;
            white-space: pre;
            margin: 0;
            padding: 0;
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh; /* Ensures the content takes up the full height of the viewport */
            flex-direction: column; /* Stack the button and ASCII display vertically */
        }

        #ascii-display {
            font-size: 20px; /* Initial value, will be updated dynamically */
            line-height: 1.1;
            text-align: center; /* Ensures the ASCII art is centered */
            display: flex;
            justify-content: center;
            align-items: center;
        }

        #play-button {
            font-size: 24px;
            padding: 10px 20px;
            cursor: pointer;
            background-color: white;
            color: black;
            border: none;
            border-radius: 5px;
            margin-top: 20px;
            position: absolute; /* Make the button float above other content */
            top: 50%%; /* Position it vertically in the center */
            left: 50%%; /* Position it horizontally in the center */
            transform: translate(-50%%, -50%%); /* Correct for the button's own size */
        }
    </style>
<script type="module" src="https://cdn.jsdelivr.net/gh/starfederation/datastar@v1.0.0/bundles/datastar.js"></script>
</head>
<body data-signals:playing="false">
    <div id="ascii-display"><div id="ascii-inner"></div></div>
    <button id="play-button"
       data-on:click="$playing=true; startAnimation().then(() => @get('/play'))"
       data-show="!$playing">Play</button>
    <audio id="audio-player" preload="auto">
        <source src="/static/audio.mp3" type="audio/mp3">
        Your browser does not support the audio element.
    </audio>
<script>

function initializeAnimation() {
    const nColumns = %(N_COLUMNS)d ;
    const nRows = %(N_ROWS)d ;
    // Monospace char cells are roughly 0.6 * fontSize wide.
    // This varies by font — if the display looks too wide or narrow, tweak this (try 0.55–0.65).
    const charWidthRatio = 0.6;

    // Must match the CSS line-height on #ascii-display
    const lineHeight = 1.1;
    // derive aspect ratio from actual frame dimensions and character cell shape
    // pixel width  = nColumns * fontSize * charWidthRatio
    // pixel height = nRows * fontSize * lineHeight
    const aspectRatio = (nColumns * charWidthRatio) / (nRows * lineHeight);
    function adjustDisplaySize() {
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;
        const asciiDisplay = document.getElementById('ascii-display');

        let displayWidth = windowWidth;
        let displayHeight = windowWidth / aspectRatio;

        if (displayHeight > windowHeight) {
            displayHeight = windowHeight;
            displayWidth = displayHeight * aspectRatio;
        }

        // fontSize such that nColumns * charWidthRatio * fontSize = displayWidth
        const fontSize = displayWidth / (nColumns * charWidthRatio);
        asciiDisplay.style.fontSize = `${fontSize}px`;
    }

    adjustDisplaySize();
    window.addEventListener('resize', adjustDisplaySize);
    // wake lock?
    // const audioPlayer = document.getElementById('audio-player');
    // audioPlayer.load();
 }

 document.addEventListener('DOMContentLoaded', () => initializeAnimation())

 // Resolves once the audio element has actually begun playback, so the
 // caller can start the SSE frame stream in sync with the first audio sample.
 async function startAnimation() {
   const audioPlayer = document.getElementById('audio-player');
   await audioPlayer.play();
}
</script>
</body>
    </html>""" % {'N_ROWS':N_ROWS, 'N_COLUMNS': N_COLUMNS} ) # need to double % to escape




# want to push a new ascii frame as SSE every 1/30 second
# calling this triggers the push
@bolt.get("/play")
@no_compress
async def play(request):
    async def generate_frames():
        loop = asyncio.get_event_loop()
        start = loop.time()
        for ii in range(N_FRAMES):
            offset = ii * FRAME_SIZE
            frame = _frame_mm[offset:offset + FRAME_SIZE].decode('ascii')
            yield SSE.patch_elements(f"""<div id="ascii-inner">{escape(frame)}</div>""")
            next_time = start + (ii + 1) * DELAY
            sleep_dur = next_time - loop.time()
            if sleep_dur > 0:
                await asyncio.sleep(sleep_dur)

    return StreamingResponse(
        generate_frames(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


bolt.mount_django("/")  # have django-bolt serve the django app as asgi

if __name__ == '__main__':
    # needs to be imported after other things are configured
    # (single-file django app style)
    import sys # noqa: E402
    from django.core.management import (  # noqa: E402
        execute_from_command_line,
    )
    execute_from_command_line(sys.argv)
