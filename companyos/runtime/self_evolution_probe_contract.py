from __future__ import annotations

import ast
from pathlib import Path


def _shape(node, skip_bound=False):
    positional_nodes=(
        list(node.args.posonlyargs)
        + list(node.args.args)
    )

    default_start=(
        len(positional_nodes)
        - len(node.args.defaults)
    )

    positional=[]

    for index,arg in enumerate(positional_nodes):
        if skip_bound and index == 0:
            continue

        positional.append({
            "name":arg.arg,
            "required":index < default_start,
            "positional_only":
                index < len(node.args.posonlyargs),
        })

    kwonly=[]

    for arg,default in zip(
        node.args.kwonlyargs,
        node.args.kw_defaults,
    ):
        kwonly.append({
            "name":arg.arg,
            "required":default is None,
        })

    return {
        "positional":positional,
        "kwonly":kwonly,
        "vararg":node.args.vararg is not None,
        "varkw":node.args.kwarg is not None,
    }


def _is_static(node):
    for dec in node.decorator_list:
        if (
            isinstance(dec,ast.Name)
            and dec.id=="staticmethod"
        ):
            return True

        if (
            isinstance(dec,ast.Attribute)
            and dec.attr=="staticmethod"
        ):
            return True

    return False


def callable_signatures(source):
    try:
        tree=ast.parse(source)
    except Exception:
        return {
            "functions":{},
            "classes":{},
        }

    functions={}
    classes={}

    for node in tree.body:

        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            functions[node.name]=_shape(
                node,
                False,
            )

        elif isinstance(node,ast.ClassDef):
            methods={}

            for child in node.body:
                if not isinstance(
                    child,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                    ),
                ):
                    continue

                methods[child.name]=_shape(
                    child,
                    not _is_static(child),
                )

            classes[node.name]={
                "constructor":methods.get(
                    "__init__",
                    {
                        "positional":[],
                        "kwonly":[],
                        "vararg":False,
                        "varkw":False,
                    },
                ),
                "methods":methods,
            }

    return {
        "functions":functions,
        "classes":classes,
    }


def _argument_errors(
    shape,
    args,
    kwargs,
    prefix,
):
    errors=[]

    if not isinstance(args,list):
        return errors

    if not isinstance(kwargs,dict):
        return errors

    positional=shape.get(
        "positional",
        [],
    )

    if (
        len(args) > len(positional)
        and not shape.get("vararg")
    ):
        errors.append(
            prefix+"_too_many_positional_args"
        )

    for index,item in enumerate(positional):
        if not item["required"]:
            continue

        by_position=index < len(args)

        by_keyword=(
            not item["positional_only"]
            and item["name"] in kwargs
        )

        if not (
            by_position
            or by_keyword
        ):
            errors.append(
                prefix
                + "_missing_required_arg:"
                + item["name"]
            )

    for item in shape.get(
        "kwonly",
        [],
    ):
        if (
            item["required"]
            and item["name"] not in kwargs
        ):
            errors.append(
                prefix
                + "_missing_required_kwarg:"
                + item["name"]
            )

    return errors


def validate_call_signature(
    probe,
    source,
):
    errors=[]

    signatures=callable_signatures(
        source
    )

    mode=probe.get("mode")

    if mode=="function":
        name=probe.get("function_name")

        shape=signatures[
            "functions"
        ].get(name)

        if shape:
            errors.extend(
                _argument_errors(
                    shape,
                    probe.get("args",[]),
                    probe.get("kwargs",{}),
                    "function",
                )
            )

    elif mode=="class_method":
        cls=probe.get("class_name")
        method=probe.get("method_name")

        row=signatures[
            "classes"
        ].get(cls)

        if row:
            errors.extend(
                _argument_errors(
                    row["constructor"],
                    probe.get(
                        "constructor_args",
                        [],
                    ),
                    probe.get(
                        "constructor_kwargs",
                        {},
                    ),
                    "constructor",
                )
            )

            shape=row[
                "methods"
            ].get(method)

            if shape:
                errors.extend(
                    _argument_errors(
                        shape,
                        probe.get("args",[]),
                        probe.get("kwargs",{}),
                        "method",
                    )
                )

    return errors


def _values(value):
    if isinstance(value,dict):
        for child in value.values():
            yield from _values(child)

    elif isinstance(value,list):
        for child in value:
            yield from _values(child)

    else:
        yield value


def validate_probe_paths(probe):
    errors=[]

    values={
        "args":probe.get("args"),
        "kwargs":probe.get("kwargs"),
        "constructor_args":
            probe.get("constructor_args"),
        "constructor_kwargs":
            probe.get("constructor_kwargs"),
    }

    for value in _values(values):

        if not isinstance(value,str):
            continue

        if value=="__SANDBOX__":
            continue

        normalized=value.replace(
            "\\",
            "/",
        )

        absolute=(
            normalized.startswith("/")
            or (
                len(normalized)>=3
                and normalized[1]==":"
                and normalized[2]=="/"
            )
        )

        traversal=(
            ".."
            in normalized.split("/")
        )

        if absolute or traversal:
            errors.append(
                "unsafe_probe_path:"
                + value
            )

    return errors


def resolve_probe_sandbox(
    value,
    sandbox,
):
    sandbox=str(
        Path(sandbox)
    )

    if value=="__SANDBOX__":
        return sandbox

    if isinstance(value,list):
        return [
            resolve_probe_sandbox(
                x,
                sandbox,
            )
            for x in value
        ]

    if isinstance(value,dict):
        return {
            k:resolve_probe_sandbox(
                v,
                sandbox,
            )
            for k,v in value.items()
        }

    return value
