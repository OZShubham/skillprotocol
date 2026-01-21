import sys

def print_lang_method(name, module):
    if module is None:
        print(f"{name}: [NOT INSTALLED]")
        return
    
    # Look for any attribute containing 'language' (properties or functions)
    methods = [m for m in dir(module) if "language" in m]
    print(f"{name}: {methods}")

print("--- Tree-Sitter Binding Inspection ---\n")

# 1. Python
try:
    import tree_sitter_python
    print_lang_method("Python", tree_sitter_python)
except ImportError:
    print_lang_method("Python", None)

# 2. JavaScript
try:
    import tree_sitter_javascript
    print_lang_method("JavaScript", tree_sitter_javascript)
except ImportError:
    print_lang_method("JavaScript", None)

# 3. TypeScript (Often includes TSX)
try:
    import tree_sitter_typescript
    print_lang_method("TypeScript", tree_sitter_typescript)
except ImportError:
    print_lang_method("TypeScript", None)

# 4. Java
try:
    import tree_sitter_java
    print_lang_method("Java", tree_sitter_java)
except ImportError:
    print_lang_method("Java", None)

# 5. Go
try:
    import tree_sitter_go
    print_lang_method("Go", tree_sitter_go)
except ImportError:
    print_lang_method("Go", None)

# 6. Rust
try:
    import tree_sitter_rust
    print_lang_method("Rust", tree_sitter_rust)
except ImportError:
    print_lang_method("Rust", None)

# 7. C++
try:
    import tree_sitter_cpp
    print_lang_method("C++", tree_sitter_cpp)
except ImportError:
    print_lang_method("C++", None)

# 8. C
try:
    import tree_sitter_c
    print_lang_method("C", tree_sitter_c)
except ImportError:
    print_lang_method("C", None)

# 9. Ruby
try:
    import tree_sitter_ruby
    print_lang_method("Ruby", tree_sitter_ruby)
except ImportError:
    print_lang_method("Ruby", None)

# 10. PHP
try:
    import tree_sitter_php
    print_lang_method("PHP", tree_sitter_php)
except ImportError:
    print_lang_method("PHP", None)

# 11. C# (C-Sharp)
try:
    # Note: Package is often tree-sitter-c-sharp, but module is tree_sitter_c_sharp
    import tree_sitter_c_sharp
    print_lang_method("C#", tree_sitter_c_sharp)
except ImportError:
    print_lang_method("C#", None)