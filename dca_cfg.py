def cfg():
    import sys
    import os.path

    cfg_path, cfg_name = os.path.join(os.path.expanduser('~'), '.dca/'), 'config'

    # creates the config file if it doesn't exist, then tells the user to fill it out
    if not os.path.exists(cfg_path+cfg_name):
        print('Config does not exist.')
        print('Creating config file at', cfg_path+cfg_name)
        try:
            f = open(cfg_path+cfg_name, 'w')
        except:
            print('Directory does not exist yet. Please create the directory', cfg_path)
            sys.exit(0)
        f.write('eshosts="localhost"\n')
        f.write('username="elastic"\n')
        f.write('password="changeme"')
        f.close()
        print('File has been created with default settings.')
        print('Please replace relevant information into the config file before running dca_setup again.')
        sys.exit(0)

    # importing the python file (does not have a python extension, so import doesn't work)
    import imp
    try:
        config = imp.load_source(cfg_name, cfg_path+cfg_name)
    except:
        print('The config is improperly configured.')
        sys.exit(0)
    if not hasattr(config, 'eshosts'):
        print('The config is missing a property - eshosts')
        sys.exit(0)
    if not hasattr(config, 'username'):
        print('The config is missing a property - username')
        sys.exit(0)
    if not hasattr(config, 'password'):
        print('The config is missing a property - password')
        sys.exit(0)
    return config
