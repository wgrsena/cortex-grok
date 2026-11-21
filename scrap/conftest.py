import os
import sys

# o scrap usa o contrato e os modelos do solver (dependência só nessa direção)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "solver"))
