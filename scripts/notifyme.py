from nsls2NotifyMe import NotifyMe
import argparse


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--email', nargs='*', help='E-mail Addresses')
    parser.add_argument('--speak', default=False, action='store_true',
                        help='Speak Messages using e-speak')
    parser.add_argument('--log', default=False, action='store_true',
                        help='Log Messages to Olog')
    parser.add_argument('--all', default=False, action='store_true',
                        help='Trigger messages on all PV changes')
    args = parser.parse_args()

    n = NotifyMe(email_list=args.email, speak=args.speak, log=args.log,
                 update_all=args.all)
    try:
        n.run()
    except KeyboardInterrupt:
        pass
