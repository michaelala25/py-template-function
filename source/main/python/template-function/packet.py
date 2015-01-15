__all__ = ["PacketEvaluator"]

class PacketEvaluator:
	r"""
	An object that can be used to lazily evaluate a function.

	PacketEvaluators are created by called ``TemplateFunction.make_packet``.
	Their purpose is to bind a function to some specific parameters. When
	called, a packet will return the result of calling the function with
	it's given parameters.

	A PacketEvaluator can also be set to memoize the result of calling
	itself using the ``set_memoize`` method.
	"""
	def __init__(self, func, params):
		self._func = func
		self._params = params
		self._result = None

		self._memoize = True

	def __repr__(self):
		r"""
		X.__repr__() <==> repr(X)
		"""
		return "PacketEvaluator for function <%s>" % self._func.__name__

	def __call__(self):
		r"""
		X.__call__() <==> X()
		"""
		if self._memoize:
			if self._result is None:
				self._result = self._func(*self._params[0], **self._params[1])
			return self._result
		return self._func(*self._params[0], **self._params[1])

	def set_memoize(self, bool):
		r"""
		Set the memoization state.

		True >> Memoize the result of calling the packet.
		False >> Discard the result of calling the packet.
		"""
		self._memoize = bool

	@property
	def function(self):
	    return self._func
	@property
	def parameters(self):
		return self._params