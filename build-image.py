#!/usr/bin/python3

import argparse
import yaml
import os
import sys
import subprocess
import semver
import hashlib
import datetime

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def _c(color, t):
    c = getattr(bcolors, color.upper())
    return "%s%s%s" % (c, t, bcolors.ENDC)

class Tag(object):
    def __init__(self, major, minor, patch):
        self.major = major
        self.minor = minor 
        self.patch = patch
    
    @classmethod
    def parse(cls, tag):
        t = tag.split('.')
        if len(t) == 3:
            return cls(t[0],t[1],t[2])
        elif len(t) == 2:
            return cls(t[0],t[1],None)
        elif len(t) == 1:
            return cls(t[0],None,None)
        raise AssertionError('Unable to parse %s' % tag)

parser = argparse.ArgumentParser()
parser.add_argument('-f','--repofile', default='repo.yml')
parser.add_argument('-p','--push', default=False, action='store_true')
parser.add_argument('-c','--containerfile', default=None)
parser.add_argument('-r','--release', default=False, action='store_true')
parser.add_argument('--cmd', required=False, default='docker')
parser.add_argument('directory')


args = parser.parse_args()

if args.containerfile is None:
    if os.path.exists('Containerfile'):
        containerfile = 'Containerfile'
    elif os.path.exists('Dockerfile'):
        containerfile = 'Dockerfile'
    else:
        raise AssertionError('Unable to locate Containerfile or Dockerfile')
else:
    containerfile = args.containerfile
    if not os.path.exists(containerfile):
        raise AssertionError('Unable to locate %s' % containerfile)

os.chdir(args.directory)

if not os.path.exists(args.repofile):
    print(_c('fail', "%s not found" % args.repofile))
    sys.exit(2)

with open(args.repofile, 'r') as f:
    conf = yaml.safe_load(f)

repo = conf.get('repo', None)
repos = conf.get('repos', [])
target = conf.get('target', None)
tag = str(conf['tag'])

stag = Tag.parse(tag)

now = datetime.datetime.now()
today = now.strftime("%Y%m%d")
utcnow = datetime.datetime.utcnow()
build = (utcnow.hour * 60) + utcnow.minute

build = '%s.%s' % (today, build)

def build_image(args, stag, repo_url, target=None):
    tags = []   
    if args.release:
        tags.append('%s:latest' % repo_url)
        if stag.patch is not None:
            tags.append('%s:%s.%s.%s-%s' % (repo_url, stag.major, stag.minor, stag.patch, build))
            tags.append('%s:%s.%s.%s' % (repo_url, stag.major, stag.minor, stag.patch))
            tags.append('%s:%s.%s' % (repo_url, stag.major, stag.minor))
            tags.append('%s:%s' % (repo_url, stag.major))
        elif stag.minor is not None:
            tags.append('%s:%s.%s-%s' % (repo_url, stag.major, stag.minor, build))
            tags.append('%s:%s.%s' % (repo_url, stag.major, stag.minor))
            tags.append('%s:%s' % (repo_url, stag.major))
        else:
            tags.append('%s:%s-%s' % (repo_url, stag.major, build))
            tags.append('%s:%s' % (repo_url, stag.major))
    else:
        tags.append('%s:development' % repo_url)
    
    print(_c('okblue', "+ Building %s" % repo_url))
    cmd = [args.cmd, 'build', '-f', containerfile]
    if target:
        cmd += ['--target', target]
    
    for t in tags:
        cmd += ['-t', t]
    cmd.append('.')
    
    out = subprocess.Popen(cmd).wait()
    if out != 0:
        raise ChildProcessError(' '.join(cmd))
    
    if args.push:
        for t in tags:
            print(_c('okblue', '+ Pushing %s' % t))
            cmd = [args.cmd, 'push', t]
            out = subprocess.Popen(cmd).wait()
            if out != 0:
                raise ChildProcessError(' '.join(cmd))
        for t in tags:
            print(_c('okgreen', 'Pushed %s' % t))
    
if repo:
    build_image(args, stag, repo, target)

if repos:
    for r in repos:
        build_image(args, stag, r['url'], r.get('target', None))

with open(args.repofile, 'w') as f:
    yaml.safe_dump(conf, f)
