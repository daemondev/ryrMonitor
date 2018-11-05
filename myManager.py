import asterisk.manager
import sys
def handle_shutdown(event, manager):
    print("Recieved shutdown event")
    manager.close()
    # we could analize the event and reconnect here
def handle_event(event, manager):
    print("Recieved event: %s" % event.name)

manager = asterisk.manager.Manager()
try:
    # connect to the manager
    try:
        manager.connect('190.117.113.7')
        manager.login('richar', '@admjds.progressive')
        # register some callbacks
        manager.register_event('Shutdown', handle_shutdown) # shutdown
        manager.register_event('*', handle_event) # catch all
        # get a status report
        response = manager.status()
        manager.logoff()
    except asterisk.manager.ManagerSocketException as e:
        print("Error connecting to the manager: %s" % e.strerror)
        sys.exit(1)
    except asterisk.manager.ManagerAuthException as e:
        print("Error logging in to the manager: %s" % e.strerror)
        sys.exit(1)
    except asterisk.manager.ManagerException as e:
        print("Error: %s" % e.strerror)
        sys.exit(1)
finally:
    manager.close()
