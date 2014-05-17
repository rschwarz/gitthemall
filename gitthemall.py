#! /usr/bin/env python2
import argparse
import os.path
import logging
import sys

from sh import git

logging.basicConfig(format='%(levelname)s: %(message)s')

COMMIT = 'commit'

def fail(msg):
    'Fail program with printed message'
    logging.error(msg)
    sys.exit(1)

def is_dirty():
    'parse git status and return True if tree is clean'
    for line in git.status(porcelain=True):
        if line.strip():
            return True
    return False

def update(repo, actions):
    'Update repo according to allowed actions.'
    repo = os.path.expanduser(repo)
    logging.debug('going to %s' % repo)
    if not os.path.isdir(repo):
        fail('No directory at %s!' % repo)
    if not os.path.isdir(os.path.join(repo, '.git')):
        fail('No git repo at %s!' % repo)
    os.chdir(repo)

    git.fetch()
    if is_dirty():
        if COMMIT in actions:
            pass # TODO: do commit!
        else:
            logging.info('Skip repo with dirty tree:')
            for line in git.status(porcelain=True):
                logging.info(line.rstrip())
            return
    # TODO: handle pull, push

def parse(config):
    'Parse config and yield repos with actions'
    with open(config) as f:
        for line in f:
            items = line.strip().split(',')
            yield items[0], items[1:]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Keep git repos up-to-date.')
    parser.add_argument('config', type=str, help='config file that lists repos')
    parser.add_argument('-v', '--verbose', default=False, action='store_true')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    for repo, actions in parse(args.config):
        update(repo, actions)
