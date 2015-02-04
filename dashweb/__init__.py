import os

modules = (m.rstrip('.py') for m in os.listdir(os.path.dirname(__file__)) if \
         not m.startswith('.') and all(w not in m for w in ['__','.pyc']))

for module in modules:
    mod = __import__('.'.join([__name__, module]), fromlist=[module])

#setattr(sys.modules[__name__], cls.__name__, cls)
