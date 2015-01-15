import types

__all__ = ["lzip", "lfilter", "lfilternone", "copy_func", "find_in_bases"]

def lzip(*iterables):
	r"""
	Shorthand for list(zip(*iterables))
	"""
	return list(zip(*iterables))

def lfilter(func, iterable):
	r"""
	Shorthand for list(filter(func, iterable))
	"""
	return list(filter(func, iterable))

def lfilternone(iterable):
	r"""
	Shorthand for list(filter(None, iterable))
	"""
	return list(filter(None, iterable))

def copy_func(func):
	r"""
	Copy the necessary components of a function.
	"""
	return types.FunctionType(
		func.__code__,
		func.__globals__,
		func.__name__,
		func.__defaults__,
		func.__closure__
		)

def find_in_bases(bases, key):
	r"""
	Find an attribute in a set of parent classes.
	"""
	for base in bases:
		val = base.__dict__.get(key)
		if val is None:
			continue
		return val