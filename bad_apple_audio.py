# /// script
# dependencies = [
#  "nanodjango-bolt @ git+https://github.com/cleemesser/nanodjango-bolt.git",
#  "datastar_py"
# ]
# ///
# also requires data downloads
# - frameData.zip to be downloaded to same directory
# - bad_apple.mp3 to ./static/bad_apple.mp3
#
# should be able to run with pipx bad_apple_audio.py runbolt
# OR uv run bad_apple_audio.py runbolt
# %%
import asyncio
import sys
import pathlib

# %%
from nanodjango import Django
from nanodjango_bolt import BoltAPI
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

sys.path.insert(0, "frameData.zip")
from frameData import frames
DELAY = 1.0 / 30  # 30 fps


index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bad Apple nanodjango-bolt SSE latency test</title>
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
            top: 50%; /* Position it vertically in the center */
            left: 50%; /* Position it horizontally in the center */
            transform: translate(-50%, -50%); /* Correct for the button's own size */
        }
    </style>
<script type="module" src="https://cdn.jsdelivr.net/gh/starfederation/datastar@v1.0.0/bundles/datastar.js"></script>
</head>
<body data-signals:playing="false">
    <div id="ascii-display"><div id="ascii-inner"></div></div>
    <button id="play-button" data-on:click="player=document.getElementById('audio-player'); $playing=true; player.play(); @get('/play')" data-show="!$playing">Play</button>

    <audio id="audio-player" >
        <source src="static/bad_apple.mp3" type="audio/mp3">
        Your browser does not support the audio element.
    </audio>


<script>

function initializeAnimation() {
    // console.log('initializeAnimation start');

    // const frameCount = framesData.length;  // Total number of frames
    // const fps = 30;  // Frames per second
    // const frameDuration = 1000 / fps;  // Duration of each frame in milliseconds
    const audioPlayer = document.getElementById('audio-player');
    const playButton = document.getElementById('play-button');
    let currentFrame = 0;


    // 4:3 aspect ratio dimensions
    const aspectRatio = 4 / 3;

    // Function to adjust the size of the ASCII display while maintaining aspect ratio
    function adjustDisplaySize() {
        // console.log('adjustDisplaySize()')
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;
        const asciiDisplay = document.getElementById('ascii-display')
        // Set the width and height based on the aspect ratio
        let displayWidth = windowWidth;
        let displayHeight = windowWidth / aspectRatio;

        // If the height exceeds the window height, adjust accordingly
        if (displayHeight > windowHeight) {
            displayHeight = windowHeight;
            displayWidth = displayHeight * aspectRatio;
        }

        // Adjust font size based on the calculated display size
        const fontSize = displayWidth / 62;  // Adjust this value to fine-tune the size

        asciiDisplay.style.fontSize = `${fontSize}px`;
    }


    // Call the function initially and on window resize
    adjustDisplaySize();
    window.addEventListener('resize', adjustDisplaySize);
    // wake lock?
    audioPlayer.load();
}
// console.log('about to call initializeAnimation');
document.addEventListener('DOMContentLoaded', () => {
  // console.log('DOM ready');
  initializeAnimation();
})

function startAnimation() {
   const audioPlayer = document.getElementById('audio-player');
   setTimeout( () => {
      audioPlayer.play();  // Play the audio after the delay
      // playAnimation();  // Start the animation after the same delay
   }, 250);  // Delay both for sync

}
</script>
</body>
</html>
"""


@app.route("/")
def index(request):
    return HttpResponse(index_html)


# want to push a new ascii frame as SSE every 1/30 second
# calling this triggers the push
@bolt.get("/play")
@no_compress
async def play(request):
    async def generate_frames():
        loop = asyncio.get_event_loop()
        start = loop.time()
        for ii, frame in enumerate(frames):
            yield SSE.patch_elements(f"""<div id="ascii-inner">{frame}</div>""")
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
    from django.core.management import (  # noqa: E402
        execute_from_command_line,
    )

    execute_from_command_line(sys.argv)
