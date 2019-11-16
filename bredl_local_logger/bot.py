from bredl_local_logger.chat_thread import ChatThread


class BredlThread(ChatThread):
    pass


if __name__ == '__main__':
    my_meta = ['color', 'display-name', 'emotes', 'sent-ts']
    threads = dict()
    threads['dansgaming'] = BredlThread(
        'dansgaming', twitch_irc=True, meta=my_meta)
    threads['pmsproxy'] = BredlThread('pmsproxy', twitch_irc=False)

    for t in threads:
        print('Starting {} logger.'.format(t))
        threads[t].start()
        print('{} logger running.'.format(t))

    for t in threads:
        threads[t].join()
