#! /usr/bin/env python2
import argparse
from collections import namedtuple
import os.path
import logging
import sys

from sh import git

logging.basicConfig(format='%(levelname)s: %(message)s')

def make_enum(name, values):
    return namedtuple(name, values)._make(values)

Action = make_enum('Action', ('commit', 'pull', 'push'))
TreeState = make_enum('TreeState', ('clean', 'dirty'))

def fail(msg):
    'Fail program with printed message'
    logging.error(msg)
    sys.exit(1)

def goto(repo_path):
    'find repo and change directory'
    repo = os.path.expanduser(repo)
    logging.debug('going to %s' % repo)
    if not os.path.isdir(repo):
        fail('No directory at %s!' % repo)
    if not os.path.isdir(os.path.join(repo, '.git')):
        fail('No git repo at %s!' % repo)
    os.chdir(repo)

def get_tree_state():
    'parse git status and return True if tree is clean'
    for line in git.status(porcelain=True):
        if line.strip():
            return TreeState.dirty
    return TreeState.clean

def update(repo, actions):
    'Update repo according to allowed actions.'
    goto(repo)
    git.fetch()

    tree_state = get_tree_state()
    if tree_state == TreeState.dirty:
        if Action.commit in actions:
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
            repo_path, actions = items[0], items[1:]
            for a in actions:
                if a not in Action:
                    raise ValueError('Unknown action: %s' % a)
            yield repo_path, actions

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Keep git repos up-to-date.')
    parser.add_argument('config', type=str, help='config file that lists repos')
    parser.add_argument('-v', '--verbose', default=False, action='store_true')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    for repo, actions in parse(args.config):
        update(repo, actions)
