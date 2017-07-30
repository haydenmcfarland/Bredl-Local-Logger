
## A local threaded Twitch Chat logger written in Python.
Stripped and gutted from my BredlBot Twitch moderation bot.

### How To Use:

Install:
```
> python setup.py install
```

Import:
```
from bredl_local_logger.bot import BredlThread

if __name__ == '__main__':
    my_meta = ['color', 'display-name', 'emotes', 'sent-ts']
    threads = dict()
    threads['dansgaming'] = BredlThread('dansgaming', twitch_irc=True, meta=my_meta)
    threads['pmsproxy'] = BredlThread('pmsproxy', twitch_irc=False)

    for t in threads:
        print('Starting {} logger.'.format(t))
        threads[t].start()
        print('{} logger running.'.format(t))

    for t in threads:
        threads[t].join()
```

Create a ```config.conf``` file in the same directory as your script with the form:
```
irc.twitch.tv
6667
BOT_NAME
oauth:OAUTH_TOKEN
```
Where ```BOT_NAME``` is the name of your Twitch account and ```OAUTH_TOKEN``` is a generated chat oauth token. An oauth token can be generated [here](http://twitchapps.com/tmi/).

Other:
- Logs are created in the same directory as your script of the form ```{streamer}/{Y_m_d}.txt```.
- ```twitch_irc``` flag determines if meta data is sent to the logger; providing ```meta``` with this flag set to ```False``` does nothing.
