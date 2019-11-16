from bredl_local_logger.config import BredlBase
from bredl_local_logger.job_thread import RecvThread, SendThread, LocalLoggerThread, StoppableThread
from socket import socket, SHUT_WR
import re

# TWITCH
TWITCH_CAPABILITIES = ('membership', 'tags', 'commands')

# REGEX
RE_CHAT = re.compile('(.*):(.+)!.+@.+.tmi.twitch.tv (.+) #.+ :(.+)')
RE_MOTD = re.compile(r'(.*):tmi.twitch.tv 376 (\S+) :(.+)')
RE_PING = re.compile('PING :tmi.twitch.tv')
DEFAULT_META = [
    'color',
    'display-name',
    'mod',
    'emotes',
    'sent-ts',
    'subscriber']

# CONSTANTS
COMMAND = 3
TEXT = 4
USER = 2
TWITCH = 1


class ChatThread(StoppableThread, BredlBase):
    def __init__(self, channel, twitch_irc, meta=DEFAULT_META):
        StoppableThread.__init__(self)
        BredlBase.__init__(self)
        self._socket = socket()
        self._channel = channel.lower()
        self._threads = dict()
        self._meta = meta
        self._threads['Logger'] = LocalLoggerThread(self._channel)
        self._threads['Send'] = SendThread(
            self._socket, self._channel, twitch_irc)
        self._threads['Recv'] = RecvThread(self._socket, self._channel)
        self._twitch_irc = twitch_irc

    def _generate_meta_data(self, twitch_params):
        return dict([j for j in [i.split('=') for i in twitch_params.split(
            ';')] if j[-1] != '' and j[0] in self._meta])

    def _send_utf(self, message):
        self._socket.send('{}\r\n'.format(message).encode('utf-8'))

    def _enable_twitch_irc_capabilities(self):
        for c in TWITCH_CAPABILITIES:
            self._send_utf('CAP REQ :twitch.tv/{}'.format(c))

    def _join_twitch_chat(self):
        self._socket.connect((self._host, self._port))
        self._send_utf("PASS {}".format(self._pass))
        self._send_utf("NICK {}".format(self._nick))
        self._send_utf("JOIN #{}".format(self._channel))
        if self._twitch_irc:
            self._enable_twitch_irc_capabilities()

    def _start_threads(self):
        for t in self._threads:
            self._threads[t].start()

    def _stop_threads(self):
        for t in self._threads:
            self._threads[t].stop()

    def _join_threads(self):
        for t in self._threads:
            self._threads[t].join()

    def _append_send_buffer(self, message):
        self._threads['Send'].event.clear()
        self._threads['Send'].send_buffer.append(message)
        self._threads['Send'].event.set()

    def _pop_recv_buffer(self):
        self._threads['Recv'].event.clear()
        messages_list = self._threads['Recv'].messages
        self._threads['Recv'].messages = []
        self._threads['Recv'].event.set()
        return messages_list

    def _process_messages(self, messages):
        for message in messages:
            if re.match(RE_PING, message):
                self._append_send_buffer('PONG :tmi.twitch.tv')
            else:
                r = re.match(RE_CHAT, message)
                if r and r.group(COMMAND) == "PRIVMSG":
                    chat_msg = '{}: {}'.format(r.group(USER), r.group(TEXT))
                    if self._twitch_irc:
                        meta_data = self._generate_meta_data(r.group(TWITCH))
                        self._threads['Logger'].log(chat_msg, meta_data)
                    else:
                        self._threads['Logger'].log(chat_msg)

    def run(self):
        self._join_twitch_chat()
        self._start_threads()
        while True:
            if self._break:
                self._socket.shutdown(SHUT_WR)
                self._stop_threads()
                break
            messages_list = self._pop_recv_buffer()
            if messages_list:
                for messages in messages_list:
                    self._process_messages(messages[-1])
        self._join_threads()
        self._socket.close()
