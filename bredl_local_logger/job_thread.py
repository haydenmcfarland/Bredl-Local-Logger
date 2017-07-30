from threading import Thread, Event
from datetime import datetime
from time import time
import codecs
import os

CHUNK_SIZE = 1024
IRC_MESSAGE_SEND_LIMIT = 30


class Counter:
    def __init__(self):
        self._count = 0

    def __call__(self):
        temp = self._count
        self._count += 1
        return temp


class StoppableThread(Thread):
    def __init__(self):
        super().__init__()
        self._break = False

    def stop(self):
        self._break = True


class RecvThread(StoppableThread):
    def __init__(self, socket, channel):
        super().__init__()
        self._counter = Counter()
        self._socket = socket
        self._channel = channel
        self._buffer = ''
        self.messages = []
        self.event = Event()

    def _recv_utf(self):
        return self._socket.recv(CHUNK_SIZE).decode('utf-8')

    def _recv_messages(self):
        self._buffer += self._recv_utf()
        messages = self._buffer.split('\r\n')
        self._buffer = messages.pop()
        self.event.wait()
        self.messages.append((self._counter(), messages))

    def run(self):
        while True:
            if self._break:
                break
            self._recv_messages()


class SendThread(StoppableThread):
    def __init__(self, socket, channel, twitch_irc):
        super().__init__()
        self._socket = socket
        self._channel = channel
        self._start = None
        self._count = 0
        self._message_limit = IRC_MESSAGE_SEND_LIMIT
        self.send_buffer = []
        self._twitch_irc = twitch_irc
        self.event = Event()

    def _send_utf(self, message):
        self._socket.send('{}\r\n'.format(message).encode('utf-8'))
        self._count += 1

    def _send_privmsg(self, message):
        self._send_utf("PRIVMSG #{} :{}".format(self._channel, message))

    def _period_check(self):
        curr_time = time()
        if not self._start or curr_time - self._start >= 30:
            self._start = curr_time
            self._count = 0
        return self._count < self._message_limit

    def _send_message(self, message):
        if 'PONG' in message:
            self._send_utf(message)
        else:
            self._send_privmsg(message)

    def _process_send_buffer(self):
        while self.send_buffer:
            if self._period_check():
                self.event.wait()
                self._send_message(self.send_buffer.pop(0))

    def run(self):
        while True:
            if self._break:
                break
            self._process_send_buffer()


class LocalLoggerThread(StoppableThread):
    def __init__(self, channel):
        super().__init__()
        self._channel = channel.lower()
        self._messages = []
        self._create_db_entry()

    def _create_db_entry(self):
        if not os.path.exists(self._channel):
            os.makedirs(self._channel)

    def log(self, message, meta_data=None):
        if meta_data:
            self._messages.append([message, meta_data])
        else:
            self._messages.append([message])

    def _commit_messages(self):
        date = datetime.utcnow().strftime('%Y_%m_%d')
        with codecs.open('{}/{}.txt'.format(self._channel, date), 'a', 'utf-8-sig') as log:
            for m in self._messages:
                log.write(str(m)+'\r\n')
        self._messages = []

    def run(self):
        while True:
            while self._messages:
                self._commit_messages()
            if self._break:
                break
