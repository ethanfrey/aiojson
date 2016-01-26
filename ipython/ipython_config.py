c = get_config()

c.InteractiveShellApp.extensions = [
    'await'
]

#c.InteractiveShellApp.exec_lines = [
#    'import aiocouchdb'
#]

c.InteractiveShell.editor = 'vim'
