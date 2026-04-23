# Django-Bolt Single File Bad Apple Via SSE
This is an demonstration of 30 fps ServerSideEvent streaming of ascii art version of the [Bad Apple movie](https://www.youtube.com/watch?v=FtutLA63Cp8).
It is a good test of the latency of your server and connection as the audio is being played on the front end and the ascii art 
is being streamed into the browser page from the server and morphed into the DOM by datastar.

So this is really just a fun test of the django-bolt server.

This is not the way you *should* serve up media as it is very susceptible to interruptions in the network.
It does demonstrate how reactive realtime browser updates can be.

It is inspired by this [datastar demonstration](https://data-star.dev/examples/bad_apple)
