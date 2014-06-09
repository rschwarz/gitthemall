#! /usr/bin/env python2
import argparse
from collections import namedtuple
import os.path
import logging
import sys

from sh import git, ErrorReturnCode_1

logging.basicConfig(format='%(levelname)s: %(message)s')

def make_enum(name, values):
    return namedtuple(name, values)._make(values)

Action = make_enum('Action', ('fetch', 'commit', 'pull', 'push'))
TreeState = make_enum('TreeState', ('clean', 'dirty'))
HeadState = make_enum('HeadState', ('up_to_date', 'older', 'newer', 'forked'))

def fail(msg):
    'Fail program with printed message'
    logging.error(msg)
    sys.exit(1)

def goto(repo_path):
    'find repo and change directory'
    repo = os.path.expanduser(repo_path)
    logging.debug('going to %s' % repo)
    if not os.path.isdir(repo):
        fail('No directory at %s!' % repo)
    if not os.path.isdir(os.path.join(repo, '.git')):
        fail('No git repo at %s!' % repo)
    os.chdir(repo)

def act(action):
    'perform given git action (with side effects)'
    assert action in Action
    if action == Action.fetch:
        git.fetch()
    elif action == Action.commit:
        git.add('.', all=True)
        msg = 'auto-commit by gitthemall'
        git.commit(message=msg)
    elif action == Action.pull:
        git.pull(rebase=True)
    else:
        raise NotImplementedError()

def get_tree_state():
    'parse git status and return current tree state'
    for line in git.status(porcelain=True):
        if line.strip():
            return TreeState.dirty
    return TreeState.clean

def is_ancestor(parent, child):
    try:
        git('merge-base', parent, child, is_ancestor=True)
        return True
    except ErrorReturnCode_1:
        return False

def get_head_state():
    local = 'HEAD'
    remote = '@{upstream}'
    if is_ancestor(remote, local):
        if is_ancestor(local, remote):
            return HeadState.up_to_date
        else:
            return HeadState.newer
    else:
        if is_ancestor(local, remote):
            return HeadState.older
        else:
            return HeadState.forked

def update(repo, actions):
    'Update repo according to allowed actions.'
    goto(repo)
    act(Action.fetch)

    # maybe commit?
    if get_tree_state() == TreeState.dirty:
        if Action.commit in actions:
            act(Action.commit)
        else:
            logging.info('Skip repo with dirty tree:')
            for line in git.status(porcelain=True):
                logging.info(line.rstrip())
            return
    assert get_tree_state() == TreeState.clean

    # maybe pull?
    if get_head_state() in [HeadState.older, HeadState.forked]:
        if Action.pull in actions:
            act(Action.pull)
        else:
            logging.info('Skip repo with HEAD behind.')
            return

    # maybe push?
    if get_head_state() == HeadState.newer:
        if Action.push in actions:
            act(Action.push)
        else:
            logging.info('Skip repo with HEAD ahead.')
            return

    assert get_head_state() == HeadState.up_to_date

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
