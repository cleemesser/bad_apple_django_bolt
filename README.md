# Django-Bolt Single File Bad Apple Via SSE
This is an demonstration of 30 fps ServerSideEvent streaming of ascii art version of the [Bad Apple movie](https://www.youtube.com/watch?v=FtutLA63Cp8).
It is a good test of the latency of your server and connection as the audio is being played on the front end and the ascii art
is being streamed into the browser page from the server and morphed into the DOM by datastar.

So this is really just a fun test of the django-bolt server with a single file app.

Note! This is not the way you *should* serve up media as it is very susceptible to interruptions in the network.
It does demonstrate how reactive realtime browser updates can be.



It is inspired by this [datastar demonstration](https://data-star.dev/examples/bad_apple)

## References
Other versions of the movie:
[bad apple movie on youtube](https://youtu.be/FtutLA63Cp8?si=Z7x8UZuOYAfJCATl)

The movie ascii art creator [cascii](https://github.com/cascii/cascii)

[django-bolt PR#208 which adds nanodjango support](https://github.com/dj-bolt/django-bolt/pull/208)

## preparing the ascii media


The app requires pre-generated frame data that is not produced by this repo —
[cascii](https://github.com/cascii/cascii) is the external renderer.

### get the movie
- `download-bad-apple.py` — fetches the source video via yt-dlp (hardcoded
  YouTube URL) to the file bad_apple.mp4

### translate it to ascii frames in individual files and the audio.mp3
- `run-cascii.py` — wraps cascii
  by default it will run:
  ```
  cascii bad_apple.mp4 --fps 30 --columns 100
  ```
  `--audio --default` are pinned flags in the script but you can specify your
  own arguments for  `--fps` / `--columns`.

- This produces a directory bad_apple/ with each ascii frame in a files
    "frame_0001.txt", "frame_0002.txt", and so on. The details.toml file
    contains parameters cascii used and audio.mp3 from the movie.

- Note: If cascii isn't on `PATH`, the script tries to download the right
  prebuilt tarball from `github.com/cascii/cascii/releases/latest` into
  `~/.cache/run-cascii/` (macOS/Linux × arm64/x64 only; Windows requires a
  manual `cargo install`). `--install-only` prepares the binary without
  rendering.
  - cascii depends on ffmpeg

### collating the frames into one file, add parameters to details.toml, move
files

- `uv run python process-cascii-output.py`
  - concatenates `bad_apple/frame_*.txt` (sorted **numerically** by the integer
  after the underscore, not lexicographically) into
  `bad_apple/bad_apple_all.txt`
  - appends `frame_size` to `details.toml` if it isn't already there. The app
  slices the blob by fixed `frame_size` offsets, so the concatenation must not
  reorder or change frame widths.
  - Idempotent: if `frame_size` already matches, re-running is a no-op; if it mismatches, the script errors out rather than silently overwriting.

### clean up
- clean up is not automatic: you can delete the frame*.txt files and the
bad_apple/audio.mp3


### Required media at runtime:
-  `bad_apple/bad_apple_all.txt`, `bad_apple/details.toml` (with `frame_size`),
    and `static/audio.mp3`.
