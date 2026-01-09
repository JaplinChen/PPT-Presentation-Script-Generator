def load_model(model_path: str, device: str = "cuda", **kwargs):
    if kwargs.get("force_ori_type", False):
        # for hubert, landmark, retinaface, mediapipe
        model = load_force_ori_type(model_path, device, **kwargs)
        return model, "ori"

    if model_path.endswith(".onnx"):
        # onnx
        import onnxruntime

        if device == "cuda":
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        else:
            providers = ["CPUExecutionProvider"]
        model = onnxruntime.InferenceSession(model_path, providers=providers)
        return model, "onnx"

    elif model_path.endswith(".engine") or model_path.endswith(".trt"):
        # tensorRT
        from .tensorrt_utils import TRTWrapper

        model = TRTWrapper(model_path)
        return model, "tensorrt"

    elif model_path.endswith(".pt") or model_path.endswith(".pth"):
        # pytorch
        model = create_model(model_path, device, **kwargs)
        return model, "pytorch"

    else:
        raise ValueError(f"Unsupported model file type: {model_path}")


def _fix_package_name(package_name: str) -> str:
    """Fix legacy relative package names to absolute ones"""
    if not package_name:
        return package_name
    if package_name.startswith("..models.modules"):
        return "core.models.modules"
    if package_name.startswith("..aux_models.modules"):
        return "core.aux_models.modules"
    if package_name.startswith(".."):
        pkg = package_name.lstrip(".")
        return f"core.{pkg}" if pkg else "core"
    return package_name

def create_model(
    model_path: str,
    device: str = "cuda",
    module_name="",
    package_name="core.models.modules",
    **kwargs,
):
    import importlib
    import torch

    # Defensive device check for Mac/CPU only builds
    if device == "cuda" and not torch.cuda.is_available():
        device = "mps" if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() else "cpu"

    # Robust package resolution
    pkg = _fix_package_name(kwargs.pop("package_name", package_name))
    mod_name = kwargs.pop("module_name", module_name)

    try:
        module = getattr(importlib.import_module(pkg), mod_name)
    except Exception as e:
        print(f"FAILED TO IMPORT {mod_name} from {pkg}: {e}")
        raise e

    # Merge fixed device into kwargs
    kwargs["device"] = device

    try:
        model = module(**kwargs)
    except TypeError as e:
        if "unexpected keyword argument 'device'" in str(e):
            kwargs.pop("device")
            model = module(**kwargs)
        else:
            raise e

    model.load_model(model_path).to(device)
    return model


def load_force_ori_type(
    model_path: str,
    device: str = "cuda",
    module_name="",
    package_name="core.aux_models.modules",
    force_ori_type=False, 
    **kwargs,
):
    import importlib
    import torch

    if device == "cuda" and not torch.cuda.is_available():
        device = "mps" if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() else "cpu"

    pkg = _fix_package_name(kwargs.pop("package_name", package_name))
    mod_name = kwargs.pop("module_name", module_name)

    try:
        module = getattr(importlib.import_module(pkg), mod_name)
    except Exception as e:
        print(f"FAILED TO IMPORT {mod_name} from {pkg}: {e}")
        raise e

    kwargs["device"] = device

    try:
        model = module(**kwargs)
    except TypeError as e:
        if "unexpected keyword argument 'device'" in str(e):
            kwargs.pop("device")
            model = module(**kwargs)
        else:
            raise e
            
    return model
