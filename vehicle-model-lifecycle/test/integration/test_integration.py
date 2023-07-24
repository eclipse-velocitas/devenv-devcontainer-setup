import json
import os


def test_model_is_generated() -> None:
    generated_model_path = json.load(open(".velocitas.json"))["variables"][
        "generatedModelPath"
    ]

    assert os.path.exists(generated_model_path)
    assert os.path.isdir(generated_model_path)
