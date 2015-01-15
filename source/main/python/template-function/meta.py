from .utils import lzip, copy_func, find_in_bases
from .constants import *
from .exception import *

import functools
import inspect

__all__ = ["mediator_meta", "TemplateFunctionMeta"]

def mediator_meta(*metaclasses):
	"""
	Return a metaclass that acts as a mediator for multiple metaclasses.

	EXAMPLE
	=======
	----
	>>> class Meta1(type):
			def __new__(metacls, name, bases, kwargs):
				print('metaclass 1')
				return super().__new__(metacls, name, bases, kwargs)

	>>> class Meta2(type):
			def __new__(metacls, name, bases, kwargs):
				print('metaclass 2')
				return super().__new__(metacls, name, bases, kwargs)

	>>> class A(metaclass=mediator_meta(Meta1, Meta2)):
			pass

	metaclass 1
	metaclass 2
	>>>
	----
	"""
	class MediatorMeta(*metaclasses):
		pass
	return MediatorMeta

class TemplateFunctionMeta(type):
	r"""
	The metaclass for a Template Function.
	"""

	def __new__(metacls, name, bases, kwargs, flags={}):

		# Warning registry for special cases.
		# (Special cases outlined by the messages in
		# TFuncWarnings).
		kwargs['_warnings'] = []

		# Find the __call__ function.
		call = kwargs.get('__call__')
		if call is None:
			call = _find_in_bases(bases, '__call__')

		# __unimplemented__ lets us know if a TemplateFunction is a function 
		# which can be called, or simply serves as an abstract base which cannot 
		# be called but instead inherited from and called as child functions.
		#
		# If __unimplemented__ is True, an error will be raised in
		# TemplateFunctionMeta.__call__.
		if call is None:
			kwargs['__unimplemented__'] = True
			return super().__new__(metacls, name, bases, kwargs)
		else:
			if isinstance(call, TemplateFunctionMeta):
				call = call.__function__
			# Copy call so any changes we make to it don't affect the original.
			call = copy_func(call)
			# Move __call__.__doc__ over to class.__doc__. This is just semantic;
			# it just makes the help information more viable to users calling
			# ``help`` on a TemplateFunction.
			if call.__doc__:
				kwargs['__doc__'] = call.__doc__
			elif flags.get('docstring'):
				kwargs['__doc__'] = flags['docstring'].__doc__
			if not (kwargs.get('__unimplemented__') or \
				    flags.get('unimplemented')):
				# Unless the user explicitly stated that the
				# function is to remain unimplemented, set it
				# to be implemented.
				kwargs['__unimplemented__'] = False

		unwrap_level = flags.get('unwrap_level')
		# "Undecorate" a decorated TemplateFunction.
		if unwrap_level:
			if unwrap_level == UNWRAP_ALL:
				while getattr(call, '__wrapped__', None):
					call = getattr(call, '__wrapped__')
			else:
				for i in range(unwrap_level):
					wrapped = getattr(call, '__wrapped__', None)
					if wrapped is None:
						break
					call = wrapped

		# has_defaults is a flag that serves to indicate
		# later whether or not a warning should be raised
		has_defaults = False

		# Handle the specific default parameters 
		# (PARAM_DEFAULT & PARAM_VARIABLE)
		if call.__defaults__:
			# Here we actually change the values of the default parameters
			# depending on what the class-wide variables are.
			arg_names = inspect.getfullargspec(call).args
			defaults = call.__defaults__

			new_defaults = []

			# This funky iterator will iterate through the names of the parameters
			# with default arguments along with their associated default value.
			for attr, val in reversed(lzip(*map(reversed, (arg_names, defaults)))):
				if val not in {PARAM_DEFAULT, PARAM_VARIABLE}:
					new_defaults.append(val)
					continue

				if attr in kwargs:
					val = kwargs[attr]
				else:
					has_defaults = True
					# Check the inherited functions to see if they sport the
					# attribute we're looking for.
					for base in bases:
						val = base.__dict__.get(attr)
						if val is not None:
							break
					if val is None:
						val = PARAM_DEFAULT
						if not kwargs['__unimplemented__']:
							kwargs['_warnings'].append(
								TFuncWarnings.call_with_default
								)
				if val == PARAM_VARIABLE:
					if new_defaults:
						raise ParameterError(
							"Default arguments set to "
							"VARIABLE must come first."
							)
					continue
				new_defaults.append(val)

			call.__defaults__ = tuple(new_defaults)

		# Apply any optional decorators to the function.
		decorators = kwargs.get('__decorators__', flags.get('decorators'))
		if decorators is None:
			decorators = _find_in_bases(bases, '__decorators__')
		if decorators:
			if has_defaults:
				# This actually shouldn't cause any interference with 
				# decorators but it's nice to warn just in case.
				kwargs['_warnings'].append(
					TFuncWarnings.decorate_with_default
					)
			if not isinstance(decorators, (list, tuple)):
				decorators = (decorators, )
			for decorator in decorators:
				old_call = call
				call = decorator(call)
				call.__wrapped__ = old_call

		kwargs['__decorators__'] = decorators if decorators else []

		kwargs['__function__'] = call

		return super().__new__(metacls, name, bases, kwargs)

	# Need to implement this, otherwise type.__init__ is called
	# which will raise a TypeError if flags are supplied.
	def __init__(cls, name, bases, kwargs, flags={}):
		type.__init__(cls, name, bases, kwargs)

	def __call__(cls, *args, **kwargs):
		r"""
		X.__call__(*args, **kwargs) <==> X(*args, **kwargs)
		"""
		if cls.__unimplemented__:
			raise NotImplementedError(
				"'%s' template function is not implemented." %\
				cls.__name__
				)
		if cls._warnings:
			for warning in cls._warnings:
				warning.warn()
		return cls.__function__(cls, *args, **kwargs)

	# This would have to be in TemplateFunctionMeta's metaclass 
	# for it to work anyways.
	#
	# def __instancecheck__(cls, value):
	# 	r"""
	# 	X.__instancecheck__(types) <==> isinstance(X, types)
	# 	"""
	# 	# Urgh, python's ``isinstance`` doesn't actually 
	# 	# call __instancecheck__ for some dumb reason so 
	# 	# this doesn't work, and it is beyond my power to 
	# 	# fix it.
	# 	if types.FunctionType == value or \
	# 	   (isinstance(value, (list, tuple)) and \
	# 	   types.FunctionType in value):
	# 		return True
	# 	return isinstance(cls, value)

	def __getattr__(cls, key):
		r"""
		X.__getattr__(key) <==> X.key
		"""
		# If the attribute in question is part of the class dict,
		# return it. If it is part of the __function__ dict, return
		# that instead (class attributes have higher priorety however).
		try:
			return cls.__dict__[key]
		except KeyError:
			try:
				return cls.__function__.__dict__[key]
			except KeyError:
				raise AttributeError(
					"%s has no attribute '%s'." % \
					(cls.__name__, key)
					)

	def __setattr__(cls, key, val):
		r"""
		X.__setattr__(key, val) <==> X.key = val
		"""
		if key in cls.__function__.__dict__:
			cls.__function__.__dict__[key] = val
		else:
			super().__setattr__(key, val)

	def __get__(cls, instance, owner):
		r"""
		Implement __get__ so TemplateFunctions can be used as methods.
		"""
		wraps = functools.wraps(cls.__function__)
		if instance is None:
			@wraps
			def wrapped(*args, **kwargs):
				return cls.__function__(cls, *args, **kwargs)
		else:
			@wraps
			def wrapped(*args, **kwargs):
				return cls.__function__(cls, instance, *args, **kwargs)
		return wrapped

	def __repr__(cls):
		r"""
		X.__repr__() <==> repr(X)
		"""
		return "<TemplateFunction:: '%s' at 0x%x>" % \
			(cls.__name__, id(cls))

	def __invert__(cls):
		r"""
		X.__invert__() <==> ~X
		"""
		if not hasattr(cls.__function__, '__wrapped__'):
			return cls
		class UnwrappedFunction(TemplateFunction):
			__call__ = cls.__function__.__wrapped__
		return UnwrappedFunction

	def __mul__(cls, other):
		r"""
		X.__mul__(Y) <==> X * Y

		Multiplication of two TemplateFunctions or a TemplateFunction and a 
		normal function will result in a "CompositeFunction", that is, a 
		TemplateFunction that when called first calls the second function,
		then takes the result and feeds it to the first function.

		It can be likened to mathematical functions, whose composition is
		defined as so:

		(composition of f and g)(x) = f(g(x))
		"""
		class CompositeFunction(TemplateFunction):
			def __call__(cls_, *args, **kwargs):
				result = other(*args, **kwargs)
				return cls(result)
		return CompositeFunction

	def __pow__(cls, other):
		r"""
		X.__pow__(Y) <==> X ** Y

		Similar to composing two functions via ``__mul__``, except the
		result of calling ``other`` is interpretted as *args and **kwargs
		to be sent into the first function, as opposed to a lone argument
		that gets passed in when using ``__mul__``.
		"""
		class CompositeFunction(TemplateFunction):
			def __call__(cls, *args, **kwargs):
				nargs, nkwargs = other(*args, **kwargs)
				return cls(*nargs, **nkwargs)
		return CompositeFunction

	@property
	def parameters(cls):
		r"""
		Return the parameters of the function.
		"""
		return inspect.getfullargspec(cls.__function__)

	@property
	def decorators(cls):
		r"""
		Return the decorators applying to the function.
		"""
		return cls.__decorators__
