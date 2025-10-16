"""
Auto-import all observation model modules when 'import reinforcement_learning.gymnasium_env' is executed.
This ensures each observation class runs its @register_observation_model decorator.
"""

import pkgutil
import importlib
import pathlib

package = __name__  # e.g., 'reinforcement_learning.gymnasium_env'
package_path = pathlib.Path(__file__).parent

for _, module_name, ispkg in pkgutil.iter_modules([str(package_path)]):
    if not ispkg:
        importlib.import_module(f"{package}.{module_name}")
