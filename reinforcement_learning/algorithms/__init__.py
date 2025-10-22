"""
Auto-import all algorithm model modules when 'import reinforcement_learning.algorithms' is executed.
This ensures each observation class runs its @register_rl_algorithm decorator.
"""

import pkgutil
import importlib
import pathlib

package = __name__  # e.g., 'reinforcement_learning.algorithms'
package_path = pathlib.Path(__file__).parent

for _, module_name, ispkg in pkgutil.iter_modules([str(package_path)]):
    if not ispkg:
        importlib.import_module(f"{package}.{module_name}")
