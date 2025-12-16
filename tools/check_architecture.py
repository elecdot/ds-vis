#!/usr/bin/env python3
import ast
import os
import sys
from typing import List, Dict, Set

# --- Configuration ---

# Define Layers
# L0: Primitives (Ops, Exceptions)
# L1: Core Domain (Models, Layout, Scene, DSL, Persistence)
# L2: Renderer Abstraction
# L3: Renderer Implementation
# L4: UI / Application

LAYERS = {
    "L0": ["ds_vis.core.ops", "ds_vis.core.exceptions"],
    "L1": ["ds_vis.core", "ds_vis.persistence", "ds_vis.dsl"], 
    "L2": ["ds_vis.renderers.base", "ds_vis.renderers"], # renderers package itself is L2, but implementations are L3
    "L3": ["ds_vis.renderers.pyside6"],
    "L4": ["ds_vis.ui", "ds_vis.examples"],
}

# Special handling for ds_vis.renderers:
# ds_vis.renderers (the package) is L2.
# ds_vis.renderers.pyside6 is L3.
# We need to ensure ds_vis.renderers.__init__ does not import L3.

# --- Analysis Logic ---

def get_module_name(file_path, src_root):
    rel_path = os.path.relpath(file_path, src_root)
    module_name = os.path.splitext(rel_path)[0].replace(os.sep, '.')
    if module_name.endswith('.__init__'):
        module_name = module_name[:-9]
    return module_name

class ImportVisitor(ast.NodeVisitor):
    def __init__(self, module_name):
        self.module_name = module_name
        self.imports = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append((alias.name, node.lineno))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.level == 0 and node.module:
            self.imports.append((node.module, node.lineno))
        # Handle relative imports roughly
        elif node.level > 0:
            # We can't easily resolve relative imports without full context,
            # but usually relative imports are within the same layer.
            # We'll skip them for this simple check unless we want to be strict.
            pass
        self.generic_visit(node)

def get_layer(module_name):
    # Check specific matches first
    for layer, prefixes in LAYERS.items():
        for prefix in prefixes:
            if module_name == prefix or module_name.startswith(prefix + "."):
                # Disambiguate L0 vs L1 (ds_vis.core.ops vs ds_vis.core)
                # If we found a match, we need to check if there is a MORE specific match in another layer?
                # L0 prefixes are more specific than L1 prefixes in our config.
                # So we should check L0 first.
                return layer
    return None

def get_layer_priority(layer_name):
    return {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}.get(layer_name, -1)

def check_file(file_path, src_root):
    module_name = get_module_name(file_path, src_root)
    
    # Determine source layer
    # We iterate layers in order L0 -> L4 to catch specific prefixes first
    src_layer = None
    for layer in ["L0", "L3", "L2", "L1", "L4"]: # Check L0 (core.ops) before L1 (core), L3 (renderers.pyside6) before L2 (renderers)
        for prefix in LAYERS[layer]:
            if module_name == prefix or module_name.startswith(prefix + "."):
                src_layer = layer
                break
        if src_layer: break
            
    if not src_layer:
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=file_path)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []

    visitor = ImportVisitor(module_name)
    visitor.visit(tree)
    
    violations = []
    for target_module, lineno in visitor.imports:
        # Determine target layer
        target_layer = None
        for layer in ["L0", "L3", "L2", "L1", "L4"]:
            for prefix in LAYERS[layer]:
                if target_module == prefix or target_module.startswith(prefix + "."):
                    target_layer = layer
                    break
            if target_layer: break
            
        if not target_layer:
            # External library or unknown
            if "PySide6" in target_module:
                if src_layer in ["L0", "L1", "L2"]:
                    violations.append(f"{file_path}:{lineno} [Strict] {src_layer} module '{module_name}' imports UI library '{target_module}'")
            continue

        # Check Layer Violation: Lower cannot import Higher
        src_prio = get_layer_priority(src_layer)
        tgt_prio = get_layer_priority(target_layer)
        
        if src_prio < tgt_prio:
            violations.append(f"{file_path}:{lineno} [Layering] {src_layer} module '{module_name}' imports {target_layer} module '{target_module}'")

        # Specific Rule: Renderer Implementation (L3) should not import Models (L1)
        # L3 -> L1 is allowed by layering (3 > 1), but forbidden by specific architecture rule "Don't drag in models"
        if src_layer == "L3" and target_layer == "L1":
            if "core.models" in target_module or "core.layout" in target_module:
                 violations.append(f"{file_path}:{lineno} [Decoupling] Renderer '{module_name}' should not import Domain '{target_module}'")

    return violations

def main():
    src_root = os.path.abspath("src")
    all_violations = []
    
    for root, _, files in os.walk(src_root):
        for file in files:
            if file.endswith(".py"):
                violations = check_file(os.path.join(root, file), src_root)
                all_violations.extend(violations)
                
    if all_violations:
        print("Architecture Violations Found:")
        for v in all_violations:
            print(v)
        # sys.exit(1) # Don't exit with error for this tool run, just report
    else:
        print("Architecture check passed.")

if __name__ == "__main__":
    main()
