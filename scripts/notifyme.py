from notifyMe import NotifyMe


def main():
    n = NotifyMe()
    try:
        n.run()
    except KeyboardInterrupt:
        pass
