#!/usr/local/bin/python3

#
# logging_manager.py
# AmazonConverter
#
# Created by Eyal Shukrun on 01/18/20.  Copyright 2020. Eyal Shukrun. All rights reserved.
#
import setup
import os
import datetime

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def pr_red(skk): return "\033[91m{}\033[00m" .format(skk) 
    @staticmethod
    def pr_green(skk): return "\033[92m{}\033[00m" .format(skk) 
    @staticmethod
    def pr_yellow(skk): return "\033[93m{}\033[00m" .format(skk) 
    @staticmethod
    def pr_light_purple(skk): return "\033[94m{}\033[00m" .format(skk) 
    @staticmethod
    def pr_purple(skk): return "\033[95m{}\033[00m" .format(skk) 
    @staticmethod
    def pr_cyan(skk): return "\033[96m{}\033[00m" .format(skk) 
    @staticmethod
    def pr_light_gray(skk): return "\033[97m{}\033[00m" .format(skk) 
    @staticmethod
    def pr_black(skk): return "\033[98m{}\033[00m" .format(skk) 

class LoggingManager:

    def __init__(self, verbose_lvl=5, to_file=None):
        """
            Verbose_lvl: level of verbosity
            level 1: prints only critical errors
            level 2: prints also success messages
            level 3: prints warnings 
            level 4: prints processing steps
            level 5: prints everything
        """
        self.verbose_lvl = verbose_lvl
        self.to_file = to_file

        if to_file:
            if not os.path.isdir(os.path.dirname(to_file)):
                print("Location can't be found: ", to_file)
            try:
                open(to_file, 'r', encoding='utf-8').close()
            except FileNotFoundError:
                print("Log file doesn't exist, creating")
                open(to_file, 'w', encoding='utf-8').close()


    def output(self, s, meta=[], verbose_lvl=5):
        """
            Change this function to redirect output
        """
        if self.verbose_lvl >= verbose_lvl:
            if self.to_file:
                with open(self.to_file, 'a', encoding='utf-8') as f:
                    f.write('-----{}-----\n\n'.format(datetime.datetime.now()))
                    try:
                        f.write(s)
                    except UnicodeEncodeError:
                        f.write(s.encode('utf-8').decode('latin-1'))
                    f.write('\n\n')
            else:
                try:
                    print(s, end="")
                except Exception as e:
                    print(s.encode('utf-8'), end="")
                    print("Error >>>")
                    import ipdb; ipdb.set_trace()

    def msg(self, *args, sep=" ", end="\n", starter="", color_f=None):

        s = starter

        for arg in args:
            if not arg:
                continue
            s += str(arg)
            s += sep

        s += end

        if color_f:
            s = color_f(s)

        return s

    def log_msg(self, *args, sep=" ", end="\n", verbose_lvl=1):
        self.output(self.msg(*args, sep=sep, end=end), verbose_lvl=verbose_lvl)

    def critical_msg(self, *args, sep=" ", end="\n", nostarter=False, verbose_lvl=1):
        starter = "[!!!] "
        if nostarter: starter = ""
        self.output(self.msg(*args, sep=sep, end=end, starter=starter, color_f=bcolors.pr_red),
                    verbose_lvl=verbose_lvl)

    def err_msg(self, *args, sep=" ", end="\n", nostarter=False, verbose_lvl=1):
        starter = "[!!] "
        if nostarter: starter = ""
        self.output(self.msg(*args, sep=sep, end=end, starter=starter, color_f=bcolors.pr_red),
                    verbose_lvl=verbose_lvl)

    def ok_msg(self, *args, sep=" ", end="\n", nostarter=False, verbose_lvl=2):
        starter = "[v] "
        if nostarter: starter = ""
        self.output(self.msg(*args, sep=sep, end=end, starter=starter, color_f=bcolors.pr_green),
                    verbose_lvl=verbose_lvl)

    def process_msg(self, *args, sep=" ", end="\n", nostarter=False, verbose_lvl=4):
        starter = "[*] "
        if nostarter: starter = ""
        self.output(self.msg(*args, sep=sep, end=end, starter=starter, color_f=bcolors.pr_cyan),
                    verbose_lvl=verbose_lvl)

    def warning_msg(self, *args, sep=" ", end="\n", nostarter=False, verbose_lvl=3):
        starter = "[!] "
        if nostarter: starter = ""
        self.output(self.msg(*args, sep=sep, end=end, starter=starter, color_f=bcolors.pr_yellow),
                    verbose_lvl=verbose_lvl)


logging_mgr = LoggingManager(setup.verbose_lvl)





