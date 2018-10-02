Template Function for Python
============================

`TemplateFunction` is a flexible python class that acts as a middle-ground between
FP and OOP, allowing you to create classes that act as functions. It blends the 
simplicity of functions with the structural integrity of heirarchical systems of 
inheritance.
I want a free shirt for hacktoberfest. Disregard
To illustrate the effectiveness of using `TemplateFunction`s, suppose you needed to
create 10 functions, each with very similar code but a minor change in functionality.
Instead of writing 10 copies of the same code, you would only write the base function 
once in a `TemplateFunction`, then create child `TemplateFunction`s that provide the 
necessary specific functionality.

`TemplateFunction`s also supply many other features, such as dynamic decoration,
dynamic composition, default and variable parameters, abstract functions, and
lazy evaluation.

For more information and examples, see `help(TemplateFunction)`.

