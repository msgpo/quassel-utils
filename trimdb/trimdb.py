import re
def printf(*args):
    for arg in args:
        arg = re.sub(r'[^\x20-\x7E]', r' ', str(arg))
    print(*args)

from quassel import *

from sqlalchemy import or_
def trim_quassel_db(uri, pruneInfoMessages=True, pruneOrphanSenders=True, olderThanTimestamp=None):
    # olderThanTimestamp: DateTime
    
    session = quassel_session(uri)

    ###############################
    if pruneInfoMessages:
        printf('----')
        printf('Job: DELETE')
        printf('         Nick/Mode')
        printf('         Join/Part/Quit')
        printf('         NetsplitJoin/NetsplitQuit')
        printf('         Notice/Server/Info/Error')
        printf('----')

        query = session.query(Message)
        criterion = [
            or_(\
                Message.type == MessageType.Notice, \
                Message.type == MessageType.Nick, \
                Message.type == MessageType.Mode, \
                Message.type == MessageType.Join, \
                Message.type == MessageType.Part, \
                Message.type == MessageType.Quit, \
                Message.type == MessageType.Server, \
                Message.type == MessageType.Info, \
                Message.type == MessageType.Error, \
                Message.type == MessageType.NetsplitJoin, \
                Message.type == MessageType.NetsplitQuit \
            )
        ]
        if olderThanTimestamp is not None:
            criterion.append(Message.time <= olderThanTimestamp)

        query = query.filter(*criterion)
        count = query.count()
        printf('Found:', count)
        deleted = query.delete()
        printf('Deleted:', deleted)
        session.commit()


    ###############################
    if pruneOrphanSenders:
        printf('----')
        printf('Job: DELETE Ophaned Senders')
        printf('----')

        queryString = 'FROM sender where senderid NOT IN (SELECT message.senderid FROM backlog message)'
        query = session.execute('SELECT COUNT(*) ' + queryString)
        count = query.fetchall()[0][0]
        printf('Found:', count)
        query = session.execute('DELETE ' + queryString)
        session.commit()

        query = session.execute('SELECT COUNT(*) ' + queryString)
        count = query.fetchall()[0][0]
        printf('After:', count)


    session.close()


if __name__ == '__main__':
    import os
    import argparse

    parser = argparse.ArgumentParser(description='Prune Quassel\'s Database')
    
    # Arguments
    parser.add_argument('uri',
                       help='The URI to Quassel\' DB.')
    # parser.add_argument('-t', '--olderThanTimestamp',
    #                    help='Delete things at older than the given unix epoch timestamp.')
    # parser.add_argument('-d', '--daysOld', action='store_none', default=7,
    #                    help='Delete things at least _ days old.')

    # Switches
    parser.add_argument('-i', '--pruneInfoMessages', action='store_true', default=False,
                       help='Delete Notice/Nick/Mode/Join/Part/Quit/Server/Info/Error/NetsplitJoin/NetsplitQuit messages. Keeping Plain/Action/Kick/Kill/Topic/DayChange/Invite messages.')
    parser.add_argument('-s', '--pruneOrphanSenders', action='store_true', default=False,
                       help='Delete sender\'s with no messages.')

    args = parser.parse_args()
    trim_quassel_db(**vars(args))
