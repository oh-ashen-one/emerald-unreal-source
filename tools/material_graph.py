"""Safe native material graph replacement for installed UE5.8 authoring."""

def clear_material(material,unreal):
    library=unreal.MaterialEditingLibrary
    # Installed DeleteAllMaterialExpressions iterates the expression view while
    # deletion mutates that array. Snapshot first, then verify nothing remains.
    before=library.get_num_material_expressions(material)
    for expression in list(library.get_material_expressions(material)):
        library.delete_material_expression(material,expression)
    remaining=library.get_num_material_expressions(material)
    if remaining:raise RuntimeError('Material graph replacement retained '+str(remaining)+' expressions')
    return before
