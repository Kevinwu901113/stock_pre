#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/wjk/workplace/stock')

from config.database import Base as ConfigBase
from backend.app.models.stock import Base as ModelBase

print('Config Base:', ConfigBase)
print('Model Base:', ModelBase)
print('Are they the same?', ConfigBase is ModelBase)

# Check if there are multiple Base classes
print('\nChecking Base class attributes:')
print('Config Base registry:', hasattr(ConfigBase, 'registry'))
print('Model Base registry:', hasattr(ModelBase, 'registry'))

# Check the actual class
print('\nConfig Base class:', type(ConfigBase))
print('Model Base class:', type(ModelBase))