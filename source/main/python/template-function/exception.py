import warnings
import enum

__all__ = ["ParameterError", "TFuncWarnings"]

class ParameterError(Exception):
	r"""
	Base exception for parameter based exceptions.
	"""
	pass

class TFuncWarnings(enum.Enum):
	r"""
	The warnings that can be raised by calling a TemplateFunction.
	"""

	call_with_default = \
	"An attempt has been made to call an implemented "
	"function with an undefined default parameter. "
	"Results are indeterminate."

	decorate_with_default = \
	"Decorating a function may result in loss "
	"of default parameter functionality. User "
	"discretion is advised."

	def __init__(self, msg):
		self.msg = msg

	def warn(self):
		warnings.warn("WARNING:: " + self.msg)