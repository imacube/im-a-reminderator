import argparse, signal, sys

from datetime import date, datetime, time, timedelta
from subprocess import Popen, TimeoutExpired
from time import sleep
from threading import Event, Thread

import yaml

from tkinter import Tk
from tkinter import ttk, Label


def parse_the_args():
    """
    Parse the arguments from the command line.
    """
    parser = argparse.ArgumentParser(description='Simple program to send reminders')
    parser.add_argument('-m, --message', type=str, required=False, metavar='<message>',
            dest='message',
            help='Message to display')
    parser.add_argument('--config', type=str, required=False, metavar='<config.yaml>',
            default='config.yaml',
            dest='config',
            help='Configuration file to load')
    parser.add_argument('-c', required=False,
            action='store_true',
            dest='child',
            help='Set if this will display a popup window')
    parser.add_argument('-p', type=str, required=False, metavar='<python>',
            dest='python', default='python',
            help='Set the name or path of the python to call')
    args = parser.parse_args()
    return args

class Ticker(Label):
    """
    Provides a self updating countdown as a label.
    """
    def __init__(self, parent=None, duration=30):
        super().__init__(parent)

        self.duration = duration
        self.tick()

    def tick(self):
        self.time = 'Will close in {}'.format(self.duration)
        self.configure(text=self.time)
        self.after(1000, self.tick)
        if self.duration > 0:
            self.duration -= 1


class Notifier():
    """
    Creates the message GUI to be displayed.
    """
    def __init__(self, message, duration=60):
        super().__init__()

        self.message = message
        self.duration = duration

    def run(self):
        root = Tk()
        frm = ttk.Frame(root, padding=10)
        frm.grid()
        label = ttk.Label(frm, text=self.message).grid(column=0, row=0)
        ticker = Ticker(frm, self.duration).grid(column=0, row=1)
        ttk.Button(frm, text="Ok", command=root.destroy).grid(column=0, row=2)
        root.after(self.duration * 1000, root.destroy)
        root.mainloop()


class Popup(Thread):
    """
    Handles repetative popup messages.
    """

    def __init__(self, event, python, message='Message not set', interval=10, unit='seconds', start_time=None):
        super().__init__()

        self.event = event
        self.message = message
        self.python = python

        if unit == 'minutes':
            self.interval = interval * 60
        else:
            self.interval = interval

        # calculate times to run
        if start_time:
            h, m = start_time.split(':')
            t = time(int(h), int(m))
            d = date.today()
            self.sync(datetime.combine(d, t))
        else:
            self.target_times = None

    def sync(self, initial_time):
        """
        Build 24 hour window of times to use.
        """
        self.target_times = [initial_time + timedelta(seconds=self.interval)]
        while self.target_times[-1] < initial_time + timedelta(days=1):
            self.target_times.append(self.target_times[-1] + timedelta(seconds=self.interval))

    def sleeper(self):
        """
        Sleep between calls
        """
        if self.target_times:
            # If using start_time, then update the values
            now = datetime.now()
            self.target_times = [i + timedelta(days=1) if i < now else i for i in self.target_times]
            target_time = min([i for i in self.target_times if i > now])
        else:
            target_time = datetime.now() + timedelta(seconds=self.interval)

        while datetime.now() < target_time and not self.event.is_set():
            self.event.wait(15)

    def run(self):
        while not self.event.is_set():
            self.sleeper()
            pid = start_child_process(self.python, self.message)

            counter = 0
            while counter < 60+10 and not pid.poll() and not self.event.is_set():
                counter += 1
                try:
                    pid.wait(timeout=1)
                except TimeoutExpired:
                    pass

            if not pid.poll():
                pid.terminate()
                try:
                    pid.wait(timeout=3)
                except TimeoutExpired:
                    pid.kill()


class Dummy(Thread):
    """
    Dummy thread that just starts and sleeps
    
    duration : seconds to run thread
    """
    def __init__(self, duration=5):
        super().__init__()
        self.duration = duration

    def run(self):
        print('thread started for {} seconds'.format(self.duration))
        sleep(self.duration)


def LoadConfig(config_file='config.yaml'):
    """
    Load the configuration file.
    """
    with open(config_file) as in_file:
        return yaml.load(in_file, Loader=yaml.SafeLoader)

def start_child_process(python, message):
    return Popen([python, 'reminder.py', '-m', str(message), '-c'])

def main(python, config_file):
    """
    Called when run on the command line.

    python : name or path of the python to use for subprocesses
    config_file : configuration file to load
    """
    event = Event()
    def handler(signum, frame):
        event.set()
        sys.exit(0)
    signal.signal(15, handler)
    signal.signal(2, handler)

    config = LoadConfig(config_file)
    threads = list()

    for popup in config['popup']:
        pop = Popup(event, python, popup['message'], popup['interval'], popup['unit'], popup.get('start_time', None))
        pop.start()
        threads.append(pop)

    while threads:
        threads = [i for i in threads if i.is_alive()]
        event.wait(15)

    sys.exit()

if __name__ == '__main__':
    args = parse_the_args()
    config_file = args.config
    message = args.message
    python = args.python

    if args.child:
        n = Notifier(message, 60)
        n.run()
        sys.exit(0)

    main(python, config_file)

