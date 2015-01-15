from .meta import TemplateFunctionMeta
from .packet import PacketEvaluator

import inspect

__all__ = ["TemplateFunction"]

class TemplateFunction(metaclass=TemplateFunctionMeta):
	r"""
	A parent class that can be subclassed to create functional classes.

	In short, any class that inherits from TemplateFunction becomes purely functional, disallowing 
	instance creation entirely. The class becomes a function which can be called normally like any
	normal function. The method the class must implement to be called is ``__call__``.

	To illustrate:
	----
	>>> class PrintHello(TemplateFunction):
			def __call__(cls):
				print("Hello world!")

	>>> PrintHello()
	Hello world!
	----

	Notice that ``__call__`` takes one parameter, 'cls'. TemplateFunctions implicitly send in
	themselves as the first parameter. This is demonstrated by the following example:

	----
	>>> class PrintMyName(TemplateFunction):
			def __call__(cls):
				print(cls.__name__)

	>>> PrintMyName()
	PrintMyName
	----

	This binding of the class to the call allows class-wide static variables to be accessed
	easily inside the function body. Thus illustrates the main purpose of TemplateFunctions;
	using a TemplateFunction allows creation of functions which can be subclassed to use
	the same code as a parent function, but with different static variables defined.

	To illustrate:
	----
	>>> class PrintThing(TemplateFunction):
		thing = ""
		def __call__(cls):
			print(cls.thing)

	>>> class PrintHello(PrintThing):
		thing = "Hello world!"

	>>> class PrintWassup(PrintThing):
		thing = "Wassup?"

	>>> PrintHello()
	Hello world!
	>>> PrintWassup()
	Wassup?

	----

	Using this structure we have just created three functions with slightly differing
	functionalities while complementing the DRY principle (Don't Repeat Yourself). This
	can be used to create hierarchical structures of functions which simplify the act
	of writing and rewriting similar code.

	-----------------------------------------------------------------------------------------
	========================
	**NOTES ON SUBCLASSING**
	========================

	Subclassing multiple TemplateFunctions can be useful in specific scenarios, however
	note that the ``__call__`` method that will be called will be the first one found in
	the MRO of the class (if of course, the class doesn't implement it's own ``__call__``).

	Subclassing non-TemplateFunction classes can be done without harm, however it should be
	noted that this will not override the functionality of calling the class. For example,
	if a TemplateFunction inherits from ``int``, then it will have access to ``int``'s
	``__dict__`` and methods, but it will not allow you to create instances of the class.

	When subclassing a class with a custom metaclass, it will always raise a TypeError Unless
	the subclassed metaclass is a submetaclass of TemplateFunctionMeta. Alternatively, a
	``mediator_meta`` could be used to dynamically create a new metaclass which inherits from
	both TemplateFunctionMeta and the new inherited metaclass. For more information, see
	``mediator_meta``.

	-----------------------------------------------------------------------------------------
	=================================
	**DEFAULT & VARIABLE PARAMETERS**
	=================================

	TemplateFunctions have a special functionality when dealing with keyword-default
	parameters. If the default value of a keyword-default parameter is set to PARAM_DEFAULT,
	then the class will default to using the static variable with the same name.

	To illustrate:
	----
	>>> class PrintThing(TemplateFunction):
			thing = "Hello"
			def __call__(cls, thing=PARAM_DEFAULT):
				print(thing)

	>>> PrintThing()
	Hello

	----

	When subclassing TemplateFunctions with a PARAM_DEFAULT parameter, the function
	will attempt to use the first instance of ``thing`` (or whatever parameter name
	one choses) that it finds in the class' MRO. 

	If a TemplateFunction uses a PARAM_DEFAULT parameter and the parameter can be
	found nowhere in the class scope, then a warning will be raised upon calling
	the class, stating that class functionality may not be what was expected because
	no default value was assigned to the parameter.

	If a PARAM_DEFAULT parameter's accompanying static variable is set to
	PARAM_VARIABLE, then the parameter will become a normal argument. Continuing
	from the example above:
	----
	>>> ...
	>>> class PrintAnything(PrintThing):
			thing = PARAM_VARIABLE

	>>> PrintAnything("Hello")

	----

	Notice now our TemplateFunction has ``thing`` as a required argument, whereas
	before it was a keyword-default argument.

	NOTE: Be careful when using PARAM_VARIABLE; for it to work properly the
	keyword-default parameter that is set to PARAM_VARIABLE must come FIRST.
	TemplateFunction will not alter the bytecode required to shift around
	the parameters.

	-----------------------------------------------------------------------------------------
	===========================
	**UNIMPLEMENTED FUNCTIONS**
	===========================

	TemplateFunctions support an optional behaviour called "unimplemented".
	A TemplateFunction marked as "unimplemented" cannot be called directly,
	it must be called by a subclass of the function which "implements" the
	function with necessary functionality. An unimplemented function will
	raise a NotImplementedError when called.

	There are three ways a class can be marked as unimplemented:

	(1). Explicitly set the ``__unimplemented__`` variable to True
	     in the class scope.

	(2). Set the "unimplemented" flag to True in the optional flags
	     parameter (discussed later, see FLAGS).

	(3). Provide no ``__call__`` method in either the class or any
	     of it's parent classes.

	If (3) is true and there isn't a single ``__call__`` method implemented
	in either the class or it's parents, then it will automatically be set
	to unimplemented.

	-----------------------------------------------------------------------------------------
	===========================
	**DECORATORS & UNWRAPPING**
	===========================

	Directly decorating the ``__call__`` method can be dangerous, especially
	in situations where ``__call__`` has a PARAM_DEFAULT parameter. Some problems
	which can arise from directly decorating ``__call__`` are:

	(1). Complete loss of functionality; if a decorator returns a function with
	     different metadata from the original ``__call__`` (i.e. a different name),
	     then it will be completely skipped over by the metaclass.

	(2). Failure to recognize and replace PARAM_DEFAULT parameters. More commonly,
		 a decorator returns a new function whose arguments are set to ``*args``
		 and ``**kwargs`` so as to be general for any function. However, if a
		 PARAM_DEFAULT parameter was present in the original, function, it will
		 fail to be recognized by TemplateFunctionMeta (because the new decorated
		 ``__call__`` has only ``*args`` and ``**kwargs``).

	In order to fix this, one can create a static variable ``__decorators__`` in 
	the class scope, or can set the "decorators" flag (see FLAGS). This must be
	a container of the decorators that should be applied to the TemplateFunction.

	To illustrate:
	-----
	>>> import functools
	>>> def decorator(func):
			@functools.wraps(func)
			def wrapper(*args, **kwargs):
				print("I'm a useful wrapper.")
				return func(*args, **kwargs)
			return wrapper

	>>> class PrintThing1(TemplateFunction):
			__decorators__ = (decorator, )

			def __call__(cls):
				print("Hey")

	>>> class PrintThing2(TemplateFunction, flags={
		"decorators": (decorator, )
		}):

		def __call__(cls):
			print("Wassup?")

	----

	After creation of the class, it's decorators (in order) can be accessed via
	the ``decorators`` property (however they cannot be reset).

	If a TemplateFunction inherits from parents that are wrapped by one or more
	decorators, then the child class can have it's ``__call__`` method "unwrapped"
	from the decorators applied to the parent ``__call__``. This can be done by
	setting the "unwrap_level" flag to an integer value determining how many times
	the function is to be unwrapped. This value may also be set to ``UNWRAP_ALL``
	in order to completely unwrap ``__call__`` from all decorators applied to it.

	Unwrapping TemplateFunctions can also be done on the fly by applying the invert
	operator ``~``. Assuming ``Decorated`` is some TemplateFunction wrapped by two
	decorators, ``~(~Decorated)`` would return a new TemplateFunction without any
	decorators.

	FLAGS
	=====
	TemplateFunctions can also optionally be created with a ``flags`` parameter
	in the class definition, which must be a dictionary containing the flags.

	For example:
	----
	>>> class UnimplementedFunction(TemplateFunction, flags={
		'unimplemented': True
		}):
		def __call__(cls):
			print("This shouldn't happen!")

	----

	The currently supported flags are:

	>> "unimplemented" :: bool :: Whether or not the function may be called
		normally (False) or raise an error upon being called (True).
		Equivalent Attribute: ``__unimplemented__``

	>> "decorators" :: container :: A container of function decorators that
		are to be applied to the TemplateFunction.
		Equivalent Attribute: ``__decorators__``

	>> "unwrap_level" :: int or UNWRAP_ALL :: The number of times a function 
		is to be unwrapped from it's parent decorators.
		Equivalent Attribute: N/A

	-----------------------------------------------------------------------------------------
	===========
	**PACKETS**
	===========

	TemplateFunctions support a sort of "lazy evaluation" method called Packet
	Evaluation. A Packet of a function is an object that carries around a function
	and a set of arguments, and when called returns the result of calling the
	function with the given arguments. Packets can be created on any TemplateFunction
	by calling it's ``make_packet`` function and supplying it with the arguments
	to be bound to the packet.

	To demonstrate:
	----
	>>> class MathFunction(TemplateFunction):
			def __call__(cls, x, y, z):
				return x**(y - z) + z/x + 8*(x + y)

	>>> packet = MathFunction.make_packet(1, 2, 3)
	>>> packet()
	28.0
	>>> packet()
	28.0
	>>> packet.function
	<TemplateFunction:: 'MathFunction' at 0x2339570>

	----

	Packets by default are set to memoize the result of calling them. If this
	behaviour is not wanted (if for example, the packet's function has side-effects),
	then one can call ``packet.set_memoize`` to set the memoization state. For
	more information, see ``PacketEvaluator``.

	-----------------------------------------------------------------------------------------
	===============
	**COMPOSITION**
	===============

	Two TemplateFunctions may be composed by combining them via the * operator.
	Mathematically, the composition of two functions `f` and `g` (denoted `f o g`)
	is described as the function such that:

		`(f o g)(x) = f(g(x))`

	Similarly, the composition of a TemplateFunction `a` and another `b` results in
	a new function which, when called, calls `b` first with the arguments passed in,
	then takes the result of calling `b` and passes it into `a`.

	The result of `b` is passed directly into `a` as a single parameter, not as
	*varargs or **varkws. If `b` returns a tuple and a dictionary (the usual format
	for function parameters), it will be sent into `a` as a single parameter.

	If it is necessary for `a` to get passed the result of `b` as *varargs and **varks,
	then the ** operator can be used to compose `a` and `b`. The result of `b` is ALWAYS
	EXPECTED to be a tuple and a dictionary, even if `a` takes no keyword arguments (in
	which case the dictionary should be empty).

	If necessary, one can define a new TemplateFunction whose ``__call__`` is the
	composition of two functions.

	For example:
	----
	>>> class MathFunc1(TemplateFunction):
			def __call__(cls, a, b):
				return a + b

	>>> class MathFunc2(TemplateFunction):
			def __call__(cls, a):
				return 8*a

	>>> class MathFunc3(TemplateFunction):
			__call__ = MathFunc2 * MathFunc1

	>>> MathFunc3(4, 5)
	72

	----

	-----------------------------------------------------------------------------------------
	=======================================
	**USING TEMPLATE FUNCTIONS AS METHODS**
	=======================================

	The only thing to note about template functions used as methods in classes is that
	the ``self`` parameter should always be second to the ``cls`` parameter. Other than
	that, TemplateFunctions can be used just like normal methods, staticmethods,
	classmethods, and properties.

	-----------------------------------------------------------------------------------------
	===============
	**OTHER NOTES**
	===============

	Attribute access on TemplateFunctions works by first checking if an attribute is
	accessible as a class attribute, then checking if is accessible as an attribute of
	the ``__call__`` method. Setting attributes works in reverse; if the attribute being
	set is found to be an attribute of ``__call__``, it is set to ``__call__`` first,
	otherwise it becomes a class attribute.

	One can access the parameter information about a TemplateFunction by using it's
	``parameters`` property, which will return the same thing as ``inspect.getfullargspec``.

	"""

	@classmethod
	def make_packet(cls, *args, **kwargs):
		"""
		Return a packet for the given *args and **kwargs.
		"""
		return PacketEvaluator(cls, (args, kwargs))

	@classmethod
	def signature(cls):
		return inspect.signature(cls.__call__)